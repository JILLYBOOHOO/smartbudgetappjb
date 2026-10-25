from datetime import date
from pathlib import Path
import os
import streamlit as st
from services.core import Store, seed, demo
from screens.views import dashboard, transactions, documents, knowledge, chat

st.set_page_config(page_title='SmartBudget JA', page_icon='◈', layout='wide')
store = Store(os.environ.get('SMARTBUDGET_DATA', str(Path(__file__).parent / 'data')))
for key, value in {'screen': 'Dashboard', 'month': date.today().strftime('%Y-%m'), 'theme': 'Dark', 'messages': [], 'quick_type': 'Income'}.items():
    st.session_state.setdefault(key, value)
try:
    seed(store)
    with st.sidebar:
        st.markdown('## ◈ SmartBudget JA')
        st.caption('YOUR MONEY. IN MOTION.')
        st.radio('Navigate', ['Dashboard', 'Income & Expenses', 'Documents', 'Knowledge Base', 'Ask SmartBudget'], key='screen')
        st.radio('Appearance', ['Dark', 'Light'], horizontal=True, key='theme')
        st.divider()
        st.caption('Single-user • Local storage • JMD')
        import json
        st.download_button('Export all records', json.dumps({k: store.load(k) for k in ['transactions', 'budgets', 'goals', 'documents', 'knowledge', 'settings']}, indent=2), 'smartbudget-backup.json', 'application/json')
        if st.button('Load Demo Data'):
            demo(store)
            st.success('Fictional demo records loaded.')
        confirm = st.checkbox('Confirm removal of demo records only')
        if st.button('Reset Demo Data', disabled=not confirm):
            for kind in ['transactions', 'budgets', 'goals']:
                store.save(kind, [r for r in store.load(kind) if not r.get('demo')])
            st.success('Demo records removed. Your other records remain.')
    light = st.session_state.theme == 'Light'
    bg, card, fg, muted = ('#F3F6FC', '#FFFFFF', '#101E34', '#425570') if light else ('#05070C', '#111D30', '#F5F9FF', '#A8B7CC')
    st.markdown(f'''<style>
    .stApp {{background:{bg};color:{fg};}} [data-testid="stSidebar"]{{background:{card};}}
    [data-testid="stHeader"]{{background:{bg};}}
    .stButton button,.stDownloadButton button,[data-testid="stForm"],[data-testid="stExpander"]{{background:{card};color:{fg};border-color:#168BFF66;}}
    [data-baseweb="input"],[data-baseweb="textarea"],[data-baseweb="base-input"], [data-testid="stChatMessage"]{{background:{card};color:{fg};}}
    [data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"],summary{{color:{fg};}}
    h1,h2,h3,p,label,[data-testid="stMetricValue"],[data-testid="stMetricLabel"]{{color:{fg}!important;}}
    [data-testid="stCaptionContainer"]{{color:{muted}!important;}}
    [data-testid="stMetric"]{{background:{card};border:1px solid #168BFF66;border-top:3px solid #168BFF;padding:22px;border-radius:18px;transition:transform .2s,border-color .2s;}}
    [data-testid="stMetric"]:hover{{transform:translateY(-2px);border-color:#00D9FF;}}
    @keyframes metricReveal{{from{{border-color:#00D9FF;box-shadow:0 0 18px #168BFF44;}}to{{border-color:#168BFF66;box-shadow:none;}}}}
    [data-testid="stMetric"]{{animation:metricReveal .6s ease-out;}}
    .stButton button,.stDownloadButton button{{min-height:44px;border-radius:12px;}}
    button:focus-visible,input:focus-visible,textarea:focus-visible{{outline:3px solid #168BFF!important;outline-offset:3px;}}
    [data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,[data-baseweb="select"]>div{{background:{card};color:{fg};}}
    .block-container{{max-width:1500px;padding-top:2rem;}}
    @media(max-width:640px){{.block-container{{padding:1rem;}}[data-testid="stMetric"]{{padding:12px;}}}}
    @media(prefers-reduced-motion:reduce){{*{{animation:none!important;transition:none!important;}}}}
    </style>''', unsafe_allow_html=True)
    st.caption('AMBER HEART ACADEMY  /  PERSONAL FINANCE OS')
    if any(r.get('demo') for r in store.load('transactions')):
        st.info('DEMO RECORDS PRESENT — fictional Jamaican financial data is clearly marked in the ledger.')
    {'Dashboard': dashboard, 'Income & Expenses': transactions, 'Documents': documents, 'Knowledge Base': knowledge, 'Ask SmartBudget': chat}[st.session_state.screen](store)
except (ValueError, OSError) as exc:
    st.error(str(exc))
    st.info('Your original files have been preserved. Check data files and folder permissions before retrying.')
