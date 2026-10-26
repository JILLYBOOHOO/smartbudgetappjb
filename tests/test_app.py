from pathlib import Path
from streamlit.testing.v1 import AppTest
from services.core import Store, demo, seed
from io import BytesIO
import streamlit as st

APP=Path(__file__).resolve().parents[1]/'app.py'

def test_five_screens_and_navigation(tmp_path,monkeypatch):
    monkeypatch.setenv('SMARTBUDGET_DATA',str(tmp_path))
    store=Store(tmp_path); seed(store); demo(store)
    app=AppTest.from_file(str(APP),default_timeout=30).run()
    assert not app.exception
    for page in ['Income & Expenses','Documents','Knowledge Base','Ask SmartBudget','Dashboard']:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, page
    app.sidebar.radio[1].set_value('Light').run()
    assert not app.exception

def test_transaction_form_persistence(tmp_path,monkeypatch):
    monkeypatch.setenv('SMARTBUDGET_DATA',str(tmp_path))
    app=AppTest.from_file(str(APP),default_timeout=30).run()
    app.sidebar.radio[0].set_value('Income & Expenses').run()
    next(w for w in app.text_input if w.label=='Amount (JMD)').set_value('1234.56')
    next(w for w in app.text_input if w.label=='Income source (optional)').set_value('Fictional employer')
    next(w for w in app.text_input if w.label=='What was it for? (optional)').set_value('Test salary')
    next(b for b in app.button if b.label=='Save transaction').click().run()
    assert not app.exception
    assert Store(tmp_path).load('transactions')[0]['amount']==123456
    assert not AppTest.from_file(str(APP)).run().exception

def test_budget_goal_chat_and_no_demo_controls(tmp_path,monkeypatch):
    monkeypatch.setenv('SMARTBUDGET_DATA',str(tmp_path))
    app=AppTest.from_file(str(APP),default_timeout=30).run()
    next(w for w in app.text_input if w.label=='Monthly limit (JMD)').set_value('15000')
    next(b for b in app.button if b.label=='Save budget').click().run()
    assert not app.exception
    assert Store(tmp_path).load('budgets')[0]['limit']==1500000
    next(w for w in app.text_input if w.label=='Goal name').set_value('School laptop')
    next(w for w in app.text_input if w.label=='Target amount (JMD)').set_value('80000')
    next(b for b in app.button if b.label=='Create goal').click().run()
    assert not app.exception
    next(w for w in app.text_input if w.label=='Contribution (JMD)').set_value('1200')
    next(b for b in app.button if b.label=='Record contribution').click().run()
    assert not app.exception
    assert Store(tmp_path).load('goals')[0]['contributions'][0]['amount']==120000
    app.sidebar.radio[0].set_value('Ask SmartBudget').run()
    next(b for b in app.button if b.label=='What is an emergency fund?').click().run()
    assert not app.exception
    assert 'Source:' in app.session_state['messages'][-1]['content']
    assert not any('demo' in b.label.lower() for b in app.sidebar.button)
    assert not Store(tmp_path).load('transactions')
    assert Store(tmp_path).load('goals')[0]['name']=='School laptop'


def test_knowledge_crud(tmp_path,monkeypatch):
    monkeypatch.setenv('SMARTBUDGET_DATA',str(tmp_path))
    app=AppTest.from_file(str(APP),default_timeout=30).run()
    app.sidebar.radio[0].set_value('Knowledge Base').run()
    # Last fields belong to the Add form; earlier fields edit seeded entries.
    [w for w in app.text_input if w.label=='Title'][-1].set_value('School transport')
    [w for w in app.text_area if w.label=='Content'][-1].set_value('Set aside a weekly bus fare allowance.')
    [w for w in app.text_input if w.label=='Topic'][-1].set_value('Transport')
    [w for w in app.text_input if w.label=='Source'][-1].set_value('Student example')
    next(b for b in app.button if b.label=='Add entry').click().run()
    assert not app.exception
    assert any(r['title']=='School transport' for r in Store(tmp_path).load('knowledge'))
    next(w for w in app.text_input if w.label=='Search knowledge').set_value('School transport').run()
    assert not app.exception

def test_invalid_input_is_visible(tmp_path,monkeypatch):
    monkeypatch.setenv('SMARTBUDGET_DATA',str(tmp_path))
    app=AppTest.from_file(str(APP),default_timeout=30).run()
    app.sidebar.radio[0].set_value('Income & Expenses').run()
    next(b for b in app.button if b.label=='Save transaction').click().run()
    assert not app.exception
    assert app.error
    assert Store(tmp_path).load('transactions')==[]

def test_quick_popup_and_optional_fields(tmp_path,monkeypatch):
    monkeypatch.setenv('SMARTBUDGET_DATA',str(tmp_path))
    app=AppTest.from_file(str(APP),default_timeout=30).run()
    next(b for b in app.button if b.label=='Add Income').click().run()
    assert not app.exception
    assert any(w.label=='Amount (JMD)' for w in app.text_input)
    next(w for w in app.text_input if w.label=='Amount (JMD)').set_value('7000')
    next(b for b in app.button if b.label=='Save transaction').click().run()
    assert not app.exception
    record=Store(tmp_path).load('transactions')[0]
    assert record['amount']==700000 and record['type']=='Income'
    assert record['source']=='' and record['description']=='Money received'
    next(b for b in app.button if b.label=='Set Budget').click().run()
    assert not app.exception
    next(w for w in app.text_input if w.label=='Limit (JMD)').set_value('45000')
    next(b for b in app.button if b.label=='Save monthly limit').click().run()
    assert not app.exception
    assert Store(tmp_path).load('budgets')[0]['limit']==4500000

def test_sentence_popup_and_upload_navigation(tmp_path,monkeypatch):
    monkeypatch.setenv('SMARTBUDGET_DATA',str(tmp_path))
    app=AppTest.from_file(str(APP),default_timeout=30).run()
    next(b for b in app.button if b.label=='Add Expense').click().run()
    next(w for w in app.text_input if w.label=='Or say it in one line').set_value('Spent 2500 on groceries yesterday').run()
    next(b for b in app.button if b.label=='Use these details').click().run()
    assert not app.exception
    assert next(w for w in app.text_input if w.label=='Amount (JMD)').value=='2500'
    next(b for b in app.button if b.label=='Save transaction').click().run()
    assert Store(tmp_path).load('transactions')[0]['category']=='Groceries'
    next(b for b in app.button if b.label=='Upload Bill').click().run()
    assert not app.exception
    assert any('PDF' in c.value for c in app.caption)

def test_receipt_review_saves_only_after_confirmation(tmp_path,monkeypatch):
    monkeypatch.setenv('SMARTBUDGET_DATA',str(tmp_path))
    file=BytesIO(b'JPS electricity receipt\n2026-10-01\nAmount due: JMD 9000.25')
    file.name='bill.txt'
    monkeypatch.setattr(st,'file_uploader',lambda *args,**kwargs:file)
    app=AppTest.from_file(str(APP),default_timeout=30).run()
    app.sidebar.radio[0].set_value('Documents').run()
    assert not Store(tmp_path).load('transactions')
    next(b for b in app.button if b.label=='Keep document and review transaction').click().run()
    assert not app.exception
    assert len(Store(tmp_path).load('documents'))==1
    assert not Store(tmp_path).load('transactions')
    assert next(w for w in app.text_input if w.label=='Amount (JMD)').value=='9000.25'
    next(b for b in app.button if b.label=='Save transaction').click().run()
    assert not app.exception
    assert Store(tmp_path).load('transactions')[0]['amount']==900025
    assert not any(b.label=='Save transaction' for b in app.button)

def test_csv_import_review_and_duplicate_block(tmp_path,monkeypatch):
    monkeypatch.setenv('SMARTBUDGET_DATA',str(tmp_path))
    file=BytesIO(b'date,description,amount,type\n2026-10-01,Salary,150000,Income\n2026-10-02,Groceries,2500,Expense')
    file.name='transactions.csv'
    monkeypatch.setattr(st,'file_uploader',lambda *args,**kwargs:file)
    app=AppTest.from_file(str(APP),default_timeout=30).run()
    app.sidebar.radio[0].set_value('Documents').run()
    assert not app.exception
    assert next(b for b in app.button if b.label=='Import reviewed transactions').disabled
    next(c for c in app.checkbox if c.label=='I reviewed all 2 transactions').check().run()
    next(b for b in app.button if b.label=='Import reviewed transactions').click().run()
    assert not app.exception
    assert len(Store(tmp_path).load('transactions'))==2
    assert next(b for b in app.button if b.label=='Import reviewed transactions').disabled


def test_savings_smart_action_popup(tmp_path,monkeypatch):
    monkeypatch.setenv('SMARTBUDGET_DATA',str(tmp_path))
    store=Store(tmp_path); seed(store); demo(store)
    app=AppTest.from_file(str(APP),default_timeout=30).run()
    next(b for b in app.button if b.label=='Add savings contribution').click().run()
    assert not app.exception
    next(w for w in app.text_input if w.label=='Amount to set aside (JMD)').set_value('1000')
    next(b for b in app.button if b.label=='Save contribution').click().run()
    assert not app.exception
    assert sum(c['amount'] for c in store.load('goals')[0]['contributions'])==8350000

def test_manual_entry_autocategorizes_and_allows_override(tmp_path,monkeypatch):
    monkeypatch.setenv('SMARTBUDGET_DATA',str(tmp_path))
    app=AppTest.from_file(str(APP),default_timeout=30).run()
    next(b for b in app.button if b.label=='Add Expense').click().run()
    next(w for w in app.text_input if w.label=='What was it for? (optional)').set_value('MEGAMART groceries').run()
    assert any('Groceries' in w.value for w in app.caption)
    next(w for w in app.text_input if w.label=='Amount (JMD)').set_value('3456.78')
    next(b for b in app.button if b.label=='Save transaction').click().run()
    assert not app.exception
    assert Store(tmp_path).load('transactions')[0]['category']=='Groceries'
    next(b for b in app.button if b.label=='Add Expense').click().run()
    next(w for w in app.text_input if w.label=='What was it for? (optional)').set_value('Taxi')
    next(w for w in app.selectbox if w.label=='Category').set_value('Other').run()
    next(w for w in app.text_input if w.label=='Amount (JMD)').set_value('800')
    next(b for b in app.button if b.label=='Save transaction').click().run()
    assert not app.exception
    assert Store(tmp_path).load('transactions')[-1]['category']=='Other'

def test_bank_statement_import_analysis(tmp_path,monkeypatch):
    monkeypatch.setenv('SMARTBUDGET_DATA',str(tmp_path))
    file=BytesIO(b'Date,Description,Debit,Credit,Balance\n01/10/2026,MEGAMART,2500.00,,97500.00\n02/10/2026,PAYROLL,,150000.00,247500.00')
    file.name='statement.csv'
    monkeypatch.setattr(st,'file_uploader',lambda *args,**kwargs:file)
    app=AppTest.from_file(str(APP),default_timeout=30).run()
    app.sidebar.radio[0].set_value('Documents').run()
    next(w for w in app.radio if w.label=='Use this CSV as').set_value('Bank statement').run()
    assert not app.exception
    assert next(m for m in app.metric if m.label=='Money out').value=='J$2,500.00'
    assert not Store(tmp_path).load('transactions')
    next(c for c in app.checkbox if c.label=='I checked the included transactions against my statement').check().run()
    next(b for b in app.button if b.label=='Import bank statement').click().run()
    assert not app.exception
    rows=Store(tmp_path).load('transactions')
    assert len(rows)==2 and rows[0]['category']=='Groceries' and rows[1]['type']=='Income'
    assert next(b for b in app.button if b.label=='Import bank statement').disabled

def test_global_search_and_reporting_month(tmp_path,monkeypatch):
    monkeypatch.setenv('SMARTBUDGET_DATA',str(tmp_path))
    store=Store(tmp_path);seed(store);demo(store)
    app=AppTest.from_file(str(APP),default_timeout=30).run()
    next(w for w in app.text_input if w.label=='Search SmartBudget').set_value('Fictional Salary').run()
    next(b for b in app.button if b.label=='Open Income & Expenses').click().run()
    assert not app.exception
    assert app.session_state['screen']=='Income & Expenses'
    from services.core import previous
    from datetime import date
    target=previous(date.today().strftime('%Y-%m'))
    next(w for w in app.selectbox if w.label=='Reporting month').set_value(target).run()
    assert app.session_state['month']==target

def test_sidebar_savings_opens_visible_manager(tmp_path,monkeypatch):
    monkeypatch.setenv('SMARTBUDGET_DATA',str(tmp_path))
    app=AppTest.from_file(str(APP),default_timeout=30).run()
    next(b for b in app.sidebar.button if b.label=='Savings goals').click().run()
    assert not app.exception
    assert app.session_state['savings_open']
    assert any(e.label=='Create savings goal' and e.proto.expanded for e in app.expander)
    next(w for w in app.text_input if w.label=='Goal name').set_value('Personal savings')
    next(w for w in app.text_input if w.label=='Target amount (JMD)').set_value('50000')
    next(b for b in app.button if b.label=='Create goal').click().run()
    assert not app.exception
    assert any(e.label=='Manage Personal savings' and e.proto.expanded for e in app.expander)
    next(w for w in app.text_input if w.label=='Contribution (JMD)').set_value('20000')
    next(b for b in app.button if b.label=='Record contribution').click().run()
    assert not app.exception
    assert Store(tmp_path).load('goals')[0]['contributions'][0]['amount']==2000000

