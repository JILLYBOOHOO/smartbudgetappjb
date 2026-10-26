from services.statements import csv_statement,text_statement,analysis
from services.capture import categorize

def test_merchant_categories_and_income_context():
    assert categorize('POS MEGAMART KINGSTON')=='Groceries'
    assert categorize('JPS monthly bill')=='Electricity'
    assert categorize('Taxi fare')=='Transportation'
    assert categorize('Payroll deposit','Income')=='Salary'
    assert categorize('Unknown merchant')=='Other'

def test_bank_csv_debit_credit_and_balance_exclusion():
    content=b'Transaction Date,Details,Debit,Credit,Balance\n01/10/2026,Opening balance,,,10000.00\n02/10/2026,MEGAMART,2500.00,,7500.00\n03/10/2026,PAYROLL,,150000.00,157500.00'
    rows,notes=csv_statement(content)
    assert len(rows)==2 and len(notes)==1
    assert rows[0]['amount']==250000 and rows[0]['category']=='Groceries'
    assert rows[1]['type']=='Income' and not rows[1]['needs_review']
    assert analysis(rows)==(15000000,250000,{'Groceries':250000})

def test_pdf_text_rows_date_order_and_uncertainty():
    text='Bank statement\n01/10/2026 Opening balance 100,000.00\n02/10/2026 POS MEGAMART 2,500.00 DR 97,500.00\n03/10/2026 PAYROLL 150,000.00 CR 247,500.00\n04/10/2026 UNKNOWN MERCHANT 500.00 247,000.00'
    rows,notes=text_statement(text)
    assert len(rows)==3 and len(notes)==1
    assert rows[0]['date']=='2026-10-02' and rows[0]['amount']==250000
    assert rows[1]['type']=='Income' and not rows[1]['needs_review']
    assert rows[2]['needs_review']
    rows,_=text_statement('02/10/2026 MEGAMART 200.00 DR',day_first=False)
    assert rows[0]['date']=='2026-02-10'

def test_unrecognized_rows_not_fabricated():
    rows,notes=text_statement('No readable transactions here')
    assert rows==[]
    rows,notes=text_statement('01/10/2026 MEGAMART 1,000.00 2,000.00 3,000.00')
    assert rows==[] and notes
    rows,notes=csv_statement(b'Date,Description,Amount\n2026-10-01,Unknown,300\n2026-10-02,Taxi,-200')
    assert rows[0]['needs_review'] and not rows[1]['needs_review']
