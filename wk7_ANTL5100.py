import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
import os

# ---------- LOAD DATA ----------
airports = pd.read_csv("Airports_USA.csv", encoding='latin1', low_memory=False)
strikes = pd.read_csv("Strike_Reports_small.csv", encoding='latin1', low_memory=False)

# ---------- CLEAN COLUMN NAMES ----------
strikes.columns = strikes.columns.str.upper().str.strip()
airports.columns = airports.columns.str.upper().str.strip()

# ---------- MERGE DATA ----------
merged = strikes.merge(airports, left_on="AIRPORT_ID", right_on="IDENT", how="left")

# ---------- FALLBACK FOR MISSING COORDINATES ----------
missing = merged[merged["LATITUDE_DEG"].isna()]
if not missing.empty:
    fallback = missing.merge(airports, left_on="AIRPORT", right_on="IATA_CODE", how="left", suffixes=("", "_FB"))
    for col in ["LATITUDE_DEG", "LONGITUDE_DEG"]:
        merged.loc[merged[col].isna(), col] = fallback[col + "_FB"].values

# ---------- ENSURE NUMERIC COORDINATES ----------
merged["LATITUDE_DEG"] = pd.to_numeric(merged["LATITUDE_DEG"], errors="coerce")
merged["LONGITUDE_DEG"] = pd.to_numeric(merged["LONGITUDE_DEG"], errors="coerce")

# ---------- AGGREGATE DATA BY AIRPORT ----------
airport_summary = merged.groupby(["AIRPORT_ID", "AIRPORT", "LATITUDE_DEG", "LONGITUDE_DEG"]).agg(
    TOTAL_STRIKES=("INDEX_NR", "count"),
    DAMAGE_STRIKES=("INDICATED_DAMAGE", lambda x: sum(x == "Y")),
    ENGINE_STRIKES=("STR_ENG1", "sum"),
    AVG_COST=("COST_REPAIRS", "mean")
).reset_index()

# ---------- CUSTOM RISK SCORE ----------
airport_summary["RISK_SCORE"] = (
    airport_summary["TOTAL_STRIKES"] +
    2 * airport_summary["DAMAGE_STRIKES"] +
    3 * airport_summary["ENGINE_STRIKES"] +
    0.0001 * airport_summary["AVG_COST"].fillna(0)
)

# ---------- CONVERT DATES ----------
merged["INCIDENT_DATE"] = pd.to_datetime(merged["INCIDENT_DATE"], errors='coerce')

# ---------- DASH APP ----------
app = Dash(__name__)

app.layout = html.Div([
    html.H1("FAA Bird Strike Dashboard", style={'textAlign':'center'}),
    html.Label("Select Airport:"),
    dcc.Dropdown(
        id='airport-dropdown',
        options=[{'label': name, 'value': aid} for name, aid in zip(airport_summary['AIRPORT'], airport_summary['AIRPORT_ID'])],
        value=airport_summary['AIRPORT_ID'].iloc[0]
    ),
    dcc.Graph(id='airport-map'),
    dcc.Graph(id='time-series'),
    dcc.Graph(id='damage-bar')
])

# ---------- CALLBACKS ----------
@app.callback(
    [Output('airport-map', 'figure'),
     Output('time-series', 'figure'),
     Output('damage-bar', 'figure')],
    [Input('airport-dropdown', 'value')]
)
def update_dashboard(selected_airport):
    # ---------- MAP ----------
    map_fig = px.scatter_geo(
        airport_summary,
        lat="LATITUDE_DEG",
        lon="LONGITUDE_DEG",
        size="TOTAL_STRIKES",
        color="RISK_SCORE",
        hover_name="AIRPORT",
        hover_data=["AIRPORT_ID", "TOTAL_STRIKES", "RISK_SCORE"],
        color_continuous_scale="Reds",
        scope="usa",
        title="FAA Airport Bird Strike Risk Score"
    )

    # ---------- TIME SERIES ----------
    df_airport = merged[merged["AIRPORT_ID"] == selected_airport].dropna(subset=["INCIDENT_DATE"])
    time_fig = px.line(
        df_airport.groupby("INCIDENT_DATE").size().reset_index(name="COUNT"),
        x="INCIDENT_DATE",
        y="COUNT",
        title=f"Bird Strikes Over Time at {df_airport['AIRPORT'].iloc[0]}" if not df_airport.empty else "No Data"
    )

    # ---------- DAMAGE STRIKES BAR ----------
    df_airport["INCIDENT_YEAR"] = df_airport["INCIDENT_DATE"].dt.year
    damage_fig = px.bar(
        df_airport.groupby("INCIDENT_YEAR")["INDICATED_DAMAGE"].apply(lambda x: sum(x == "Y")).reset_index(name="DAMAGE_STRIKES"),
        x="INCIDENT_YEAR",
        y="DAMAGE_STRIKES",
        title=f"Damage Strikes per Year at {df_airport['AIRPORT'].iloc[0]}" if not df_airport.empty else "No Data"
    )

    return map_fig, time_fig, damage_fig
