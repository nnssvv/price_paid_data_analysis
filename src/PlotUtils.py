import plotly.graph_objects as go
import pandas as pd

def plot_transaction_volume_with_annotations(df):
    """
    Plots monthly transaction volume and 3-month moving average
    with shaded event windows. Visual aesthetics are unchanged.
    """

    # Ensure datetime format
    df['transfer_date'] = pd.to_datetime(df['transfer_date'], errors='coerce')

    # Create month-year
    df['month_year'] = df['transfer_date'].dt.to_period('M').dt.to_timestamp()

    # Aggregate and calculate 3-month moving average
    monthly_counts = df.groupby('month_year').size().reset_index(name='transaction_count')
    monthly_counts['ma_3m'] = monthly_counts['transaction_count'].rolling(window=3).mean()

    # Build figure manually
    fig = go.Figure()

    # Blue line — Number of Transactions
    fig.add_trace(go.Scatter(
        x=monthly_counts['month_year'],
        y=monthly_counts['transaction_count'],
        mode='lines',
        name='Number of Transactions',
        line=dict(color='blue', width=1)
    ))

    # Red line — 3-month Moving Average
    fig.add_trace(go.Scatter(
        x=monthly_counts['month_year'],
        y=monthly_counts['ma_3m'],
        mode='lines',
        name='3-Month Moving Average',
        line=dict(color='red', width=1)
    ))

    # Define shaded windows
    shaded_periods = [
        {
            "label": "Stamp Duty Holiday",
            "start": "2020-07-08",
            "end": "2021-06-30",
            "color": "rgba(255, 0, 0, 0.05)",
            "xshift": 80
        },
        {
            "label": "COVID Lockdown",
            "start": "2020-03-23",
            "end": "2020-06-15",
            "color": "rgba(0, 0, 255, 0.05)",
            "xshift": 0
        }
    ]

    for period in shaded_periods:
        fig.add_vrect(
            x0=pd.to_datetime(period["start"]),
            x1=pd.to_datetime(period["end"]),
            fillcolor=period["color"],
            layer="below",
            line_width=0
        )
        fig.add_annotation(
            x=pd.to_datetime(period["start"]),
            y=0.95,
            yref='paper',
            text=period["label"],
            showarrow=False,
            font=dict(size=13, color="black"),
            align='left',
            xshift=period["xshift"],
            bgcolor="rgba(255,255,255,0.6)"
        )

    # Layout
    fig.update_layout(
        xaxis=dict(tickformat='%b %Y', showgrid=True, zeroline=False),
        yaxis=dict(showgrid=True, zeroline=False),
        paper_bgcolor='white',
        margin=dict(t=120),
        legend=dict(
            orientation='h',
            x=0.5,
            y=1.12,
            xanchor='center',
            yanchor='bottom',
            font=dict(size=16)
        )
    )

    fig.show()
    return fig
