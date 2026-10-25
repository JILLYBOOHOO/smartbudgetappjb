from datetime import date
import pytest
from services.core import *

@pytest.fixture
def store(tmp_path):
    s=Store(tmp_path); seed(s); return s

def tx(kind,amount,cat='Groceries',when='2026-10-01'):
    return dict(id=uid(),type=kind,amount=cents(amount),category=cat,date=when,description='Test')

def test_precision():
    assert cents('0.10')+cents('0.20')==30
    assert cents('1.005')==101
    for value in ['NaN','Infinity','0','-4','abc']:
        with pytest.raises(ValueError): cents(value)

def test_income_expense_balance_category_month():
    rows=[tx('Income',100),tx('Expense','12.34'),tx('Expense',5,'Rent','2026-09-01')]
    assert totals(rows)==(10000,1734,8266)
    assert categories(rows)=={'Groceries':1234,'Rent':500}
    assert totals(period(rows,'2026-10'))==(10000,1234,8766)

def test_storage_edit_delete_restart(store):
    row=tx('Expense',40); store.put('transactions',row)
    store.put('transactions',{**row,'amount':5000})
    assert Store(store.root).load('transactions')[0]['amount']==5000
    assert len(store.load('transactions'))==1
    store.delete('transactions',row['id']); assert store.load('transactions')==[]

def test_corruption_preserved(store):
    p=store.path('transactions'); p.write_text('{bad')
    with pytest.raises(ValueError,match='preserved'): store.load('transactions')
    assert p.read_text()=='{bad'

def test_invalid_loaded_record(store):
    store.save('transactions',[{'id':'x','amount':1.2}])
    with pytest.raises(ValueError): store.load('transactions')

def test_budget_and_actions():
    rows=[tx('Expense',85)]
    b=dict(id='b',month='2026-10',category='Groceries',limit=10000,threshold=80)
    assert utilization(b,rows)==(8500,1500,.85)
    assert '85%' in actions(rows,[b],[],'2026-10')[0][0]
    assert actions([],[],[],'2026-10')
    assert not actions(rows,[],[],'2026-10')

def test_savings():
    g=dict(name='Laptop',target=10000,contributions=[dict(amount=8000)])
    assert saved(g)==8000
    assert actions([tx('Expense',1)],[],[g],'2026-10')

def test_retrieval(store):
    result=retrieve('What is an emergency fund?',store.load('knowledge'))
    assert result[0]['title']=='Emergency funds'
    assert retrieve('zzzzqqq',store.load('knowledge'))==[]

def test_documents_errors_and_text():
    assert extract('../../bill.txt',b'Fictional bill')=='Fictional bill'
    for name,content in [('bad.exe',b'hi'),('empty.txt',b''),('bad.pdf',b'notpdf'),('bad.txt',b'\xff'),('big.txt',b'x'*(10*1024*1024+1))]:
        with pytest.raises((ValueError,UnicodeError)): extract(name,content)
    assert 'Amount' in extract('bill.csv',b'Item,Amount\nRent,48000')

def test_pdf_text_and_scan():
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, NameObject, DictionaryObject
    writer=PdfWriter(); page=writer.add_blank_page(300,300)
    font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
    page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(font)})})
    stream=DecodedStreamObject(); stream.set_data(b'BT /F1 12 Tf 10 250 Td (Fictional electricity bill JMD 9000) Tj ET')
    page[NameObject('/Contents')]=writer._add_object(stream)
    output=io.BytesIO(); writer.write(output)
    assert 'electricity' in extract('bill.pdf',output.getvalue())
    blank=PdfWriter(); blank.add_blank_page(100,100); output=io.BytesIO(); blank.write(output)
    with pytest.raises(ValueError,match='OCR'): extract('scan.pdf',output.getvalue())

def test_demo_idempotent_and_assistant(store):
    demo(store,date(2026,10,25)); demo(store,date(2026,10,25))
    assert len(store.load('transactions'))==32
    assert totals(period(store.load('transactions'),'2026-10'))==(18500000,10900000,7600000)
    assert 'J$76,000.00' in answer('What is my available balance?',store,'2026-10')
    assert 'Groceries' in answer('Which category has the highest spending?',store,'2026-10') or 'Rent' in answer('Which category has the highest spending?',store,'2026-10')
    assert 'Source:' in answer('What is an emergency fund?',store,'2026-10')
    assert previous('2026-01')=='2025-12'
