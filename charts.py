# charts.py
import altair as alt
import pandas as pd
from datetime import datetime


def plot_12week_line(logs_df: pd.DataFrame, goals: dict):
    df = logs_df.copy()
    df['date'] = pd.to_datetime(df['timestamp'])
    df['week'] = df['date'].dt.to_period('W').apply(lambda r: r.start_time)
    weekly = df.groupby(['week', 'activity'])['value'].sum().reset_index()
    recent = weekly[weekly['week'] >= (pd.Timestamp.now() - pd.Timedelta(weeks=12))]
    chart = alt.Chart(recent).mark_line(point=True).encode(
        x=alt.X('week:T', title='Week'),
        y=alt.Y('value:Q', title='Total', scale=alt.Scale(zero=True)),
        color=alt.Color('activity:N', title='Activity'),
        tooltip=['week:T','activity','value']
    ).properties(width=700, height=400, title='Last 12 Weeks Activity')
    return chart


def plot_calendar_heatmap(logs_df: pd.DataFrame):
    df = logs_df.copy()
    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    df['week'] = df['date'].apply(lambda d: d.isocalendar()[1])
    df['weekday'] = pd.to_datetime(df['date']).dt.day_name().str[:3]
    counts = df.groupby(['week','weekday']).size().reset_index(name='count')
    weekday_order = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
    chart = alt.Chart(counts).mark_rect().encode(
        x=alt.X('weekday:N', sort=weekday_order, title='Day of Week'),
        y=alt.Y('week:O', title='Week Number'),
        color=alt.Color('count:Q', title='Logs'),
        tooltip=['week','weekday','count']
    ).properties(width=300, height=300, title='Activity Heatmap')
    return chart
