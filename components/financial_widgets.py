"""Supported Streamlit v2 financial display; Python owns all monetary values."""
from pathlib import Path
import streamlit as st
from services.core import money

@st.cache_resource
def renderer(css,js):
    root=Path(__file__).parent
    return st.components.v2.component("financial_glass",html='<section class="money-grid" aria-label="Financial overview"></section>',css=css,js=js)

def financial_cards(items,light=False,history=None,progress=0):
    root=Path(__file__).parent
    return renderer((root/'financial_widgets.css').read_text(),(root/'financial_widgets.js').read_text())(data={"light":light,"history":history or {},"progress":progress,"items":[dict(tone=t,icon=i,label=l,cents=v,formatted=money(v),note=n) for t,i,l,v,n in items]},key="financial_overview",on_add_record_change=lambda:None)
