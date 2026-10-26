"""Read-only visual components. All actions remain native Streamlit widgets."""
from html import escape
from pathlib import Path
import streamlit as st
from services.core import money

def caption(text):
    """Prevent JMD dollar signs from becoming Markdown math delimiters."""
    st.caption(str(text).replace('$',r'\$'))

CATEGORY_COLORS = ['#00E5FF','#FF668A','#00E6B8','#FFC857','#9D5CFF','#FF4FD8','#168BFF']
def category_color(label):
    import hashlib
    from services.core import CATEGORIES
    mapping={'Housing':'#00E5FF','Rent':'#00E5FF','Groceries':'#FF668A','Food':'#FF668A','Transport':'#FFC857','Utilities':'#9D5CFF','Entertainment':'#168BFF','Other':'#8C9BFF','Health':'#00E6B8'}
    if label in mapping: return mapping[label]
    index = CATEGORIES.index(label) if label in CATEGORIES else int(hashlib.sha256(label.encode()).hexdigest()[:8],16)
    return CATEGORY_COLORS[index % len(CATEGORY_COLORS)]

def category_legend(categories):
    colors=[category_color(label) for label in categories]
    total=sum(categories.values())
    icons={'Housing':'⌂','Groceries':'♧','Food':'♧','Transport':'▰','Utilities':'ϟ','Entertainment':'✧','Health':'✚','Other':'◉'}
    html='<div class="category-legend">'
    for index,(label,value) in enumerate(categories.items()):
        html+=f'<div class="category-item"><span class="category-dot" style="background:{colors[index%len(colors)]}"></span><span>{icons.get(label,"◈")} {escape(label)}<small>{value/total:.0%} of spending</small><strong>{escape(money(value))}</strong></span></div>'
    st.markdown(html+'</div>',unsafe_allow_html=True)

def apply_theme(light=False):
    values = {
        'BG':'#eef3fc' if light else '#05070d',
        'FG':'#12213c' if light else '#f5f9ff',
        'MUTED':'#405776' if light else '#a9bdd8',
        'SURFACE':'rgba(255,255,255,.92)' if light else 'rgba(12,26,49,.88)',
        'INPUT':'#ffffff' if light else '#0b1930',
        'SIDE':'#e4edfa' if light else '#071226',
        'GRID':'rgba(54,100,164,.18)' if light else 'rgba(98,155,228,.12)',
        'INCOME':'#00658c' if light else '#42cfff',
        'EXPENSE':'#b51d46' if light else '#ff788f',
        'BALANCE':'#237500' if light else '#39ff14',
        'SAVINGS':'#7431b6' if light else '#c13bff',
    }
    css=(Path(__file__).parent/'theme.css').read_text(encoding='utf-8')
    for name,value in values.items(): css=css.replace('{{'+name+'}}',value)
    if light: css += (Path(__file__).parent/'light-actions.css').read_text(encoding='utf-8')
    neo = ('--neo-shadow:#a9b9cf99;--neo-highlight:#ffffff;--neo-edge:#ffffffcc;--neo-well:#e9f0f9;' if light else '--neo-shadow:#000711cc;--neo-highlight:#29405a80;--neo-edge:#46617c55;--neo-well:#0b1729;')
    css += ':root{'+neo+'}' + (Path(__file__).parent/'dashboard-neumorphic.css').read_text(encoding='utf-8')
    hud = ('--hud-surface:#f8fbff;--hud-base:#dce7f5;--hud-ink:#10213b;--hud-shadow:#9eb0c669;--hud-focus:#10213b;' if light else '--hud-surface:#050a12;--hud-base:#02050a;--hud-ink:#f5f9ff;--hud-shadow:#00000099;--hud-focus:#00d9ff;')
    css += ':root{'+hud+'}' + (Path(__file__).parent/'quick-actions-hud.css').read_text(encoding='utf-8')
    css += (Path(__file__).parent/'quick-actions-orbit.css').read_text(encoding='utf-8')
    css += (Path(__file__).parent/'quick-actions-glass.css').read_text(encoding='utf-8')
    st.markdown('<style>'+css+'</style>',unsafe_allow_html=True)

def brand():
    st.markdown('<div class="brand"><span class="brand-symbol" aria-hidden="true"><svg viewBox="0 0 48 48" fill="none"><defs><linearGradient id="brand-gradient" x2="1" y2="1"><stop stop-color="#83f8ff"/><stop offset=".5" stop-color="#00d5ff"/><stop offset="1" stop-color="#0070ff"/></linearGradient></defs><path d="M12 5H45L36 16H15L22 22H32L41 31L30 43H1L10 32H29L23 27H13L4 18Z" fill="url(#brand-gradient)" stroke="#65eaff" stroke-width=".8"/></svg></span><div><strong>SmartBudget <em>JA</em></strong><small>YOUR MONEY. IN MOTION.</small></div></div>',unsafe_allow_html=True)

def page_intro(title,subtitle,eyebrow='SMARTBUDGET JA'):
    dashboard=title=='Your money. In motion.'
    title_html=escape(title).replace('In motion.', '<span class="motion-title">In motion.</span>')
    greeting='Good evening' if __import__('datetime').datetime.now().hour>=17 else 'Your financial overview'
    extra='<div class="hero-orbit" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>' if dashboard else ''
    st.markdown(f'<div class="page-intro {"dashboard-hero" if dashboard else ""}"><span class="eyebrow">{greeting if dashboard else escape(eyebrow)}</span><h1>{title_html}</h1><p>{escape(subtitle)}</p>{extra}</div>',unsafe_allow_html=True)

def summary_cards(items, history=None, progress=0):
    from components.financial_widgets import financial_cards
    return financial_cards(items, st.session_state.get('theme') == 'Light', history, progress)

def recent_rows(rows):
    if not rows:
        st.caption('Your next transaction will appear here.'); return
    html='<div class="activity-list">'
    for row in rows:
        income=row['type']=='Income'
        html+=f'<div class="activity-row"><span class="activity-icon {"positive" if income else "negative"}" aria-hidden="true">{"↗" if income else "↙"}</span><div class="activity-copy"><strong>{escape(row["description"])}</strong><small>{escape(row["date"])} · {escape(row["category"])} · {escape(row["type"])}</small></div><span class="activity-amount {"positive" if income else "negative"}">{escape(money(row["amount"]))}</span></div>'
    st.markdown(html+'</div>',unsafe_allow_html=True)

def knowledge_preview(title,text,source):
    st.markdown(f'<div class="knowledge-preview"><span class="eyebrow">LOCAL KNOWLEDGE</span><h3>{escape(title)}</h3><p>{escape(text[:170])}{"…" if len(text)>170 else ""}</p><small>{escape(source)}</small></div>',unsafe_allow_html=True)
