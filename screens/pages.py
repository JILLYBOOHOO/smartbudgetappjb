import hashlib
import io
from datetime import date
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from services.core import *
from screens.capture import request_capture, review_form, upload_flow
from components.design import page_intro, summary_cards, recent_rows, knowledge_preview, caption, category_legend, category_color

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
    fig.update_layout(template='plotly_white' if light else 'plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#101E34' if light else '#F5F9FF', height=212, margin=dict(l=5,r=5,t=16,b=12), transition_duration=0)
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})

def dashboard(store):
    month=st.session_state.month
    rows,goals,budgets=store.load('transactions'),store.load('goals'),store.load('budgets')
    current=period(rows,month)
    inc,exp,net=totals(current)
    old_inc=totals(period(rows,previous(month)))[0]
    savings=sum(saved(g) for g in goals)
    target=sum(g['target'] for g in goals)
    page_intro('Your money. In motion.','Track. Plan. Save. Achieve.','YOUR FINANCIAL OVERVIEW')
    spark_months=[month]
    for _ in range(11): spark_months.append(previous(spark_months[-1]))
    spark_months.reverse()
    history={tone:[totals(period(rows,m))[idx] for m in spark_months] for tone,idx in [('income',0),('expense',1)]}
    summary_cards([
        ('income','↑','Total Income',inc,f'{(inc-old_inc)/old_inc:+.1%} vs previous month' if old_inc else 'Selected reporting month'),
        ('expense','↙','Total Expenses',exp,f'{exp/inc:.1%} of recorded income' if inc else 'No income recorded'),
        ('balance','▣','Available Balance',net,'Period net cash flow'),
        ('savings','◎','Savings',savings,f'{savings/target:.0%} of combined targets' if target else 'Set your first savings goal'),
    ],history=history,progress=min(savings/target,1) if target else 0)
    st.subheader('Quick Actions')
    with st.container(key='quick_actions'):
        cols=st.columns(6)
        cols[0].button('Add Income',icon=':material/add:',on_click=request_capture,args=('Income',),width='stretch')
        cols[1].button('Add Expense',icon=':material/receipt_long:',on_click=request_capture,args=('Expense',),width='stretch')
        cols[2].button('Upload Bill',icon=':material/document_scanner:',on_click=request_capture,args=('Upload',),width='stretch')
        cols[3].button('Set Budget',icon=':material/track_changes:',on_click=lambda:st.session_state.update(budget_open=True),width='stretch')
        cols[4].button('Transactions',icon=':material/format_list_bulleted:',on_click=go_to,args=('Income & Expenses',),width='stretch')
        cols[5].button('Ask SmartBudget',icon=':material/auto_awesome:',on_click=go_to,args=('Ask SmartBudget',),width='stretch')
    with st.container(key='analytics'):
        left,right=st.columns(2)
        with left:
            with st.container(key='income_panel'):
                title_col,filter_col=st.columns([1.5,1])
                title_col.subheader('Income vs. Expenses')
                count=filter_col.selectbox('History range',['Last 6 months','Last 3 months'],label_visibility='collapsed')
                months=[month]
                for _ in range(5 if count=='Last 6 months' else 2): months.append(previous(months[-1]))
                months.reverse()
                fig=go.Figure()
                for i,label,color in [(0,'Income','#42CFFF'),(1,'Expenses','#FF788F')]:
                    fig.add_bar(name=label,x=months,y=[totals(period(rows,m))[i]/100 for m in months],marker_color=color,marker_line_color=color,marker_line_width=1,hovertemplate='%{x}<br>J$%{y:,.2f}<extra>'+label+'</extra>')
                fig.update_layout(bargap=.45,barmode='group',legend=dict(orientation='h',y=1.2,x=0),yaxis=dict(tickprefix='J$',gridcolor='rgba(110,160,230,.12)',zeroline=False),xaxis=dict(type='category',tickvals=months,ticktext=[date.fromisoformat(m+'-01').strftime('%b') for m in months]))
                plot(fig)
                with st.expander('Chart figures'):
                    st.text('\n'.join(f'{m}: income {money(totals(period(rows,m))[0])}, expenses {money(totals(period(rows,m))[1])}' for m in months))
        with right:
            with st.container(key='spending_panel'):
                cats=categories(current)
                title_col,filter_col=st.columns([1.5,1])
                title_col.subheader('Spending by Category')
                if cats:
                    focus=filter_col.selectbox('Highlight category',['All categories']+list(cats),label_visibility='collapsed')
                    fig=go.Figure(go.Pie(labels=list(cats),values=[v/100 for v in cats.values()],hole=.78,sort=False,textinfo='none',pull=[.065 if c==focus else 0 for c in cats],marker=dict(colors=[category_color(c) for c in cats],line=dict(color='#0c1730',width=4)),hovertemplate='%{label}<br>J$%{value:,.2f} · %{percent}<extra></extra>'))
                    fig.add_annotation(text=money(exp),x=.5,y=.54,showarrow=False,font=dict(size=15))
                    fig.add_annotation(text='TOTAL SPENT',x=.5,y=.37,showarrow=False,font=dict(size=9,color='#91a8c8'))
                    overall=next((b for b in budgets if b['month']==month and b['category']=='All spending'),None)
                    if overall: caption(('Over budget: '+money(exp-overall['limit'])) if exp>overall['limit'] else ('Budget remaining: '+money(overall['limit']-exp)))
                    fig.update_layout(showlegend=False)
                    with st.container(key='category_split'):
                        donut,legend=st.columns([1.1,1],gap='small')
                        with donut: plot(fig)
                        with legend: category_legend(cats)
                else:
                    st.info('Your category breakdown appears after your first expense.')
    with st.container(key='dashboard_lower'):
        left,right=st.columns([1.15,1])
        with left:
            with st.container(key='recent_panel'):
                st.subheader('Recent Transactions')
                recent_rows(sorted(current,key=lambda r:r['date'],reverse=True)[:4])
                st.button('View all transactions',on_click=go_to,args=('Income & Expenses',),width='stretch')
        with right:
            with st.container(key='insights_panel'):
                st.subheader('✧ Smart Insights')
                insights=actions(rows,budgets,goals,month)
                if inc and exp/inc<.2:
                    caption(f'Recorded spending is {exp/inc:.1%} of income this month. Check that all expenses have been entered.')
                for index,(message,screen) in enumerate(insights[:3]):
                    caption(message)
                    if screen=='Dashboard':
                        st.button('Add savings contribution',key=f'action_{index}',on_click=lambda:st.session_state.update(contribution_open=True))
                    else:
                        st.button('Review transactions',key=f'action_{index}',on_click=go_to,args=(screen,))
                if not goals: caption('Start a savings goal for emergencies or something you are working toward.')
                if not insights and not inc: caption('Add transactions to unlock insights from your own records.')
                st.button('Manage budgets & savings',on_click=lambda:st.session_state.update(manage_finances=True),width='stretch')
    caption('Available Balance = selected-period income minus expenses, not a bank account balance. Savings are separate contributions across all dates.')
    with st.expander('Budgets & savings',expanded=st.session_state.get('manage_finances',False)):
        budget_panel(store,month,rows)
        if not st.session_state.get('savings_open',False): savings_panel(store)
    if st.session_state.get('budget_open',False): budget_dialog(store,month,rows)
    elif st.session_state.get('savings_open',False): savings_dialog(store)
    elif st.session_state.get('contribution_open',False): contribution_dialog(store)

def display_rows(rows):
    if not rows:
        st.info('No matching transactions.')
        return
    st.dataframe(pd.DataFrame([{'Date':r['date'],'Type':r['type'],'Category':r['category'],'Description':r['description'],'Amount':money(r['amount'])} for r in rows]), hide_index=True, width='stretch')

def dismiss_contribution():
    st.session_state.pop('contribution_open',None)

@st.dialog('Add to your savings',on_dismiss=dismiss_contribution)
def contribution_dialog(store):
    goals=store.load('goals')
    if not goals:
        st.info('Create a savings goal on the dashboard first.'); return
    with st.form('contribution_popup'):
        identifier=st.selectbox('Goal',[g['id'] for g in goals],format_func=lambda x:next(g['name'] for g in goals if g['id']==x))
        amount=st.text_input('Amount to set aside (JMD)')
        when=st.date_input('Savings date')
        if st.form_submit_button('Save contribution',type='primary'):
            try:
                goal=next(g for g in goals if g['id']==identifier)
                store.put('goals',{**goal,'contributions':goal.get('contributions',[])+[dict(id=uid(),amount=cents(amount),date=when.isoformat())]})
            except ValueError as exc:
                st.error(str(exc)); return
            st.session_state.notice='Savings contribution recorded.'
            dismiss_contribution(); st.rerun()

def dismiss_budget():
    st.session_state.pop('budget_open',None)

@st.dialog('Set a monthly budget',on_dismiss=dismiss_budget)
def budget_dialog(store,month,rows):
    caption('Choose a category or set a limit for all spending in '+month+'.')
    with st.form('budget_popup'):
        category=st.selectbox('Budget for',['All spending']+CATEGORIES)
        amount=st.text_input('Limit (JMD)',placeholder='e.g. 30000')
        threshold=st.slider('Alert me at (%)',50,100,80)
        if st.form_submit_button('Save monthly limit',type='primary'):
            try:
                existing=next((b for b in store.load('budgets') if b['month']==month and b['category']==category),None)
                store.put('budgets',dict(id=existing['id'] if existing else uid(),month=month,category=category,limit=cents(amount),threshold=threshold))
            except ValueError as exc:
                st.error(str(exc)); return
            st.session_state.notice='Monthly budget saved.'
            dismiss_budget()
            st.rerun()

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
        st.progress(min(ratio,1.0),text=f"{b['category']}: {money(spent)} / {money(b['limit'])} · {money(remaining)} remaining".replace('$',r'\$'))
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

def dismiss_savings():
    st.session_state.pop('savings_open',None)

@st.dialog('Manage your savings',width='large',on_dismiss=dismiss_savings)
def savings_dialog(store):
    savings_panel(store,expanded=True)

def savings_panel(store,expanded=False):
    st.subheader('Savings goals')
    caption('Contributions track money you have set aside; they are not expenses or bank transfers. Goal deletion removes its contribution history.')
    goals = store.load('goals')
    for g in goals:
        st.progress(min(saved(g)/g['target'],1.0),text=(f"{g['name']} · {money(saved(g))} / {money(g['target'])}" + (' · Completed' if g.get('completed') else '')).replace('$',r'\$'))
        with st.expander('Manage ' + g['name'],expanded=expanded):
            with st.form('contrib'+g['id']):
                amount=st.text_input('Contribution (JMD)')
                when=st.date_input('Contribution date',key='cd'+g['id'])
                if st.form_submit_button('Record contribution'):
                    store.put('goals',{**g,'contributions':g.get('contributions',[])+[dict(id=uid(),amount=cents(amount),date=when.isoformat())]}); st.rerun()
            with st.form('goaledit'+g['id']):
                name=st.text_input('Goal name',g['name'])
                target=st.text_input('Target (JMD)',str(Decimal(g['target'])/100))
                deadline=st.text_input('Target date (YYYY-MM-DD, optional)',g.get('deadline',''))
                complete=st.checkbox('Mark completed',g.get('completed',False))
                if st.form_submit_button('Update goal'):
                    if not name.strip(): raise ValueError('Enter a goal name.')
                    if deadline: date.fromisoformat(deadline)
                    store.put('goals',{**g,'name':name.strip(),'target':cents(target),'deadline':deadline,'completed':complete}); st.rerun()
            st.write('Target date: ' + (g.get('deadline') or 'Not set'))
            for c in g.get('contributions',[]): caption(f"{c['date']} · {money(c['amount'])}")
            if st.checkbox('Confirm delete goal and contributions',key='gc'+g['id']):
                if st.button('Delete goal',key='gd'+g['id']): store.delete('goals',g['id']); st.rerun()
    with st.expander('Create savings goal',expanded=expanded and not goals):
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
    draft={**row,'amount_text':str(Decimal(row['amount'])/100) if row else '', 'type':row.get('type',st.session_state.quick_type),'category':row.get('category','Other')}
    review_form(store,draft,'edit_'+row['id'] if row else 'inline_new',original=row)

def transactions(store):
    page_intro('Income & Expenses','Every transaction. One clear picture.','YOUR ACTIVITY')
    a,b,c=st.columns(3)
    a.button('Add Income',on_click=request_capture,args=('Income',),type='primary',width='stretch')
    b.button('Add Expense',on_click=request_capture,args=('Expense',),width='stretch')
    c.button('Upload Bill',on_click=request_capture,args=('Upload',),width='stretch')
    with st.expander('Prefer to type the details here?'): transaction_form(store)
    rows=store.load('transactions')
    st.subheader('Your ledger')
    a,b,c=st.columns(3)
    search=a.text_input('Search description, source or notes',key='search_tx')
    category=b.selectbox('Filter category',['All']+CATEGORIES,key='filter_cat')
    kind=c.selectbox('Filter type',['All','Income','Expense'],key='filter_kind')
    all_dates=[date.fromisoformat(r['date']) for r in rows]
    dates=st.date_input('Date range',value=(min(all_dates) if all_dates else date.today().replace(day=1),max(all_dates+[date.today()])),key='filter_dates')
    sort=st.selectbox('Sort',['Newest','Oldest','Amount high to low','Amount low to high'])
    filtered=[r for r in rows if (category=='All' or r['category']==category) and (kind=='All' or r['type']==kind) and search.lower() in ' '.join(str(r.get(k,'')) for k in ['description','notes','source']).lower() and (len(dates)!=2 or dates[0].isoformat()<=r['date']<=dates[1].isoformat())]
    filtered.sort(key=lambda r:r['amount'] if 'Amount' in sort else r['date'],reverse=sort in ['Newest','Amount high to low'])
    display_rows(filtered)
    export=pd.DataFrame([{**r,'amount_jmd':str(Decimal(r['amount'])/100)} for r in filtered]).to_csv(index=False)
    # Escape spreadsheet formula prefixes in text fields for safe CSV opening.
    if filtered:
        frame=pd.DataFrame([{**r,'amount_jmd':str(Decimal(r['amount'])/100)} for r in filtered])
        for col in frame.columns:
            frame[col]=frame[col].map(lambda x: "'"+x if isinstance(x,str) and x.startswith(('=','+','-','@','\t','\r')) else x)
        export=frame.to_csv(index=False)
    st.download_button('Export filtered CSV',export,'transactions.csv','text/csv')
    if filtered:
        identifier=st.selectbox('View or edit transaction',[r['id'] for r in filtered],format_func=lambda x:next(f"{r['date']} · {r['description']} · {money(r['amount'])}" for r in filtered if r['id']==x))
        row=next(r for r in filtered if r['id']==identifier)
        caption('Record ID: '+identifier)
        # Key the editor container by the selected ID so widget defaults refresh.
        with st.expander('Edit selected transaction'):
            with st.container(key='editor_'+identifier): transaction_form(store,row)
        if st.checkbox('Confirm permanent transaction deletion'):
            if st.button('Delete transaction'): store.delete('transactions',identifier); st.rerun()

def documents(store):
    page_intro('Documents','From paper to a clearer money picture.','YOUR DOCUMENT WORKSPACE')
    upload_flow(store)
    st.divider()
    st.subheader('Saved documents')
    search=st.text_input('Search uploaded document text')
    for d in store.load('documents'):
        if search.lower() not in (d['name']+' '+d['text']).lower(): continue
        with st.expander(d['name']):
            caption(f"{d.get('size',0):,} bytes · {d.get('date','')} · ID {d['id']}")
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
    page_intro('Knowledge Base','Build better money habits. Find answers in your local sources.','LEARN & GROW')
    rows=store.load('knowledge')
    query=st.text_input('Search knowledge')
    topic=st.selectbox('Topic',['All']+sorted(set(r['topic'] for r in rows)))
    shown=retrieve(query,rows) if query else rows
    for r in shown:
        if topic!='All' and r['topic']!=topic: continue
        knowledge_preview(r['title'],r['text'],r['source'])
        with st.expander('Read & manage · '+r['title']):
            st.text(r['text']); caption('Source: '+r['source'])
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
    st.markdown('<div class="assistant-beacon" aria-hidden="true">✧</div>',unsafe_allow_html=True)
    page_intro('Ask SmartBudget','A little clarity for your next money move.','YOUR LOCAL MONEY COMPANION')
    caption('Calculated from your records. Retrieved from your sources. No external AI service.')
    caption('“This month” and “last month” use today’s date. Other financial questions use the reporting month. Savings totals cover all dates.')
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
