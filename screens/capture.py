import hashlib
from datetime import date
from decimal import Decimal
from pathlib import Path
import streamlit as st
import pandas as pd
from services.core import *
from services.capture import suggest, csv_drafts, categorize
from services.statements import csv_statement, text_statement, analysis
from components.design import caption

def request_capture(mode='Expense'):
    if mode=='Upload':
        st.session_state.screen='Documents'
        st.session_state.pop('capture_mode',None)
        return
    st.session_state.capture_mode=mode
    st.session_state.pop('quick_draft',None)
    st.session_state.draft_revision=st.session_state.get('draft_revision',0)+1
    st.session_state.capture_sentence=''

def saved_notice():
    st.session_state.notice='Saved. Your dashboard and ledger are updated.'
    st.session_state.pop('capture_mode',None)
    st.rerun()

def review_form(store, draft, key, original=None, document=None):
    """Compact reactive editor; category suggestion updates when description changes."""
    original=original or {}
    kind=st.radio('Money direction',['Expense','Income'],index=0 if draft.get('type','Expense')=='Expense' else 1,horizontal=True,key=key+'_kind',label_visibility='collapsed',format_func=lambda x:'I spent' if x=='Expense' else 'I received')
    main,details=st.tabs(['Quick entry','Extra details'])
    with main:
        a,b=st.columns([1,1.4])
        amount=a.text_input('Amount (JMD)',draft.get('amount_text',''),placeholder='e.g. 2500',key=key+'_amount')
        description=b.text_input('What was it for? (optional)',draft.get('description',''),placeholder='e.g. MegaMart groceries',key=key+'_description')
        inferred=categorize(description,kind)
        a,b=st.columns([1.4,1])
        options=['Auto-detect']+CATEGORIES
        default=original.get('category') or 'Auto-detect'
        selection=a.selectbox('Category',options,index=options.index(default),key=key+'_category')
        category=(inferred if inferred!='Other' else draft.get('category','Other')) if selection=='Auto-detect' else selection
        when=b.date_input('Date',date.fromisoformat(draft.get('date',date.today().isoformat())),key=key+'_date')
        caption('Suggested category: '+category+' · Change Category to override.' if selection=='Auto-detect' else 'Using your selected category: '+category)
    with details:
        a,b=st.columns(2)
        payment=a.selectbox('Payment method',['Cash','Bank transfer','Debit card','Credit card','Other'],index=['Cash','Bank transfer','Debit card','Credit card','Other'].index(original.get('payment','Cash')),key=key+'_payment')
        source=b.text_input('Income source (optional)',original.get('source',''),key=key+'_source')
        notes=st.text_input('Notes (optional)',original.get('notes',''),key=key+'_notes')
    if st.button('Save transaction',type='primary',width='stretch',key=key+'_save'):
        try:
            record={**original,'id':original.get('id',uid()),'type':kind,'amount':cents(amount),'description':description.strip() or ('Money received' if kind=='Income' else 'Money spent'),'category':category,'date':when.isoformat(),'payment':payment,'source':source.strip(),'notes':notes}
            if document: record['document_id']=document['id']
            validate_transaction(record); store.put('transactions',record)
        except (ValueError,OSError) as exc:
            st.error(str(exc)); return
        saved_notice()

def statement_preview(store,file,content,text,digest,save_document):
    caption('Amounts are interpreted as JMD. Foreign-currency statements are not supported.')
    order=st.radio('Statement date format',['Day/month/year','Month/day/year'],horizontal=True,key='date_order_'+digest)
    try:
        drafts,skipped=(csv_statement(content,order.startswith('Day')) if file.name.lower().endswith('.csv') else text_statement(text,order.startswith('Day')))
    except ValueError as exc:
        st.error(str(exc)); return
    st.download_button('Download extracted text',text,Path(file.name).stem+'-extracted.txt','text/plain',key='text_'+digest)
    if skipped:
        st.warning(f'{len(skipped)} lines or rows were excluded. Review the extraction notes before importing.')
        with st.expander('Extraction notes'): st.text('\n'.join(skipped))
    if not drafts:
        st.info('No transaction rows recognized. For PDFs, use one line per transaction: full date, description, amount with two decimals, optional DR/CR, optional running balance. Export your bank statement as CSV for other layouts.'); return
    caption('Categories are suggested from merchant descriptions. Edit any cell below. Running balances are excluded. Check every date, amount and money direction against your statement.')
    if any(r['needs_review'] for r in drafts):
        st.warning('Some money directions are uncertain. Those rows start unchecked; verify Income/Expense and tick Include to use them.')
    frame=pd.DataFrame([{'Include':not r['needs_review'],'Date':r['date'],'Description':r['description'],'Type':r['type'],'Category':r['category'],'Amount (JMD)':str(Decimal(r['amount'])/100),'Check direction':r['needs_review']} for r in drafts])
    edited=st.data_editor(frame,hide_index=True,width='stretch',height=min(310,80+35*len(frame)),key='statement_'+digest+order,column_config={
        'Include':st.column_config.CheckboxColumn('Include'),
        'Type':st.column_config.SelectboxColumn('Type',options=['Income','Expense'],required=True),
        'Category':st.column_config.SelectboxColumn('Category',options=CATEGORIES,required=True),
        'Amount (JMD)':st.column_config.TextColumn('Amount (JMD)',required=True),
    },disabled=['Check direction'])
    reviewed=[]
    try:
        for item in edited.to_dict('records'):
            if not item['Include']: continue
            record=dict(id=uid(),date=str(item['Date']),description=str(item['Description']).strip(),type=item['Type'],category=item['Category'],amount=cents(item['Amount (JMD)']),source='',payment='Bank transfer',notes='Reviewed bank statement import')
            validate_transaction(record); reviewed.append(record)
    except (ValueError,TypeError) as exc:
        st.error('Correct the preview before importing: '+str(exc)); return
    income,expense,cats=analysis(reviewed)
    a,b,c=st.columns(3)
    a.metric('Included',str(len(reviewed))); b.metric('Money in',money(income)); c.metric('Money out',money(expense))
    if cats: caption('Spending: '+' · '.join(f'{k} {money(v)}' for k,v in cats.items()))
    existing=store.load('transactions')
    already=any(r.get('import_digest')==digest for r in existing)
    if already: st.warning('This statement was already imported. No second import is allowed while its records exist.')
    confirmed=st.checkbox('I checked the included transactions against my statement',key='checked_'+digest)
    if st.button('Import bank statement',type='primary',disabled=not reviewed or not confirmed or already,key='import_'+digest):
        document=save_document()
        for record in reviewed:
            record.update(document_id=document['id'],import_digest=digest)
        store.save('transactions',existing+reviewed); saved_notice()


def upload_flow(store):
    caption('Receipts, bills and bank statements · extracted locally · review before import.')
    file=st.file_uploader('Choose PDF, TXT or CSV',type=['pdf','txt','csv'],key='capture_file')
    caption('Text PDFs are supported. Photos and scanned PDFs need a text-based export; image OCR is not installed.')
    if file is None: return
    content=file.getvalue(); digest=hashlib.sha256(content).hexdigest()
    try:
        text=extract(file.name,content)
    except ValueError as exc:
        st.error(str(exc)); return
    existing=next((d for d in store.load('documents') if d.get('digest')==digest),None)
    with st.expander('View extracted text'): st.text(text)
    looks_bank='statement' in file.name.lower() or bool(re.search(r'(?i)\b(?:opening balance|closing balance|debit[^\n]*credit|withdrawal[^\n]*deposit)\b',text))
    if file.name.lower().endswith('.csv'):
        choice=st.radio('Use this CSV as',['Transaction list','Bank statement','One receipt or bill','Store document only'],index=1 if looks_bank else 0,horizontal=True)
    else:
        choice=st.radio('What would you like to do?',['One receipt or bill','Bank statement','Store document only'],index=1 if looks_bank else 0,horizontal=True)
    def save_document():
        if existing: return existing
        identifier=uid(); filename=identifier+Path(file.name).suffix.lower()
        (store.root/'uploads'/filename).write_bytes(content)
        document=dict(id=identifier,name=Path(file.name).name,file=filename,text=text,size=len(content),digest=digest,date=date.today().isoformat())
        store.put('documents',document); return document
    if choice=='Store document only':
        if st.button('Save document',type='primary'):
            save_document(); saved_notice()
    elif choice=='Bank statement':
        statement_preview(store,file,content,text,digest,save_document)
    elif choice=='Transaction list':
        try: drafts=csv_drafts(content)
        except ValueError as exc: st.error(str(exc)); return
        st.dataframe([dict(Date=r['date'],Type=r['type'],Description=r['description'],Category=r['category'],Amount=money(r['amount'])) for r in drafts],hide_index=True,width='stretch')
        caption('Amounts are JMD. A positive number defaults to Expense unless the CSV type column says Income. Correct the source CSV if any row is wrong.')
        already=any(r.get('import_digest')==digest for r in store.load('transactions'))
        if already: st.warning('This transaction file has already been imported. Delete its imported records before importing it again.')
        confirmed=st.checkbox(f'I reviewed all {len(drafts)} transactions')
        if st.button('Import reviewed transactions',type='primary',disabled=not confirmed or already):
            document=save_document()
            rows=store.load('transactions')
            for draft in drafts:
                record={**draft,'id':uid(),'document_id':document['id'],'import_digest':digest}
                validate_transaction(record); rows.append(record)
            store.save('transactions',rows); saved_notice()
    else:
        draft=suggest(text)
        st.info('Suggested details only. Check the amount, direction, category and date. An invoice is not necessarily paid; save only money actually spent or received.')
        # Store the document explicitly; financial records still require the form's Save.
        if not existing:
            if st.button('Keep document and review transaction',type='primary'):
                save_document(); st.rerun(scope='app')
            return
        if any(r.get('document_id')==existing['id'] for r in store.load('transactions')):
            st.warning('A transaction is already linked to this document. You can edit it in the ledger.')
            return
        review_form(store,draft,'receipt_'+digest,document=existing)

def dismiss_capture():
    st.session_state.pop('capture_mode',None)

@st.dialog('Add money activity',width='medium',on_dismiss=dismiss_capture)
def capture_dialog(store):
    mode=st.session_state.get('capture_mode','Expense')
    if mode=='Upload':
        upload_flow(store); return
    with st.popover('✦ Type a sentence instead'):
        text=st.text_input('Or say it in one line',placeholder='Spent 2500 on groceries yesterday',key='capture_sentence')
        if st.button('Use these details',disabled=not text.strip()):
            try:
                st.session_state.quick_draft=suggest(text)
                st.session_state.draft_revision=st.session_state.get('draft_revision',0)+1
            except ValueError as exc: st.error(str(exc))
    draft=st.session_state.get('quick_draft',dict(type=mode,category='Other'))
    review_form(store,draft,'quick_'+str(st.session_state.get('draft_revision',0)))

def open_capture(store):
    if st.session_state.get('capture_mode'): capture_dialog(store)
