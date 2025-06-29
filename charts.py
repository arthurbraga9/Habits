# charts.py
import altair as alt
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Union
from PIL import Image, UnidentifiedImageError
import matplotlib.pyplot as plt


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

def create_pie_chart(images_path: Union[str, Path], results_path: Union[str, Path]) -> Path:
    """Create a pie chart of image counts per subfolder.

    Any files that cannot be opened as images are skipped rather than raising an
    exception. The resulting chart is saved to ``results_path``.
    """
    images_dir = Path(images_path)
    output_path = Path(results_path)

    counts = {}
    for img_file in images_dir.rglob("*"):
        if img_file.is_dir():
            continue
        try:
            with Image.open(img_file):
                pass
        except (UnidentifiedImageError, OSError):
            # Skip unreadable files
            print(f"Skipping unreadable image: {img_file}")
            continue
        label = img_file.parent.name
        counts[label] = counts.get(label, 0) + 1

    if not counts:
        raise ValueError("No valid images found in provided directory")

    labels = list(counts.keys())
    values = [counts[l] for l in labels]

    plt.figure(figsize=(6, 6))
    plt.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
    plt.axis("equal")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close()
    return output_path
