from pathlib import Path
from streamlit.testing.v1 import AppTest
from services.core import Store, demo, seed

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
    next(w for w in app.text_input if w.label=='Income source (required for income)').set_value('Fictional employer')
    next(w for w in app.text_input if w.label=='Description').set_value('Test salary')
    next(b for b in app.button if b.label=='Save transaction').click().run()
    assert not app.exception
    assert Store(tmp_path).load('transactions')[0]['amount']==123456
    assert not AppTest.from_file(str(APP)).run().exception

def test_budget_goal_chat_and_safe_reset(tmp_path,monkeypatch):
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
    next(b for b in app.sidebar.button if b.label=='Load Demo Data').click().run()
    assert len(Store(tmp_path).load('transactions'))==32
    assert next(b for b in app.sidebar.button if b.label=='Reset Demo Data').disabled
    next(c for c in app.sidebar.checkbox if c.label=='Confirm removal of demo records only').check().run()
    next(b for b in app.sidebar.button if b.label=='Reset Demo Data').click().run()
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
