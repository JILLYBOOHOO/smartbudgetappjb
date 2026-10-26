from datetime import date
from pathlib import Path
import os
import importlib
import streamlit as st
from services.core import Store, seed
# Refresh stateless UI helpers when their source changes, including on servers
# whose file watcher keeps imported modules cached. Financial services stay loaded.
refresh_dependents=False
for module_name in ['components.financial_widgets','components.design','screens.capture','screens.pages','components.shell']:
    ui_module=importlib.import_module(module_name)
    source_stamp=Path(ui_module.__file__).stat().st_mtime_ns
    if refresh_dependents or getattr(ui_module,'_ui_source_stamp',None)!=source_stamp:
        importlib.reload(ui_module)
        ui_module._ui_source_stamp=source_stamp
        refresh_dependents=True
from screens.pages import dashboard, transactions, documents, knowledge, chat
from screens.capture import open_capture, request_capture
from components.design import apply_theme, brand
from components.shell import topbar, mobile_nav

st.set_page_config(page_title='SmartBudget JA', page_icon='◈', layout='wide')
store = Store(os.environ.get('SMARTBUDGET_DATA', str(Path(__file__).parent / 'data')))
for key, value in {'screen': 'Dashboard', 'month': date.today().strftime('%Y-%m'), 'theme': 'Dark', 'messages': [], 'quick_type': 'Income'}.items():
    st.session_state.setdefault(key, value)
try:
    seed(store)
    with st.sidebar:
        brand()
        st.radio('Navigate', ['Dashboard', 'Income & Expenses', 'Documents', 'Knowledge Base', 'Ask SmartBudget'], key='screen',label_visibility='collapsed',format_func=lambda x:{'Dashboard':'⌂   Dashboard','Income & Expenses':'▧   Income & Expenses','Documents':'▤   Documents','Knowledge Base':'▣   Knowledge Base','Ask SmartBudget':'✧   Ask SmartBudget'}[x])
        def open_finance_panel(panel):
            st.session_state.screen='Dashboard'
            st.session_state.manage_finances=True
            st.session_state.pop('budget_open',None)
            st.session_state.pop('contribution_open',None)
            st.session_state.savings_open=panel=='Goals'
            if panel=='Budgets': st.session_state.budget_open=True
        with st.container(key='sidebar_analytics'):
            st.caption('ANALYTICS')
            st.button('Budgets',icon=':material/account_balance_wallet:',on_click=open_finance_panel,args=('Budgets',),width='stretch')
            st.button('Savings goals',icon=':material/flag:',on_click=open_finance_panel,args=('Goals',),width='stretch')
            st.button('Transaction history',icon=':material/bar_chart:',on_click=lambda:st.session_state.update(screen='Income & Expenses'),width='stretch')
        st.radio('Appearance', ['Dark', 'Light'], horizontal=True, key='theme')
        st.divider()
        st.caption('Single-user • Local storage • JMD')
        import json
        st.download_button('Export all records', json.dumps({k: store.load(k) for k in ['transactions', 'budgets', 'goals', 'documents', 'knowledge', 'settings']}, indent=2), 'smartbudget-backup.json', 'application/json')
        with st.container(key='sidebar_assistant'):
            st.button('Ask SmartBudget',icon=':material/smart_toy:',key='sidebar_ask',on_click=lambda:st.session_state.update(screen='Ask SmartBudget'),width='stretch')
    apply_theme(st.session_state.theme == 'Light')
    with st.container(key='mobile_brand'):
        brand()
    topbar(store)
    if st.session_state.get('notice'):
        st.success(st.session_state.pop('notice'))
    {'Dashboard': dashboard, 'Income & Expenses': transactions, 'Documents': documents, 'Knowledge Base': knowledge, 'Ask SmartBudget': chat}[st.session_state.screen](store)
    mobile_nav()
    open_capture(store)
except (ValueError, OSError) as exc:
    st.error(str(exc))
    st.info('Your original files have been preserved. Check data files and folder permissions before retrying.')


