"""Explainable local suggestions. Nothing is saved until reviewed."""
import io
import re
from decimal import Decimal
from datetime import date, timedelta
import pandas as pd
from services.core import cents, CATEGORIES

CATEGORY_HINTS = {
    'Salary': ['salary', 'payroll', 'wages'],
    'Freelance Income': ['freelance', 'client payment'],
    'Electricity': ['electricity', 'jps'], 'Water': ['water bill', 'nwc'],
    'Internet': ['internet', 'wifi', 'flow', 'digicel broadband'],
    'Phone Credit': ['phone credit', 'top up', 'topup', 'digicel'],
    'Rent': ['rent', 'landlord'],
    'Groceries': ['grocery', 'groceries', 'supermarket', 'food', 'super plus', 'pricesmart', 'hi lo', 'hilo', 'megamart', 'progressive', 'walmart'],
    'Transportation': ['taxi', 'bus fare', 'transport', 'gas', 'petrol', 'fuel', 'shell', 'texaco', 'totalenergies', 'uber'],
    'Healthcare': ['doctor', 'pharmacy', 'medical', 'hospital', 'dental'],
    'Education': ['school', 'tuition', 'education', 'college', 'academy'],
    'Entertainment': ['movie', 'entertainment', 'netflix', 'spotify', 'restaurant', 'kfc', 'burger king', 'lunch', 'dinner'],
}

def categorize(description, kind='Expense'):
    normalized = re.sub(r'[^a-z0-9]+', ' ', description.lower()).strip()
    for category, words in CATEGORY_HINTS.items():
        if category in ['Salary', 'Freelance Income'] and kind != 'Income':
            continue
        if any(re.search(r'\b'+re.escape(word)+r'\b', normalized) for word in words):
            return category
    return 'Other'

def suggest(text, kind=None):
    lowered = text.lower()
    kind = kind or ('Income' if re.search(r'\b(made|earned|received|salary|paid me|income)\b', lowered) else 'Expense')
    # Prefer a labelled total; otherwise accept an explicitly currency-marked amount.
    labelled = re.search(r'\b(?:grand total|amount due|total due|total|amount)\s*[:=]?\s*(?:JMD|J\$|\$)?\s*([\d,]+(?:\.\d{1,2})?)', text, re.I)
    currency = re.search(r'(?:JMD|J\$|\$)\s*([\d,]+(?:\.\d{1,2})?)', text, re.I)
    casual = re.search(r'\b(?:spent|made|earned|received|paid|bought)\s+(?:JMD|J\$|\$)?\s*([\d,]+(?:\.\d{1,2})?)(?:\s*(k))?', text, re.I)
    match = labelled or currency or casual
    amount = ''
    if match:
        raw = match.group(1).replace(',', '')
        amount = str(Decimal(cents(raw) * (1000 if match is casual and casual.group(2) else 1)) / 100)
    category = categorize(text,kind)
    when = date.today() - timedelta(days=1 if 'yesterday' in lowered else 0)
    iso = re.search(r'\b\d{4}-\d{2}-\d{2}\b', text)
    if iso:
        try: when=date.fromisoformat(iso.group())
        except ValueError: pass
    return dict(type=kind,amount_text=amount,category=category,date=when.isoformat(),description=text.strip().splitlines()[0][:160] if text.strip() else '')

def csv_drafts(content):
    frame=pd.read_csv(io.BytesIO(content),dtype=str).fillna('')
    columns={str(c).strip().lower():c for c in frame.columns}
    if 'amount' not in columns and 'amount_jmd' not in columns:
        raise ValueError('CSV needs an amount or amount_jmd column in JMD, plus optional date, description, type and category columns.')
    if len(frame)>1000: raise ValueError('Import at most 1,000 transactions per file.')
    result=[]
    for index,row in frame.iterrows():
        def value(name,default=''): return str(row[columns[name]]).strip() if name in columns else default
        try:
            raw=value('amount_jmd',value('amount')).replace(',','').replace('J$','').replace('$','')
            negative=raw.startswith('-')
            amount=cents(raw.lstrip('+-'))
            kind=value('type','Expense' if negative else 'Expense').title()
            if kind not in ['Income','Expense']: raise ValueError('Type must be Income or Expense.')
            when=value('date',date.today().isoformat()); date.fromisoformat(when)
            description=value('description',value('merchant','Imported transaction')) or 'Imported transaction'
            category=value('category',suggest(description,kind)['category'])
            if category not in CATEGORIES: category='Other'
            result.append(dict(type=kind,amount=amount,date=when,description=description,category=category,source='',payment='Other',notes='Reviewed CSV import'))
        except ValueError as exc:
            raise ValueError(f'CSV row {index+2}: {exc}') from exc
    if not result: raise ValueError('CSV contains no transactions.')
    return result
