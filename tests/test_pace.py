from datetime import date
import pytest
from services.pace import spending_pace


def fixture(spent=3100000,limit=5000000):
    return [dict(type='Expense',amount=spent,date='2026-10-01',category='Groceries')],[dict(month='2026-10',category='All spending',limit=limit)]

def test_current_month_pace_and_full_money_values():
    rows,budgets=fixture()
    state=spending_pace(rows,budgets,'2026-10',date(2026,10,26))
    assert state['used']==62 and state['spent']==3100000 and state['remaining']==1900000
    assert state['expected']==pytest.approx(26/31*100)
    assert state['status']=='On track' and state['difference']<0

def test_over_budget_is_not_hidden_by_clamp():
    rows,budgets=fixture(7500000)
    state=spending_pace(rows,budgets,'2026-10',date(2026,10,31))
    assert state['used']==150 and state['needle']==100
    assert state['status']=='Over budget' and state['remaining']==-2500000

def test_past_future_and_leap_year():
    rows,budgets=fixture()
    assert spending_pace(rows,budgets,'2026-10',date(2026,11,1))['status']=='Within budget'
    future=spending_pace(rows,budgets,'2026-10',date(2026,9,30))
    assert future['status']=='Month not started' and future['difference'] is None
    state=spending_pace([], [dict(month='2024-02',category='All spending',limit=10000)],'2024-02',date(2024,2,29))
    assert state['days']==29 and state['expected']==100

def test_missing_total_budget_does_not_add_category_limits():
    rows,budgets=fixture();budgets[0]['category']='Groceries'
    state=spending_pace(rows,budgets,'2026-10',date(2026,10,26))
    assert state['budget'] is None and state['spent']==3100000
    assert spending_pace(rows,[dict(month='2026-09',category='All spending',limit=10)],'2026-10')['budget'] is None

def test_equal_pace_and_ahead_within_budget():
    rows,budgets=fixture(10000,31000)
    assert spending_pace(rows,budgets,'2026-10',date(2026,10,10))['status']=='On track'
    assert spending_pace(rows,budgets,'2026-10',date(2026,10,2))['status']=='Ahead of pace'
