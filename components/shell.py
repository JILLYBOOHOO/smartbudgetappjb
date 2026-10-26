from datetime import date
import streamlit as st
from services.core import previous
from screens.capture import request_capture

def navigate(screen):
    st.session_state.screen=screen

def topbar(store):
    months={st.session_state.month,date.today().strftime('%Y-%m')}
    cursor=date.today().strftime('%Y-%m')
    for _ in range(35):
        cursor=previous(cursor);months.add(cursor)
    months.update(r['date'][:7] for r in store.load('transactions'))
    months=sorted(months,reverse=True)
    with st.container(key='topbar'):
        a,b=st.columns([3,1.3],vertical_alignment='bottom')
        query=a.text_input('Search SmartBudget',placeholder='Search transactions, documents, knowledge…',key='global_search',label_visibility='collapsed',icon=':material/search:')
        selected=b.selectbox('Reporting month',months,index=months.index(st.session_state.month),format_func=lambda x:date.fromisoformat(x+'-01').strftime('%B %Y'),label_visibility='collapsed',key='reporting_month')
        st.session_state.month=selected
    if query.strip():
        q=query.strip().lower()
        collections=[('transactions','Income & Expenses',['description','category','source']),('documents','Documents',['name','text']),('knowledge','Knowledge Base',['title','text','topic'])]
        with st.expander('Search results',expanded=True):
            found=False
            for kind,screen,fields in collections:
                matches=[r for r in store.load(kind) if q in ' '.join(str(r.get(f,'')) for f in fields).lower()][:3]
                if matches:
                    found=True
                    st.caption(screen+' · '+' / '.join(str(r.get('description') or r.get('name') or r.get('title'))[:100] for r in matches))
                    st.button('Open '+screen,key='global_'+kind,on_click=navigate,args=(screen,))
            if not found: st.caption('No matching local records. Try a category, merchant or source title.')

def mobile_nav():
    """Supported native controls; shown below content on small screens, not fake HTML links."""
    with st.container(key='mobile_nav'):
        cols=st.columns(5)
        for col,label,screen in zip(cols,['Home','Ledger','Add','Docs','Ask'],['Dashboard','Income & Expenses',None,'Documents','Ask SmartBudget']):
            if screen:
                col.button(label,key='mobile_'+label,on_click=navigate,args=(screen,),width='stretch')
            else:
                col.button('＋ Add',key='mobile_Add',on_click=request_capture,args=('Expense',),width='stretch',type='primary')
