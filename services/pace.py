"""Budget pace uses calendar progress, never a fabricated health score."""
import calendar
from datetime import date
from services.core import period,totals


def spending_pace(rows,budgets,month,today=None):
    today=today or date.today()
    start=date.fromisoformat(month+'-01')
    days=calendar.monthrange(start.year,start.month)[1]
    end=date(start.year,start.month,days)
    budget=next((b for b in budgets if b['month']==month and b['category']=='All spending'),None)
    spent=totals(period(rows,month))[1]
    if not budget or budget['limit']<=0:
        return dict(spent=spent,budget=None,status='Set a monthly budget',expected=None)
    limit=budget['limit'];used=spent/limit*100
    expected=0 if today<start else (100 if today>end else today.day/days*100)
    if today<start:
        status='Month not started';difference=None
    elif today>end:
        status='Over budget' if spent>limit else 'Within budget';difference=None
    else:
        status='Over budget' if spent>limit else ('On track' if used<=expected else 'Ahead of pace')
        difference=used-expected
    return dict(spent=spent,budget=limit,remaining=limit-spent,used=used,needle=min(max(used,0),100),expected=expected,status=status,difference=difference,days=days,elapsed=max(0,min((today-start).days+1,days)))
