import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
# ---------- LOAD DATA ----------
strikes = pd.read_csv(
    r"C:\Users\Candis\Documents\candis\ANTL 5100\Strike_Reports.csv",
    encoding='latin1',
    low_memory=False
)
airports = pd.read_csv(r"C:\Users\Candis\Documents\candis\ANTL 5100\Airports_USA.csv")

strikes.columns = strikes.columns.str.upper().str.strip()
airports.columns = airports.columns.str.upper().str.strip()
# ---------- Merge Data ----------
merged = strikes.merge(
    airports,
    left_on="AIRPORT_ID",
    right_on="IDENT",
    how="left"
)
# ---------- FALLBACK ----------
missing = merged[merged["LATITUDE_DEG"].isna()]

if not missing.empty:
    fallback = missing.merge(
        airports,
        left_on="AIRPORT",
        right_on="IATA_CODE",
        how="left",
        suffixes=("", "_FB")
    )

    for col in ["LATITUDE_DEG", "LONGITUDE_DEG"]:
        merged.loc[merged[col].isna(), col] = fallback[col + "_FB"].values
# ---------- ENSURE NUMERIC COORDINATES ----------
merged["LATITUDE_DEG"] = pd.to_numeric(merged["LATITUDE_DEG"], errors="coerce")
merged["LONGITUDE_DEG"] = pd.to_numeric(merged["LONGITUDE_DEG"], errors="coerce")
# ---------- AGGREGATE ----------
airport_summary = (
    merged.groupby(["AIRPORT_ID", "AIRPORT", "LATITUDE_DEG", "LONGITUDE_DEG"])
    .agg(
        TOTAL_STRIKES=("INDEX_NR", "count"),
        DAMAGE_STRIKES=("INDICATED_DAMAGE", lambda x: sum(x == "Y")),
        ENGINE_STRIKES=("STR_ENG1", "sum"),
        AVG_COST=("COST_REPAIRS", "mean"),
    )
    .reset_index()
)
# ---------- CUSTOM METRIC ----------
airport_summary["RISK_SCORE"] = (
    airport_summary["TOTAL_STRIKES"]
    + 2 * airport_summary["DAMAGE_STRIKES"]
    + 3 * airport_summary["ENGINE_STRIKES"]
    + 0.0001 * airport_summary["AVG_COST"].fillna(0)
)
# ---------- GEOGRAPHIC MAP ----------
fig = px.scatter_geo(
    airport_summary,
    lat="LATITUDE_DEG",
    lon="LONGITUDE_DEG",
    size="TOTAL_STRIKES",
    color="RISK_SCORE",
    hover_name="AIRPORT",
    hover_data=["AIRPORT_ID", "TOTAL_STRIKES", "RISK_SCORE"],
    color_continuous_scale="Reds",
    scope="usa",
    title="FAA Airport Bird Strike Risk Score (Custom Metric)"
)
fig.show()
# ---------- STATE MAP ----------
state_summary = merged.groupby("STATE").size().reset_index(name="TOTAL_STRIKES")

fig = px.choropleth(
    state_summary,
    locations="STATE",
    locationmode="USA-states",
    color="TOTAL_STRIKES",
    color_continuous_scale="OrRd",
    scope="usa",
    title="Bird Strikes by U.S. State"
)
fig.show()
# ---------- TIME SERIES ----------
merged["INCIDENT_DATE"] = pd.to_datetime(merged["INCIDENT_DATE"])

yearly = merged.groupby("INCIDENT_YEAR").size()
yearly.plot(kind="line", figsize=(10,5), title="Yearly Bird Strikes")

monthly = merged.groupby("INCIDENT_MONTH").size().reset_index(name="COUNT")
px.line(monthly, x="INCIDENT_MONTH", y="COUNT",
        title="Seasonality of Bird Strikes (Monthly)").show()

merged["WEEKDAY"] = merged["INCIDENT_DATE"].dt.day_name()
weekday = merged.groupby("WEEKDAY").size().reset_index(name="COUNT")
px.bar(weekday, x="WEEKDAY", y="COUNT",
       title="Weekly Bird Strike Pattern").show()
# ---------- FILTERED TIME SERIES ----------
fig = go.Figure()

airports_list = merged["AIRPORT_ID"].unique()
traces = []

for airport in airports_list:
    subset = merged[merged["AIRPORT_ID"] == airport]
    fig.add_trace(go.Scatter(
        x=subset["INCIDENT_DATE"],
        y=subset["INDEX_NR"],
        name=airport,
        visible=False
    ))
fig.data[0].visible = True

fig.update_layout(
    title="Bird Strikes per Airport Over Time",
    updatemenus=[
        {
            "buttons": [
                {
                    "label": a,
                    "method": "update",
                    "args": [
                        {"visible": [airport == a for airport in airports_list]},
                        {"title": f"Bird Strikes at {a}"}
                    ]
                }
                for a in airports_list
            ]
        }
    ]
)

fig.show()