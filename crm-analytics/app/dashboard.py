import dash
from dash import dcc, html, dash_table
import plotly.express as px
import pandas as pd
import sys
import os

# Konfigurimi i rrugëve që Python të importojë saktë modulin analitik
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.analytics import get_rfm_data

# 1. Ngarkojmë të dhënat e analizuara nga K-Means & RFM
try:
    df = get_rfm_data()
except Exception as e:
    print(f"Gabim gjatë ekzekutimit të analizës: {e}")
    df = pd.DataFrame(columns=['customer_id', 'recency', 'frequency', 'monetary', 'segment_name', 'company_name', 'city', 'industry'])

# Inicializojmë aplikacionin Dash
app = dash.Dash(__name__, title="CRM Analytics Dashboard - TBU")

# 2. Llogaritjet për Panel 1 (Global KPI Summary)
total_kliente = len(df)
vlera_mesatare_blerje = df['monetary'].mean() if 'monetary' in df.columns else 0
frekuenca_mesatare = df['frequency'].mean() if 'frequency' in df.columns else 0

# 3. Grafikët për Panel 2 & 3
# Grafiku Pie: Shpërndarja e kompanive shqiptare në segmente
fig_pie = px.pie(
    df, 
    names='segment_name', 
    title="Shpërndarja e Klientëve SME Shqiptare sipas Segmenteve",
    hole=0.4,
    color_discrete_sequence=px.colors.qualitative.Pastel
)
fig_pie.update_layout(title_x=0.5, font=dict(family="Segoe UI", size=14))

# Grafiku Bar: Të ardhurat totale për çdo segment të llogaritur
df_revenue = df.groupby('segment_name')['monetary'].sum().reset_index()
fig_bar = px.bar(
    df_revenue,
    x='segment_name',
    y='monetary',
    title="Të Ardhurat Totale (Lekë) për çdo Segment RFM",
    labels={'monetary': 'Totali i Shpenzimeve (Lekë)', 'segment_name': 'Segmenti'},
    color='segment_name',
    color_discrete_sequence=px.colors.qualitative.Safe
)
fig_bar.update_layout(title_x=0.5, showlegend=False, font=dict(family="Segoe UI", size=14))

# 4. Ndërtimi i pamjes vizuale (Stilimi i faqes me CSS inline)
app.layout = html.Div(style={'fontFamily': 'Segoe UI, Arial, sans-serif', 'backgroundColor': '#f3f4f6', 'padding': '30px'}, children=[
    
    # Banner-i Kryesor (Header)
    html.Div(style={'backgroundColor': '#1e3a8a', 'color': 'white', 'padding': '25px', 'borderRadius': '12px', 'marginBottom': '30px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}, children=[
        html.H1("DASHBOARD ANALITIK I INTEGRUAR CRM", style={'margin': '0', 'fontSize': '30px', 'fontWeight': 'bold', 'textAlign': 'center'}),
        html.P("Segmentimi Automatik i Klientëve (Modeli RFM & Algoritmi Inteligjent K-Means) — Punim Diplome Master", style={'margin': '8px 0 0 0', 'textAlign': 'center', 'opacity': '0.9', 'fontSize': '16px'})
    ]),
    
    # PANEL 1: Kartat Përmbledhëse të KPI-ve (Global Summary)
    html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '30px', 'gap': '20px'}, children=[
        html.Div(style={'flex': '1', 'backgroundColor': 'white', 'padding': '25px', 'borderRadius': '12px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.05)', 'textAlign': 'center', 'borderLeft': '6px solid #2563eb'}, children=[
            html.H3("Totali i Klientëve SME", style={'margin': '0', 'color': '#4b5563', 'fontSize': '16px', 'textTransform': 'uppercase'}),
            html.H2(f"{total_kliente}", style={'margin': '12px 0 0 0', 'color': '#111827', 'fontSize': '36px', 'fontWeight': 'bold'})
        ]),
        html.Div(style={'flex': '1', 'backgroundColor': 'white', 'padding': '25px', 'borderRadius': '12px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.05)', 'textAlign': 'center', 'borderLeft': '6px solid #10b981'}, children=[
            html.H3("Vlera Vjetore Mesatare (Monetary)", style={'margin': '0', 'color': '#4b5563', 'fontSize': '16px', 'textTransform': 'uppercase'}),
            html.H2(f"{vlera_mesatare_blerje:,.2f} ALL", style={'margin': '12px 0 0 0', 'color': '#111827', 'fontSize': '30px', 'fontWeight': 'bold'})
        ]),
        html.Div(style={'flex': '1', 'backgroundColor': 'white', 'padding': '25px', 'borderRadius': '12px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.05)', 'textAlign': 'center', 'borderLeft': '6px solid #f59e0b'}, children=[
            html.H3("Frekuenca Mesatare e Blerjeve (F)", style={'margin': '0', 'color': '#4b5563', 'fontSize': '16px', 'textTransform': 'uppercase'}),
            html.H2(f"{frekuenca_mesatare:.1f} herë / vit", style={'margin': '12px 0 0 0', 'color': '#111827', 'fontSize': '30px', 'fontWeight': 'bold'})
        ]),
    ]),
    
    # PANEL 2 & 3: Grafikët Vizualë (Shpërndarja dhe të Ardhurat)
    html.Div(style={'display': 'flex', 'gap': '25px', 'marginBottom': '30px'}, children=[
        html.Div(style={'flex': '1', 'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '12px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.05)'}, children=[
            dcc.Graph(figure=fig_pie)
        ]),
        html.Div(style={'flex': '1', 'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '12px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.05)'}, children=[
            dcc.Graph(figure=fig_bar)
        ]),
    ]),
    
    # PANEL 4: Drill-Down Details (Tabela interaktive me filtrim)
    html.Div(style={'backgroundColor': 'white', 'padding': '25px', 'borderRadius': '12px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.05)'}, children=[
        html.H3("Panel i Detajuar: Lista e Bizneseve dhe Segmentet e Caktuara", style={'marginTop': '0', 'marginBottom': '20px', 'color': '#1f2937', 'fontSize': '18px'}),
        dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[
                {"name": "ID Klienti", "id": "customer_id"},
                {"name": "Kompania", "id": "company_name"},
                {"name": "Qyteti", "id": "city"},
                {"name": "Industria", "id": "industry"},
                {"name": "Recency (Ditë)", "id": "recency"},
                {"name": "Frequency (Blerje)", "id": "frequency"},
                {"name": "Monetary (Lekë)", "id": "monetary"},
                {"name": "Segmenti RFM", "id": "segment_name"}
            ],
            page_size=10,
            filter_action="native",  # Lejon filtrimin interaktiv nga përdoruesi
            sort_action="native",    # Lejon renditjen sipas kolonave
            style_table={'overflowX': 'auto'},
            style_header={'backgroundColor': '#f9fafb', 'fontWeight': 'bold', 'color': '#374151', 'border': '1px solid #e5e7eb', 'padding': '12px'},
            style_cell={'padding': '12px', 'textAlign': 'left', 'border': '1px solid #e5e7eb', 'fontSize': '14px', 'color': '#4b5563'},
            style_data_conditional=[
                {
                    'if': {'column_id': 'segment_name', 'filter_query': '{segment_name} contains "VIP"'},
                    'backgroundColor': '#d1fae5', 'color': '#065f46', 'fontWeight': 'bold'
                },
                {
                    'if': {'column_id': 'segment_name', 'filter_query': '{segment_name} contains "Rrezik"'},
                    'backgroundColor': '#fee2e2', 'color': '#991b1b', 'fontWeight': 'bold'
                }
            ]
        )
    ])
])

if __name__ == '__main__':
    app.run(debug=True, port=8050)