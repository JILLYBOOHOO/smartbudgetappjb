"""Local single-user finance, persistence, retrieval and document services."""
import csv
import io
import json
import os
import re
import uuid
from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

CATEGORIES = ['Salary', 'Freelance Income', 'Groceries', 'Rent', 'Electricity', 'Water', 'Internet', 'Phone Credit', 'Transportation', 'Education', 'Healthcare', 'Entertainment', 'Savings', 'Other']
KINDS = ('transactions', 'budgets', 'goals', 'documents', 'knowledge', 'settings')

def uid():
    return uuid.uuid4().hex

def cents(value):
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number <= 0 or number > Decimal('1000000000'):
            raise ValueError('Enter an amount above zero and at most J$1 billion.')
        return int((number * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    except (InvalidOperation, TypeError):
        raise ValueError('Enter a valid monetary amount.') from None

def money(value):
    return f'J${Decimal(value) / 100:,.2f}'

class Store:
    """Atomic replacements; corruption is preserved and reported, never overwritten."""
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / 'uploads').mkdir(exist_ok=True)

    def path(self, kind):
        if kind not in KINDS:
            raise ValueError('Unknown record collection.')
        return self.root / f'{kind}.json'

    def load(self, kind):
        path = self.path(kind)
        if not path.exists():
            self.save(kind, [])
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(data, list) or any(not isinstance(x, dict) or not isinstance(x.get('id'), str) for x in data):
                raise ValueError('Expected records with string IDs.')
            if len({x['id'] for x in data}) != len(data):
                raise ValueError('Duplicate IDs.')
            for row in data:
                if kind == 'transactions':
                    validate_transaction(row)
                elif kind == 'budgets':
                    if type(row.get('limit')) is not int or row['limit'] <= 0 or not re.fullmatch(r'\d{4}-\d{2}', row.get('month', '')):
                        raise ValueError('Invalid budget.')
                elif kind == 'goals':
                    if type(row.get('target')) is not int or row['target'] <= 0 or any(type(c.get('amount')) is not int or c['amount'] <= 0 for c in row.get('contributions', [])):
                        raise ValueError('Invalid savings goal.')
                elif kind == 'knowledge' and not all(isinstance(row.get(k), str) for k in ['title', 'text', 'topic', 'source']):
                    raise ValueError('Invalid knowledge entry.')
                elif kind == 'documents' and not all(isinstance(row.get(k), str) for k in ['name', 'text', 'file']):
                    raise ValueError('Invalid document metadata.')
            return data
        except (ValueError, KeyError, TypeError) as exc:
            raise ValueError(f'Cannot read {path.name}: {exc} Original file preserved. Restore it from a backup or repair the JSON.') from exc

    def save(self, kind, records):
        path = self.path(kind)
        temp = path.with_suffix('.' + uid() + '.tmp')
        try:
            with temp.open('w', encoding='utf-8') as handle:
                json.dump(records, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, path)
        finally:
            temp.unlink(missing_ok=True)

    def put(self, kind, record):
        rows = self.load(kind)
        rows = [x for x in rows if x['id'] != record['id']] + [record]
        self.save(kind, rows)

    def delete(self, kind, identifier):
        self.save(kind, [x for x in self.load(kind) if x['id'] != identifier])

def validate_transaction(row):
    if row.get('type') not in ['Income', 'Expense'] or type(row.get('amount')) is not int or row['amount'] <= 0:
        raise ValueError('Invalid transaction amount or type.')
    date.fromisoformat(row['date'])
    if row.get('category') not in CATEGORIES or not row.get('description', '').strip():
        raise ValueError('Select a category and enter a description.')

def period(rows, month):
    return [r for r in rows if r['date'].startswith(month)]

def totals(rows):
    income = sum(r['amount'] for r in rows if r['type'] == 'Income')
    expense = sum(r['amount'] for r in rows if r['type'] == 'Expense')
    return income, expense, income - expense

def categories(rows):
    result = Counter()
    for row in rows:
        if row['type'] == 'Expense':
            result[row['category']] += row['amount']
    return dict(result)

def utilization(budget, rows):
    rows = period(rows, budget['month'])
    spent = totals(rows)[1] if budget['category'] == 'All spending' else categories(rows).get(budget['category'], 0)
    return spent, budget['limit'] - spent, spent / budget['limit']

def saved(goal):
    return sum(c['amount'] for c in goal.get('contributions', []))

def previous(month):
    year, mon = map(int, month.split('-'))
    return f'{year if mon > 1 else year - 1:04d}-{mon - 1 if mon > 1 else 12:02d}'

def actions(rows, budgets, goals, month):
    result = []
    if not period(rows, month):
        result.append(('No transactions this month. Add your first record.', 'Income & Expenses'))
    for b in budgets:
        if b['month'] == month:
            spent, remaining, ratio = utilization(b, rows)
            if ratio >= b.get('threshold', 80) / 100:
                result.append((f"{b['category']}: {ratio:.0%} of budget used; {money(abs(remaining))} {'over limit' if remaining < 0 else 'remaining'}.", 'Income & Expenses'))
    old = categories(period(rows, previous(month)))
    for cat, amount in categories(period(rows, month)).items():
        if old.get(cat, 0) > 0 and amount >= old[cat] * 1.5:
            result.append((f'{cat}: {money(amount)} versus {money(old[cat])} in the previous full month. Current month may be incomplete.', 'Income & Expenses'))
    for g in goals:
        if .8 <= saved(g) / g['target'] < 1 and not g.get('completed'):
            result.append((f"{g['name']} is {saved(g) / g['target']:.0%} funded. Record a contribution.", 'Dashboard'))
    return result

SEEDS = {
    'Budgeting': 'Create a budget by recording income, listing essential expenses such as rent and transport, setting category limits, and reviewing actual spending each month.',
    'Saving money': 'Choose an affordable savings contribution after reviewing essential costs. Set a named goal and track contributions regularly.',
    'Emergency funds': 'An emergency fund is money set aside for unexpected essential costs or interrupted income. Start with a small achievable target and build toward several months of essential expenses.',
    'Managing expenses': 'To reduce unnecessary spending, review categories, compare recurring bills, plan grocery shopping, and pause purchases you do not need.',
    'Financial planning': 'List short and long term goals, estimate their costs, choose target dates, and review progress when income or expenses change.',
    'Needs versus wants': 'Needs support essential living, such as housing, groceries and transport to work. Wants improve comfort or enjoyment, such as entertainment. Context matters.',
    'Understanding income': 'Income is money received from salary, freelance work or other sources. In Jamaica, budget using the take-home Jamaican dollar amount you actually receive.',
    'Managing debt': 'List balances, interest costs and minimum payments. Plan required payments first and compare strategies for paying extra. Contact the lender if payments become difficult.',
    'Financial habits': 'Record transactions consistently, review your budget weekly and set realistic savings goals. Small regular actions make records more useful.'
}

def seed(store):
    if not any(s['id'] == 'knowledge_seeded' for s in store.load('settings')):
        existing = store.load('knowledge')
        store.save('knowledge', existing + [dict(id=uid(), title=k, topic=k, text=v, source='SmartBudget JA educational guide') for k, v in SEEDS.items()])
        store.put('settings', {'id': 'knowledge_seeded', 'value': True})

def tokens(text):
    stop = {'what', 'is', 'a', 'an', 'the', 'how', 'can', 'i', 'my', 'to', 'and', 'of', 'do', 'me'}
    return {w.rstrip('s') for w in re.findall(r'[a-z]+', text.lower()) if w not in stop}

def retrieve(question, entries):
    query = tokens(question)
    matches = [(len(query & tokens(e['title'] + ' ' + e['text'])) / max(1, len(query)), e) for e in entries]
    return [e for score, e in sorted(matches, key=lambda pair: pair[0], reverse=True)[:3] if score > 0]

def answer(question, store, month):
    q = question.lower()
    rows = store.load('transactions')
    month = previous(date.today().strftime('%Y-%m')) if 'last month' in q else date.today().strftime('%Y-%m') if 'this month' in q else month
    filtered = period(rows, month)
    inc, exp, net = totals(filtered)
    if 'goal' in q and ('closest' in q or 'completion' in q):
        goals = [g for g in store.load('goals') if not g.get('completed') and saved(g) < g['target']]
        if not goals:
            return 'There are no unfinished savings goals.'
        g = max(goals, key=lambda x: saved(x) / x['target'])
        return f"{g['name']} is closest: {saved(g) / g['target']:.1%}, with {money(g['target'] - saved(g))} remaining."
    if 'saved' in q or 'how much have i saved' in q:
        return f"Recorded savings contributions across all dates: {money(sum(saved(g) for g in store.load('goals')))}. These are tracked separately from expenses."
    if 'budget' in q and ('over' in q or 'am i' in q):
        budgets = [b for b in store.load('budgets') if b['month'] == month]
        return '\n\n'.join(f"{b['category']}: {money(utilization(b, rows)[0])} spent of {money(b['limit'])}; {utilization(b, rows)[2]:.0%} used." for b in budgets) or f'No budgets configured for {month}.'
    if 'balance' in q or 'cash flow' in q:
        return f'{month}: net cash flow is {money(net)} (income {money(inc)} minus expenses {money(exp)}). This is not a bank account balance.'
    if 'income' in q and any(s in q for s in ['how much', 'what was', 'total']):
        return f'{month}: recorded income is {money(inc)}.'
    if any(s in q for s in ['spend', 'spent', 'spending']) and any(s in q for s in ['how much', 'highest', 'most', 'total']):
        cats = categories(filtered)
        if 'highest' in q or 'most' in q:
            return f'{month}: highest spending is {max(cats, key=cats.get)} at {money(max(cats.values()))}.' if cats else f'No expenses recorded for {month}.'
        for cat in CATEGORIES:
            if cat.lower() in q:
                return f'{month}: {cat} spending is {money(cats.get(cat, 0))}.'
        return f'{month}: recorded expenses are {money(exp)}.'
    entries = retrieve(question, store.load('knowledge'))
    return '\n\n'.join(f"{e['text']}\n\nSource: {e['title']} — {e['source']}" for e in entries) if entries else 'I could not match that question. Try asking about recorded income, spending, budgets, savings, or a topic in your knowledge base.'

def extract(name, content):
    if not content or len(content) > 10 * 1024 * 1024:
        raise ValueError('Upload a nonempty file up to 10 MB.')
    ext = Path(name).suffix.lower()
    try:
        if ext == '.pdf':
            from pypdf import PdfReader
            if not content.startswith(b'%PDF-'):
                raise ValueError('The file is not a valid PDF.')
            reader = PdfReader(io.BytesIO(content))
            if reader.is_encrypted:
                raise ValueError('Encrypted PDFs are not supported.')
            if len(reader.pages) > 100:
                raise ValueError('PDFs must contain at most 100 pages.')
            text = '\n'.join(page.extract_text() or '' for page in reader.pages)
        elif ext in ['.txt', '.csv']:
            text = content.decode('utf-8-sig')
            if '\x00' in text:
                raise ValueError('The file contains binary content.')
            if ext == '.csv':
                import pandas as pd
                frame = pd.read_csv(io.StringIO(text))
                text = frame.to_csv(index=False)
        else:
            raise ValueError('Supported formats: PDF, TXT and CSV.')
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f'Cannot process this document: {type(exc).__name__}. Use a readable UTF-8 text/CSV or unencrypted text PDF.') from exc
    if not text.strip():
        raise ValueError('No extractable text. This may be a scanned PDF. OCR is not available; upload a text-based version.')
    if len(text) > 1_000_000:
        raise ValueError('Extracted text exceeds the one-million-character limit.')
    return text

def demo(store, today=None):
    today = today or date.today()
    months = [today.strftime('%Y-%m')]
    for _ in range(3):
        months.append(previous(months[-1]))
    rows = [r for r in store.load('transactions') if not r.get('demo')]
    for index, month in enumerate(months):
        for kind, cat, amount in [('Income', 'Salary', 150000), ('Income', 'Freelance Income', 35000), ('Expense', 'Rent', 48000), ('Expense', 'Groceries', 23500 + index * 1200), ('Expense', 'Transportation', 14000), ('Expense', 'Electricity', 9000), ('Expense', 'Internet', 6500), ('Expense', 'Entertainment', 8000)]:
            rows.append(dict(id=uid(), type=kind, category=cat, amount=cents(amount), date=f'{month}-01', description=f'Fictional {cat}', source='Demo', payment='Bank transfer', notes='', demo=True))
    store.save('transactions', rows)
    month = months[0]
    for kind, records in [('budgets', [dict(id=uid(), month=month, category='Groceries', limit=cents(28000), threshold=80, demo=True)]), ('goals', [dict(id=uid(), name='Emergency Fund', target=cents(100000), deadline='', completed=False, contributions=[dict(id=uid(), amount=cents(82500), date=today.isoformat())], demo=True)])]:
        store.save(kind, [r for r in store.load(kind) if not r.get('demo')] + records)
