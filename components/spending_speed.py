"""Plotly speedometer driven entirely by persisted budget and expense values."""
import math
from datetime import date
import plotly.graph_objects as go
import streamlit as st
from services.pace import spending_pace
from services.core import money
from components.design import caption


def speedometer_figure(state,light=False):
    fg='#12213c' if light else '#eaf6ff'
    muted='#405776' if light else '#94afcb'
    def arc(lo,hi,radius=1):
        angles=[math.pi-(lo+(hi-lo)*i/40)/100*math.pi for i in range(41)]
        return [radius*math.cos(a) for a in angles],[radius*math.sin(a) for a in angles]
    fig=go.Figure()
    x,y=arc(0,100)
    fig.add_scatter(x=x,y=y,mode='lines',line=dict(color='#c5d5e6' if light else '#152c42',width=22),hoverinfo='skip',showlegend=False)
    # Small overlapping strokes blend the palette continuously along the arc.
    stops=[(0,(0,217,255)),(35,(57,232,139)),(58,(200,236,34)),(75,(255,188,69)),(100,(255,73,121))]
    for lo in range(100):
        midpoint=lo+.5
        left,right=next((a,b) for a,b in zip(stops,stops[1:]) if a[0]<=midpoint<=b[0])
        blend=(midpoint-left[0])/(right[0]-left[0])
        channels=[round(a+(b-a)*blend) for a,b in zip(left[1],right[1])]
        color='rgb('+','.join(map(str,channels))+')'
        x,y=arc(lo,min(lo+1.15,100))
        fig.add_scatter(x=x,y=y,mode='lines',line=dict(color=color,width=12),hoverinfo='skip',showlegend=False)
    tx=[];ty=[]
    for v in range(0,101,5):
        a=math.pi-v/100*math.pi
        tx.extend([.84*math.cos(a),(.75 if v%20==0 else .79)*math.cos(a),None]);ty.extend([.84*math.sin(a),(.75 if v%20==0 else .79)*math.sin(a),None])
    fig.add_scatter(x=tx,y=ty,mode='lines',line=dict(color=muted,width=2),hoverinfo='skip',showlegend=False)
    for v in range(0,101,20):
        a=math.pi-v/100*math.pi
        fig.add_annotation(x=.65*math.cos(a),y=.65*math.sin(a),text=str(v),showarrow=False,font=dict(color=fg,size=11))
    a=math.pi-state['needle']/100*math.pi
    fig.add_scatter(x=[0,.72*math.cos(a)],y=[0,.72*math.sin(a)],mode='lines',line=dict(color='#005e83' if light else '#e5fbff',width=5),hoverinfo='skip',showlegend=False)
    if state['expected'] is not None:
        a=math.pi-state['expected']/100*math.pi
        fig.add_scatter(x=[.91*math.cos(a),1.07*math.cos(a)],y=[.91*math.sin(a),1.07*math.sin(a)],mode='lines',line=dict(color=fg,width=2),hoverinfo='skip',showlegend=False)
    fig.add_scatter(x=[0],y=[0],mode='markers',marker=dict(size=24,color='#00d9ff',line=dict(color=fg,width=3)),hoverinfo='skip',showlegend=False)
    fig.add_annotation(x=0,y=-.25,text=f"<b>{state['used']:.1f}%</b>",showarrow=False,font=dict(color='#00658c' if light else '#00d9ff',size=32))
    fig.add_annotation(x=0,y=-.43,text='MONTHLY BUDGET USED',showarrow=False,font=dict(color=muted,size=10))
    fig.add_annotation(x=-1,y=-.12,text='LOW',showarrow=False,font=dict(color='#007186' if light else '#00d9ff',size=10))
    fig.add_annotation(x=1,y=-.12,text='HIGH',showarrow=False,font=dict(color='#b51d46' if light else '#ff668a',size=10))
    fig.update_layout(height=285,margin=dict(l=12,r=12,t=8,b=5),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font=dict(color=fg),xaxis=dict(visible=False,range=[-1.15,1.15],fixedrange=True),yaxis=dict(visible=False,range=[-.53,1.12],scaleanchor='x',scaleratio=1,fixedrange=True),showlegend=False,dragmode=False,transition_duration=0)
    return fig


def spending_speed(rows,budgets,month):
    state=spending_pace(rows,budgets,month)
    with st.container(key='spending_speed_panel'):
        title,status=st.columns([2,1],vertical_alignment='center')
        title.subheader('Spending speed')
        status.caption(state['status'])
        if state['budget'] is None:
            caption('Set an All spending budget for '+month+' to see your spending pace.')
            st.button('Set monthly budget',icon=':material/target:',key='pace_set_budget',on_click=lambda:st.session_state.update(budget_open=True))
            return
        st.plotly_chart(speedometer_figure(state,st.session_state.get('theme')=='Light'),width='stretch',config={'displayModeBar':False},key='spending_speed_chart')
        a,b,c=st.columns(3)
        a.metric('Spent',money(state['spent']))
        b.metric('Over budget' if state['remaining']<0 else 'Remaining',money(abs(state['remaining'])))
        c.metric('Monthly limit',money(state['budget']))
        if state['difference'] is not None:
            difference=state['difference']
            message=('On the expected spending pace.' if abs(difference)<.05 else f"Spending is {abs(difference):.1f} percentage points {'ahead of' if difference>0 else 'below'} the calendar pace.")
            caption(message+f" Day {state['elapsed']} of {state['days']}; expected use {state['expected']:.1f}%.")
        else:
            caption('The selected month has not started.' if state['expected']==0 else 'Completed month: comparing total spending with the full monthly budget.')
        caption('Needle: budget used. Thin marker: calendar pace. This is a simple even-spending comparison, not financial advice; bills may be paid early in the month.')
        if state['used']>100: caption('The needle stops at 100%; the percentage and over-budget amount retain the full actual value.')
