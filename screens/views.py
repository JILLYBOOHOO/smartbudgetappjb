import hashlib
import io
from datetime import date
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from services.core import *

def go_to(screen, kind=None):
    st.session_state.screen = screen
    if kind:
        st.session_state.quick_type = kind

def month_picker():
    chosen = st.date_input('Reporting month', date.fromisoformat(st.session_state.month + '-01'), key='report_date')
    st.session_state.month = chosen.strftime('%Y-%m')
    return st.session_state.month

def plot(fig):
    light = st.session_state.theme == 'Light'
    fig.update_layout(template='plotly_white' if light else 'plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#101E34' if light else '#F5F9FF', height=340, margin=dict(l=10,r=10,t=35,b=20), transition_duration=0)
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})

def dashboard(store):
    st.title('Your money. In motion.')
    month = month_picker()
    rows, goals, budgets = store.load('transactions'), store.load('goals'), store.load('budgets')
    current = period(rows, month)
    inc, exp, net = totals(current)
    old_inc = totals(period(rows, previous(month)))[0]
    for col, label, amount, delta in zip(st.columns(4), ['Total income', 'Total expenses', 'Available · period cash flow', 'Recorded savings · all dates'], [inc, exp, net, sum(saved(g) for g in goals)], [f'{(inc-old_inc)/old_inc:+.1%} vs previous month' if old_inc else None, f'{exp/inc:.1%} of income' if inc else 'No income recorded', 'Income minus expenses', 'Separate contributions ledger']):
        col.metric(label, money(amount), delta, delta_color='off')
    st.caption('Available is the selected period’s net cash flow, not a verified bank balance. Savings do not reduce this figure.')
    for col, label, screen, kind in zip(st.columns(6), ['＋ Income','− Expense','↑ Upload bill','◎ Set budget','≡ Transactions','✦ Ask'], ['Income & Expenses','Income & Expenses','Documents','Dashboard','Income & Expenses','Ask SmartBudget'], ['Income','Expense',None,None,None,None]):
        col.button(label, on_click=go_to, args=(screen,kind), width='stretch')
    left, right = st.columns(2)
    with left:
        st.subheader('Income & expenses')
        months = sorted(set(r['date'][:7] for r in rows if r['date'][:7] <= month))[-6:]
        fig = go.Figure()
        for i, label, color in [(0,'Income','#19E3B1'),(1,'Expenses','#FF766D')]:
            fig.add_bar(name=label, x=months, y=[totals(period(rows,m))[i]/100 for m in months], marker_color=color)
        plot(fig)
        st.caption('Chart shows up to six recorded months ending with the reporting month; values in JMD.')
    with right:
        st.subheader('Where your money goes')
        cats = categories(current)
        if cats:
            fig = go.Figure(go.Pie(labels=list(cats),values=[v/100 for v in cats.values()],hole=.72,marker_colors=['#168BFF','#19E3B1','#B17CFF','#FF766D','#FFBE55','#00D9FF']))
            fig.add_annotation(text=money(exp),x=.5,y=.5,showarrow=False)
            plot(fig)
            st.caption(' · '.join(f'{k}: {money(v)}' for k,v in cats.items()))
        else:
            st.info('No expenses in this month. Add one to see the category chart.')
    st.subheader('Smart Actions')
    for index, (message, screen) in enumerate(actions(rows,budgets,goals,month)):
        st.info(message)
        st.button('Review ' + screen, key=f'action_{index}', on_click=go_to, args=(screen,))
    if not actions(rows,budgets,goals,month):
        st.caption('No budget or savings alerts for this period.')
    budget_panel(store,month,rows)
    savings_panel(store)
    st.subheader('Recent activity')
    display_rows(sorted(current,key=lambda r:r['date'],reverse=True)[:8])

def display_rows(rows):
    if not rows:
        st.info('No matching transactions.')
        return
    st.dataframe(pd.DataFrame([{'Date':r['date'],'Type':r['type'],'Category':r['category'],'Description':r['description'],'Amount':money(r['amount']),'Demo':r.get('demo',False)} for r in rows]), hide_index=True, width='stretch')

def budget_panel(store, month, rows):
    st.subheader('Budgets · ' + month)
    budgets = [b for b in store.load('budgets') if b['month']==month]
    if budgets:
        fig = go.Figure()
        fig.add_bar(name='Budget',x=[b['category'] for b in budgets],y=[b['limit']/100 for b in budgets],marker_color='#168BFF')
        fig.add_bar(name='Actual',x=[b['category'] for b in budgets],y=[utilization(b,rows)[0]/100 for b in budgets],marker_color='#FF766D')
        plot(fig)
    for b in budgets:
        spent,remaining,ratio = utilization(b,rows)
        st.progress(min(ratio,1.0),text=f"{b['category']}: {money(spent)} / {money(b['limit'])} · {money(remaining)} remaining")
        if st.checkbox('Confirm delete budget',key='bc'+b['id']):
            if st.button('Delete budget',key='bd'+b['id']):
                store.delete('budgets',b['id']); st.rerun()
    with st.expander('Set or edit monthly budget'):
        with st.form('budget'):
            category = st.selectbox('Budget category',['All spending']+CATEGORIES)
            amount = st.text_input('Monthly limit (JMD)','30000')
            threshold = st.slider('Warning threshold (%)',50,100,80)
            if st.form_submit_button('Save budget'):
                existing = next((b for b in budgets if b['category']==category),None)
                store.put('budgets',dict(id=existing['id'] if existing else uid(),month=month,category=category,limit=cents(amount),threshold=threshold))
                st.rerun()

def savings_panel(store):
    st.subheader('Savings goals')
    st.caption('Contributions track money you have set aside; they are not expenses or bank transfers. Goal deletion removes its contribution history.')
    goals = store.load('goals')
    for g in goals:
        st.progress(min(saved(g)/g['target'],1.0),text=f"{g['name']} · {money(saved(g))} / {money(g['target'])}" + (' · Completed' if g.get('completed') else ''))
        with st.expander('Manage ' + g['name']):
            with st.form('goaledit'+g['id']):
                name=st.text_input('Goal name',g['name'])
                target=st.text_input('Target (JMD)',str(Decimal(g['target'])/100))
                deadline=st.text_input('Target date (YYYY-MM-DD, optional)',g.get('deadline',''))
                complete=st.checkbox('Mark completed',g.get('completed',False))
                if st.form_submit_button('Update goal'):
                    if not name.strip(): raise ValueError('Enter a goal name.')
                    if deadline: date.fromisoformat(deadline)
                    store.put('goals',{**g,'name':name.strip(),'target':cents(target),'deadline':deadline,'completed':complete}); st.rerun()
            with st.form('contrib'+g['id']):
                amount=st.text_input('Contribution (JMD)')
                when=st.date_input('Contribution date',key='cd'+g['id'])
                if st.form_submit_button('Record contribution'):
                    store.put('goals',{**g,'contributions':g.get('contributions',[])+[dict(id=uid(),amount=cents(amount),date=when.isoformat())]}); st.rerun()
            st.write('Target date: ' + (g.get('deadline') or 'Not set'))
            for c in g.get('contributions',[]): st.caption(f"{c['date']} · {money(c['amount'])}")
            if st.checkbox('Confirm delete goal and contributions',key='gc'+g['id']):
                if st.button('Delete goal',key='gd'+g['id']): store.delete('goals',g['id']); st.rerun()
    with st.expander('Create savings goal'):
        with st.form('newgoal'):
            name=st.text_input('Goal name')
            amount=st.text_input('Target amount (JMD)')
            deadline=st.text_input('Optional target date (YYYY-MM-DD)')
            if st.form_submit_button('Create goal'):
                if not name.strip(): raise ValueError('Enter a goal name.')
                if deadline: date.fromisoformat(deadline)
                store.put('goals',dict(id=uid(),name=name.strip(),target=cents(amount),deadline=deadline,completed=False,contributions=[])); st.rerun()

def transaction_form(store, row=None):
    row=row or {}
    with st.form('transaction_edit_' + row['id'] if row else 'transaction_new'):
        kind=st.selectbox('Transaction type',['Income','Expense'],index=['Income','Expense'].index(row.get('type',st.session_state.quick_type)))
        a,b=st.columns(2)
        amount=a.text_input('Amount (JMD)',str(Decimal(row['amount'])/100) if row else '')
        category=b.selectbox('Category',CATEGORIES,index=CATEGORIES.index(row.get('category','Salary')))
        when=a.date_input('Transaction date',date.fromisoformat(row['date']) if row else date.today())
        source=b.text_input('Income source (required for income)',row.get('source',''))
        description=st.text_input('Description',row.get('description',''))
        payment=st.selectbox('Payment method',['Cash','Bank transfer','Debit card','Credit card','Other'],index=['Cash','Bank transfer','Debit card','Credit card','Other'].index(row.get('payment','Cash')))
        notes=st.text_area('Optional notes',row.get('notes',''))
        if st.form_submit_button('Save transaction',type='primary'):
            if kind=='Income' and not source.strip(): raise ValueError('Enter the income source.')
            record={**row,'id':row.get('id',uid()),'type':kind,'amount':cents(amount),'category':category,'date':when.isoformat(),'source':source.strip(),'description':description.strip(),'payment':payment,'notes':notes}
            validate_transaction(record); store.put('transactions',record)
            st.success('Transaction saved.'); st.rerun()

def transactions(store):
    st.title('Income & Expenses')
    with st.expander('Add a transaction',expanded=True): transaction_form(store)
    rows=store.load('transactions')
    st.subheader('Your ledger')
    a,b,c=st.columns(3)
    search=a.text_input('Search description, source or notes',key='search_tx')
    category=b.selectbox('Filter category',['All']+CATEGORIES,key='filter_cat')
    kind=c.selectbox('Filter type',['All','Income','Expense'],key='filter_kind')
    dates=st.date_input('Date range',value=(date.today().replace(day=1),date.today()),key='filter_dates')
    sort=st.selectbox('Sort',['Newest','Oldest','Amount high to low','Amount low to high'])
    filtered=[r for r in rows if (category=='All' or r['category']==category) and (kind=='All' or r['type']==kind) and search.lower() in ' '.join(str(r.get(k,'')) for k in ['description','notes','source']).lower() and (len(dates)!=2 or dates[0].isoformat()<=r['date']<=dates[1].isoformat())]
    filtered.sort(key=lambda r:r['amount'] if 'Amount' in sort else r['date'],reverse=sort in ['Newest','Amount high to low'])
    display_rows(filtered)
    export=pd.DataFrame([{**r,'amount_jmd':str(Decimal(r['amount'])/100)} for r in filtered]).to_csv(index=False)
    # Escape spreadsheet formula prefixes in text fields for safe CSV opening.
    if filtered:
        frame=pd.DataFrame([{**r,'amount_jmd':str(Decimal(r['amount'])/100)} for r in filtered])
        for col in frame.select_dtypes(include='object'):
            frame[col]=frame[col].map(lambda x: "'"+x if isinstance(x,str) and x.startswith(('=','+','-','@','\t','\r')) else x)
        export=frame.to_csv(index=False)
    st.download_button('Export filtered CSV',export,'transactions.csv','text/csv')
    if filtered:
        identifier=st.selectbox('View or edit transaction',[r['id'] for r in filtered],format_func=lambda x:next(f"{r['date']} · {r['description']} · {money(r['amount'])}" for r in filtered if r['id']==x))
        row=next(r for r in filtered if r['id']==identifier)
        st.caption('Record ID: '+identifier)
        # Key the editor container by the selected ID so widget defaults refresh.
        with st.container(key='editor_'+identifier): transaction_form(store,row)
        if st.checkbox('Confirm permanent transaction deletion'):
            if st.button('Delete transaction'): store.delete('transactions',identifier); st.rerun()

def documents(store):
    st.title('Documents')
    st.caption('Processed locally. PDF (text only), UTF-8 TXT or CSV · maximum 10 MB, 100 PDF pages. No OCR or external uploads.')
    upload=st.file_uploader('Choose a financial document',type=['pdf','txt','csv'])
    if st.button('Process document',disabled=upload is None):
        content=upload.getvalue(); digest=hashlib.sha256(content).hexdigest()
        if any(d.get('digest')==digest for d in store.load('documents')):
            st.warning('This document is already stored.')
        else:
            text=extract(upload.name,content); identifier=uid(); filename=identifier+Path(upload.name).suffix.lower()
            (store.root/'uploads'/filename).write_bytes(content)
            store.put('documents',dict(id=identifier,name=Path(upload.name).name,file=filename,text=text,size=len(content),digest=digest,date=date.today().isoformat()))
            st.success('Document processed. Preview it below and add it to your knowledge base.')
    search=st.text_input('Search uploaded document text')
    for d in store.load('documents'):
        if search.lower() not in (d['name']+' '+d['text']).lower(): continue
        with st.expander(d['name']):
            st.caption(f"{d.get('size',0):,} bytes · {d.get('date','')} · ID {d['id']}")
            st.text(d['text'])
            if st.button('Add to Knowledge Base',key='dk'+d['id']):
                entry_id='doc_'+d['id']
                store.put('knowledge',dict(id=entry_id,title=d['name'],text=d['text'],topic='Uploaded documents',source='Uploaded document: '+d['name']))
                st.success('Knowledge entry added or refreshed.')
            if st.checkbox('Confirm delete document and linked knowledge entry',key='dc'+d['id']):
                if st.button('Delete document',key='dd'+d['id']):
                    filename=d['file']
                    if Path(filename).name!=filename or not re.fullmatch(r'[a-f0-9]{32}\.(pdf|txt|csv)',filename): raise ValueError('Unsafe stored filename.')
                    (store.root/'uploads'/filename).unlink(missing_ok=True)
                    store.delete('knowledge','doc_'+d['id']); store.delete('documents',d['id']); st.rerun()

def knowledge(store):
    st.title('Knowledge Base')
    st.caption('Local educational material and your uploaded sources. Search uses explainable keyword overlap; no language model is connected.')
    rows=store.load('knowledge')
    query=st.text_input('Search knowledge')
    topic=st.selectbox('Topic',['All']+sorted(set(r['topic'] for r in rows)))
    shown=retrieve(query,rows) if query else rows
    for r in shown:
        if topic!='All' and r['topic']!=topic: continue
        with st.expander(r['title']):
            st.text(r['text']); st.caption('Source: '+r['source'])
            with st.form('ke'+r['id']):
                title=st.text_input('Title',r['title']); text=st.text_area('Content',r['text'])
                subject=st.text_input('Topic',r['topic']); source=st.text_input('Source',r['source'])
                if st.form_submit_button('Update entry'):
                    if not all(v.strip() for v in [title,text,subject,source]): raise ValueError('All knowledge fields are required.')
                    store.put('knowledge',dict(id=r['id'],title=title,text=text,topic=subject,source=source)); st.rerun()
            if st.checkbox('Confirm delete entry',key='kc'+r['id']):
                if st.button('Delete entry',key='kd'+r['id']): store.delete('knowledge',r['id']); st.rerun()
    with st.expander('Add knowledge entry'):
        with st.form('kn'):
            title=st.text_input('Title'); text=st.text_area('Content'); topic=st.text_input('Topic'); source=st.text_input('Source')
            if st.form_submit_button('Add entry'):
                if not all(v.strip() for v in [title,text,topic,source]): raise ValueError('All knowledge fields are required.')
                store.put('knowledge',dict(id=uid(),title=title,text=text,topic=topic,source=source)); st.rerun()

def chat(store):
    st.title('✦ Ask SmartBudget')
    st.caption('Your local money companion · deterministic calculations + sourced knowledge retrieval. No LLM or API keys.')
    month_picker()
    st.caption('“This month” and “last month” use today’s date. Other financial questions use the reporting month. Savings totals cover all dates.')
    suggestions=['How much did I spend this month?','Am I over budget?','What is an emergency fund?','Which savings goal is closest to completion?']
    selected=None
    for index,q in enumerate(suggestions):
        if index % 2 == 0: cols = st.columns(2)
        col = cols[index % 2]
        if col.button(q,key=q): selected=q
    if st.button('Clear chat history'): st.session_state.messages=[]; st.rerun()
    for m in st.session_state.messages:
        with st.chat_message(m['role']): st.text(m['content'])
    question=st.chat_input('Ask about your money or financial habits') or selected
    if question:
        st.session_state.messages.append(dict(role='user',content=question))
        with st.chat_message('user'): st.text(question)
        with st.spinner('Reviewing local records and sources…'):
            response=answer(question,store,st.session_state.month)
        st.session_state.messages.append(dict(role='assistant',content=response))
        with st.chat_message('assistant'): st.text(response)
