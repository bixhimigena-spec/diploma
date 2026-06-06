import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import sys
import os

# --------------------------------------------------
# Load analytics module (custom project structure)
# --------------------------------------------------
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(base_dir, ".."))

from app.analytics import get_rfm_data

# --------------------------------------------------
# Load data safely
# --------------------------------------------------
try:
    df = get_rfm_data()
except Exception as err:
    print("Error loading RFM data:", err)
    df = pd.DataFrame(columns=[
        'customer_id', 'recency', 'frequency', 'monetary',
        'segment_name', 'company_name', 'city', 'industry'
    ])

# --------------------------------------------------
# Initialize Dash app
# --------------------------------------------------
app = dash.Dash(__name__)
app.title = "CRM Analytics Dashboard"

# --------------------------------------------------
# Dropdown options
# --------------------------------------------------
def build_options(series):
    return [{'label': val, 'value': val} for val in sorted(series.dropna().unique())]

segment_options = build_options(df['segment_name'])
city_options = build_options(df['city'])
industry_options = build_options(df['industry'])

# --------------------------------------------------
# Layout
# --------------------------------------------------
app.layout = html.Div(
    style={
        'fontFamily': 'Segoe UI, sans-serif',
        'backgroundColor': '#F8F9FA',
        'padding': '20px'
    },
    children=[

        # Header
        html.Div([
            html.H2("CRM Analytics Dashboard"),
            html.P("Customer Segmentation using RFM & K-Means")
        ], style={'marginBottom': '20px'}),

        # Filters
        html.Div([
            dcc.Dropdown(id='seg-filter', options=segment_options, placeholder="Segment"),
            dcc.Dropdown(id='city-filter', options=city_options, placeholder="City"),
            dcc.Dropdown(id='industry-filter', options=industry_options, placeholder="Industry"),
            html.Button("Reset", id='reset-btn', n_clicks=0)
        ], style={'display': 'flex', 'gap': '10px', 'marginBottom': '20px'}),

        # KPIs
        html.Div([
            html.Div([html.H4("Customers"), html.H2(id='kpi-customers')]),
            html.Div([html.H4("Avg Monetary"), html.H2(id='kpi-monetary')]),
            html.Div([html.H4("Avg Frequency"), html.H2(id='kpi-frequency')]),
        ], style={'display': 'flex', 'justifyContent': 'space-between'}),

        # Charts
        html.Div([
            dcc.Graph(id='pie-chart'),
            dcc.Graph(id='bar-chart')
        ], style={'display': 'flex'}),

        dcc.Graph(id='scatter-3d'),

        # Table
        dash_table.DataTable(
            id='table',
            page_size=10,
            filter_action="native",
            sort_action="native",
            columns=[{"name": col, "id": col} for col in df.columns]
        )
    ]
)

# --------------------------------------------------
# Reset filters
# --------------------------------------------------
@app.callback(
    [Output('seg-filter', 'value'),
     Output('city-filter', 'value'),
     Output('industry-filter', 'value')],
    Input('reset-btn', 'n_clicks')
)
def reset_filters(n):
    if n and n > 0:
        return None, None, None
    return dash.no_update, dash.no_update, dash.no_update

# --------------------------------------------------
# Update dashboard
# --------------------------------------------------
@app.callback(
    [
        Output('kpi-customers', 'children'),
        Output('kpi-monetary', 'children'),
        Output('kpi-frequency', 'children'),
        Output('pie-chart', 'figure'),
        Output('bar-chart', 'figure'),
        Output('scatter-3d', 'figure'),
        Output('table', 'data')
    ],
    [
        Input('seg-filter', 'value'),
        Input('city-filter', 'value'),
        Input('industry-filter', 'value')
    ]
)
def update_dashboard(seg, city, industry):
    dff = df.copy()

    # Apply filters
    if seg:
        dff = dff[dff['segment_name'] == seg]
    if city:
        dff = dff[dff['city'] == city]
    if industry:
        dff = dff[dff['industry'] == industry]

    # KPIs
    total = len(dff)
    avg_monetary = f"{dff['monetary'].mean():.2f}" if total else "0"
    avg_frequency = f"{dff['frequency'].mean():.1f}" if total else "0"

    # Pie chart
    pie_fig = px.pie(dff, names='segment_name', hole=0.3)

    # Bar chart
    revenue = dff.groupby('segment_name')['monetary'].sum().reset_index()
    bar_fig = px.bar(revenue, x='segment_name', y='monetary')

    # 3D scatter
    scatter_fig = px.scatter_3d(
        dff,
        x='recency',
        y='frequency',
        z='monetary',
        color='segment_name',
        hover_name='company_name'
    )

    return (
        str(total),
        avg_monetary,
        avg_frequency,
        pie_fig,
        bar_fig,
        scatter_fig,
        dff.to_dict('records')
    )


if __name__ == "__main__":
    app.run(debug=True)
