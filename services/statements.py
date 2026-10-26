"""Local, conservative bank export parsing. All rows are drafts for review."""
import io
import re
from datetime import datetime
from decimal import Decimal
import pandas as pd
from services.core import cents
from services.capture import categorize

def parse_date(value, day_first=True):
    value=value.strip()
    formats=['%Y-%m-%d','%Y/%m/%d','%d %b %Y','%d %B %Y','%d-%b-%Y']
    formats += ['%d/%m/%Y','%d-%m-%Y','%d/%m/%y'] if day_first else ['%m/%d/%Y','%m-%d-%Y','%m/%d/%y']
    for fmt in formats:
        try: return datetime.strptime(value,fmt).date().isoformat()
        except ValueError: pass
    raise ValueError('Use a full date including year. Check the chosen day/month order.')

def amount_value(value):
    clean=re.sub(r'(?i)\b(?:JMD|USD|DR|CR)\b|J\$|\$|,|\s','',str(value))
    if not clean or clean in ['-','—']: return 0
    return cents(clean.strip('()+-'))

def row(when,description,amount,kind,review=False):
    return dict(date=when,description=description.strip(),amount=amount,type=kind,category=categorize(description,kind),source='',payment='Bank transfer',notes='Reviewed bank statement import',needs_review=review)

def csv_statement(content,day_first=True):
    frame=pd.read_csv(io.BytesIO(content),dtype=str).fillna('')
    if len(frame)>1000: raise ValueError('Import at most 1,000 rows at a time.')
    names={re.sub(r'[^a-z]','',str(c).lower()):c for c in frame.columns}
    def find(*aliases): return next((names[a] for a in aliases if a in names),None)
    datecol=find('date','transactiondate','postingdate','valuedate')
    desccol=find('description','details','transactiondescription','narration','merchant','particulars','memo')
    debit=find('debit','debits','withdrawal','withdrawals','moneyout','debitamount')
    credit=find('credit','credits','deposit','deposits','moneyin','creditamount')
    amountcol=find('amount','amountjmd','transactionamount')
    typecol=find('type','transactiontype','debitcredit','drcr')
    if not datecol or not desccol or not (amountcol or debit or credit):
        raise ValueError('Bank CSV needs Date and Description/Details, plus Amount or Debit/Credit columns. Running Balance is never imported as a transaction.')
    rows=[]; skipped=[]
    for index,data in frame.iterrows():
        description=str(data[desccol]).strip()
        if re.search(r'(?i)\b(opening|closing|brought forward|carried forward)\b.*\bbalance\b',description):
            skipped.append(f'Row {index+2}: balance summary excluded.'); continue
        try:
            when=parse_date(str(data[datecol]),day_first)
            out=amount_value(data[debit]) if debit else 0
            incoming=amount_value(data[credit]) if credit else 0
            if out and incoming: raise ValueError('Both debit and credit are populated; split or correct the row.')
            if debit or credit:
                if not (out or incoming):
                    skipped.append(f'Row {index+2}: no debit or credit amount.'); continue
                amount=out or incoming; kind='Expense' if out else 'Income'; review=False
            else:
                raw=str(data[amountcol]); amount=amount_value(raw)
                if not amount:
                    skipped.append(f'Row {index+2}: zero amount excluded.'); continue
                tag=str(data[typecol]).lower().strip() if typecol else ''
                if tag in ['income','credit','cr','deposit']: kind='Income'; review=False
                elif tag in ['expense','debit','dr','withdrawal']: kind='Expense'; review=False
                elif raw.strip().startswith(('-', '(')): kind='Expense'; review=False
                else: kind='Income'; review=True
            rows.append(row(when,description or 'Bank transaction',amount,kind,review))
        except ValueError as exc:
            skipped.append(f'Row {index+2}: {exc}')
    return rows,skipped

DATE_START = re.compile(r'^\s*(\d{4}[-/]\d{2}[-/]\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}[- ]+[A-Za-z]{3,9}[- ]+\d{4})\s+(.+)$')
AMOUNT = re.compile(r'(?<![\w/])(?:JMD\s*|J\$\s*|\$\s*)?[-+]?\(?\d[\d,]*\.\d{2}\)?(?:\s*(?:DR|CR))?\b',re.I)

def text_statement(text,day_first=True):
    rows=[]; skipped=[]
    for number,line in enumerate(text.splitlines(),1):
        match=DATE_START.match(line)
        if not match: continue
        rawdate,detail=match.groups()
        if re.search(r'(?i)\b(opening|closing|brought forward|carried forward)\b.*\bbalance\b',detail):
            skipped.append(f'Line {number}: balance summary excluded.'); continue
        amounts=list(AMOUNT.finditer(detail))
        if not amounts:
            skipped.append(f'Line {number}: no amount with two decimal places.'); continue
        try:
            when=parse_date(rawdate,day_first)
            # Common text export: date, description, transaction amount, running balance.
            # Extra columns are ambiguous and are surfaced instead of guessed.
            if len(amounts)>2:
                raise ValueError('Multiple monetary columns; use a CSV export for this statement layout.')
            first=amounts[0]; raw=first.group()
            description=detail[:first.start()].strip(' -|')
            if not description: raise ValueError('Description missing or wrapped onto another line.')
            marker=(raw+' '+detail[max(0,first.start()-3):first.start()]).upper()
            if re.search(r'\bCR\b',marker): kind='Income'; review=False
            elif re.search(r'\bDR\b',marker) or raw.strip().startswith(('-', '(')): kind='Expense'; review=False
            elif re.search(r'(?i)\b(salary|payroll|deposit|credit interest)\b',description): kind='Income'; review=True
            else: kind='Expense'; review=True
            rows.append(row(when,description,amount_value(raw),kind,review))
        except ValueError as exc:
            skipped.append(f'Line {number}: {exc}')
        if len(rows)>1000: raise ValueError('Import at most 1,000 transactions per statement.')
    return rows,skipped

def analysis(rows):
    income=sum(r['amount'] for r in rows if r['type']=='Income')
    expense=sum(r['amount'] for r in rows if r['type']=='Expense')
    categories={}
    for r in rows:
        if r['type']=='Expense': categories[r['category']]=categories.get(r['category'],0)+r['amount']
    return income,expense,categories
