from datetime import date,timedelta
import pytest
from services.capture import suggest,csv_drafts

def test_sentence_suggestions():
    draft=suggest('Spent 2,500 on groceries yesterday')
    assert draft['amount_text']=='2500'
    assert draft['category']=='Groceries'
    assert draft['type']=='Expense'
    assert draft['date']==(date.today()-timedelta(days=1)).isoformat()
    income=suggest('Made 35k from a freelance client')
    assert income['amount_text']=='35000' and income['type']=='Income'

def test_bill_total_preferred_to_date():
    draft=suggest('JPS invoice 2026-10-01\nSubtotal 8000\nAmount due: JMD 9,000.25')
    assert draft['amount_text']=='9000.25'
    assert draft['category']=='Electricity'
    assert suggest('Unknown receipt')['amount_text']==''

def test_csv_review_rows():
    rows=csv_drafts(b'date,description,amount,type\n2026-10-01,Salary,150000,Income\n2026-10-02,groceries,-2500,Expense')
    assert len(rows)==2 and rows[0]['amount']==15000000
    assert rows[1]['amount']==250000 and rows[1]['category']=='Groceries'
    with pytest.raises(ValueError,match='row 2'):
        csv_drafts(b'date,amount\nwrong,123')
    with pytest.raises(ValueError,match='amount'):
        csv_drafts(b'hello,world\na,b')
