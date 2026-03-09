import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from dash import Dash, dcc, html, Input, Output

# =======================
# DATA LOADING / PREP
# =======================

# flights.csv must be in the same folder
# columns: date, airline, from_airport, to_airport, distance_km,
#          duration_hr, delay_min, trip_type, dep_time_local, aircraft

flights = pd.read_csv("flights.csv", parse_dates=["date"])

# airports.csv must be in the same folder
# columns: airport, lat, lon, city, country
airports = pd.read_csv("airports.csv")

# Add missing columns if user omitted any
if "delay_min" not in flights.columns:
    flights["delay_min"] = 0

if "dep_time_local" not in flights.columns:
    flights["dep_time_local"] = "12:00"

if "aircraft" not in flights.columns:
    flights["aircraft"] = "Unknown"

# Join coordinates for origin and destination
flights = flights.merge(
    airports[["airport", "lat", "lon"]],
    left_on="from_airport",
    right_on="airport",
    how="left",
).rename(columns={"lat": "from_lat", "lon": "from_lon"}).drop(columns=["airport"])

flights = flights.merge(
    airports[["airport", "lat", "lon"]],
    left_on="to_airport",
    right_on="airport",
    how="left",
).rename(columns={"lat": "to_lat", "lon": "to_lon"}).drop(columns=["airport"])

# Basic derived fields
flights["year"] = flights["date"].dt.year
flights["month"] = flights["date"].dt.to_period("M").astype(str)

# Parse departure time into decimal hour for polar plot
def time_to_hour(t):
    try:
        h, m = str(t).split(":")
        return int(h) + int(m) / 60.0
    except Exception:
        return np.nan

flights["dep_hour"] = flights["dep_time_local"].apply(time_to_hour)

# =======================
# APP SETUP
# =======================

app = Dash(__name__)
app.title = "Personal Flight Dashboard"

years = sorted(flights["year"].dropna().unique())
airlines = sorted(flights["airline"].dropna().unique())
trip_types = sorted(flights["trip_type"].dropna().unique())

app = Dash(__name__)
app.title = "Personal Flight Dashboard"

years = sorted(flights["year"].dropna().unique())
airlines = sorted(flights["airline"].dropna().unique())
trip_types = sorted(flights["trip_type"].dropna().unique())

app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap" rel="stylesheet">
        <style>
            body {
                margin: 0;
                font-family: 'Space Grotesk', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""

app.layout = html.Div(
    style={"backgroundColor": "#020617", "color": "#e5e7eb", "minHeight": "100vh"},
    children=[
        # TOP BAR WITH PROFILE
        html.Div(
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "padding": "1.2rem 2rem 1rem 2rem",
                "background": "linear-gradient(135deg, #020617 0%, #0f172a 40%, #0369a1 100%)",
                "borderBottom": "1px solid #1f2937",
            },
            children=[
                html.Div(
                    children=[
                        html.Div(
                            "Flight Log",
                            style={
                                "fontSize": "0.8rem",
                                "letterSpacing": "0.18em",
                                "textTransform": "uppercase",
                                "color": "#9ca3af",
                                "marginBottom": "0.1rem",
                            },
                        ),
                        html.Div(
                            "My Personal Flight Cockpit",
                            style={
                                "fontSize": "1.9rem",
                                "fontWeight": "700",
                                "letterSpacing": "0.03em",
                            },
                        ),
                        html.Div(
                            "Visualizing routes, hours, and stories from my own sky time.",
                            style={
                                "fontSize": "0.9rem",
                                "color": "#cbd5f5",
                                "marginTop": "0.25rem",
                            },
                        ),
                    ]
                ),
                # PROFILE CARD
                html.Div(
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "gap": "0.75rem",
                        "backgroundColor": "rgba(15,23,42,0.85)",
                        "padding": "0.6rem 0.9rem",
                        "borderRadius": "999px",
                        "backdropFilter": "blur(8px)",
                        "border": "1px solid rgba(148,163,184,0.45)",
                    },
                    children=[
                        # Replace src with your own image path or URL
                        html.Img(
                            src="https://images.pexels.com/photos/912050/pexels-photo-912050.jpeg?auto=compress&cs=tinysrgb&w=80",
                            style={
                                "width": "40px",
                                "height": "40px",
                                "borderRadius": "50%",
                                "objectFit": "cover",
                                "border": "2px solid #38bdf8",
                            },
                        ),
                        html.Div(
                            children=[
                                html.Div(
                                    "Pallavi Kochar",
                                    style={
                                        "fontSize": "0.95rem",
                                        "fontWeight": "600",
                                    },
                                ),
                                html.Div(
                                    "Finance • Traveler • Dancer",
                                    style={
                                        "fontSize": "0.8rem",
                                        "color": "#9ca3af",
                                    },
                                ),
                            ]
                        ),
                    ],
                ),
            ],
        ),

        # FILTERS + TABS BELOW
        html.Div(
            style={"padding": "0.75rem 2rem 0 2rem"},
            children=[
                html.Div(
                    style={
                        "display": "flex",
                        "gap": "1rem",
                        "flexWrap": "wrap",
                        "justifyContent": "center",
                        "marginBottom": "0.75rem",
                        "marginTop": "0.5rem",
                    },
                    children=[
                        html.Div(
                            [
                                html.Label("Year", style={"fontWeight": "600"}),
                                dcc.Dropdown(
                                    options=[{"label": "All", "value": "ALL"}]
                                    + [{"label": str(y), "value": y} for y in years],
                                    value="ALL",
                                    clearable=False,
                                    id="year-filter",
                                    style={"width": "10rem", "color": "#000"},
                                ),
                            ]
                        ),
                        html.Div(
                            [
                                html.Label("Airline", style={"fontWeight": "600"}),
                                dcc.Dropdown(
                                    options=[{"label": "All", "value": "ALL"}]
                                    + [{"label": a, "value": a} for a in airlines],
                                    value="ALL",
                                    clearable=False,
                                    id="airline-filter",
                                    style={"width": "12rem", "color": "#000"},
                                ),
                            ]
                        ),
                        html.Div(
                            [
                                html.Label("Trip type", style={"fontWeight": "600"}),
                                dcc.Dropdown(
                                    options=[{"label": "All", "value": "ALL"}]
                                    + [{"label": t, "value": t} for t in trip_types],
                                    value="ALL",
                                    clearable=False,
                                    id="trip-filter",
                                    style={"width": "12rem", "color": "#000"},
                                ),
                            ]
                        ),
                    ],
                ),
                dcc.Tabs(
                    id="tabs",
                    value="overview",
                    colors={
                        "border": "#111827",
                        "primary": "#0ea5e9",
                        "background": "#020617",
                    },
                    children=[
                        dcc.Tab(
                            label="Overview",
                            value="overview",
                            style={"backgroundColor": "#020617", "color": "#9ca3af"},
                            selected_style={
                                "backgroundColor": "#0f172a",
                                "color": "#e5e7eb",
                            },
                        ),
                        dcc.Tab(
                            label="Routes & Map",
                            value="routes",
                            style={"backgroundColor": "#020617", "color": "#9ca3af"},
                            selected_style={
                                "backgroundColor": "#0f172a",
                                "color": "#e5e7eb",
                            },
                        ),
                        dcc.Tab(
                            label="Delays & Reliability",
                            value="delays",
                            style={"backgroundColor": "#020617", "color": "#9ca3af"},
                            selected_style={
                                "backgroundColor": "#0f172a",
                                "color": "#e5e7eb",
                            },
                        ),
                        dcc.Tab(
                            label="Patterns & Trip Types",
                            value="patterns",
                            style={"backgroundColor": "#020617", "color": "#9ca3af"},
                            selected_style={
                                "backgroundColor": "#0f172a",
                                "color": "#e5e7eb",
                            },
                        ),
                    ],
                ),
            ],
        ),

        html.Div(id="tab-content", style={"padding": "1rem 1.5rem 2rem 2rem"}),
    ],
)

# =======================
# FILTER HELPER
# =======================

def apply_filters(df, year, airline, trip_type):
    out = df.copy()
    if year != "ALL":
        out = out[out["year"] == int(year)]
    if airline != "ALL":
        out = out[out["airline"] == airline]
    if trip_type != "ALL":
        out = out[out["trip_type"] == trip_type]
    return out

# =======================
# FIGURE BUILDERS
# =======================

def kpi_card(title, value):
    return html.Div(
        style={
            "backgroundColor": "#0f172a",
            "padding": "0.75rem 1rem",
            "borderRadius": "0.5rem",
            "minWidth": "160px",
        },
        children=[
            html.Div(title, style={"fontSize": "0.8rem", "color": "#9ca3af"}),
            html.Div(value, style={"fontSize": "1.4rem", "fontWeight": "700"}),
        ],
    )

def overview_layout(df):
    total_flights = len(df)
    total_distance = df["distance_km"].sum()
    total_hours = df["duration_hr"].sum()
    airports_used = (
        pd.unique(df[["from_airport", "to_airport"]].values.ravel("K"))
        if not df.empty
        else []
    )
    unique_airports = len(airports_used)

    by_month = (
        df.groupby("month")["distance_km"]
        .sum()
        .reset_index()
        .sort_values("month")
    )
    fig_distance = px.area(
        by_month,
        x="month",
        y="distance_km",
        title="Distance flown over time",
    )
    fig_distance.update_layout(
        template="plotly_dark",
        paper_bgcolor="#020617",
        plot_bgcolor="#020617",
    )

    by_airline = (
        df.groupby("airline")["distance_km"]
        .sum()
        .reset_index()
        .sort_values("distance_km", ascending=False)
    )
    fig_airline = px.bar(
        by_airline,
        x="airline",
        y="distance_km",
        title="Distance by airline",
    )
    fig_airline.update_layout(
        template="plotly_dark",
        paper_bgcolor="#020617",
        plot_bgcolor="#020617",
    )

    cards = html.Div(
        style={
            "display": "flex",
            "gap": "1rem",
            "flexWrap": "wrap",
            "marginBottom": "1rem",
        },
        children=[
            kpi_card("Total flights", f"{total_flights}"),
            kpi_card("Total distance (km)", f"{int(total_distance):,}"),
            kpi_card("Hours in the air", f"{total_hours:.1f}"),
            kpi_card("Unique airports", f"{unique_airports}"),
        ],
    )

    graphs = html.Div(
        style={"display": "flex", "gap": "1rem", "flexWrap": "wrap"},
        children=[
            html.Div(style={"flex": "1 1 350px"}, children=[dcc.Graph(figure=fig_distance)]),
            html.Div(style={"flex": "1 1 350px"}, children=[dcc.Graph(figure=fig_airline)]),
        ],
    )

    return html.Div([cards, graphs])

def routes_layout(df):
    # group by route with coordinates
    routes = (
        df.groupby(["from_airport", "to_airport", "from_lat", "from_lon", "to_lat", "to_lon"])
        .size()
        .reset_index(name="flights")
    )

    lats = []
    lons = []

    for _, r in routes.iterrows():
        if pd.isna(r["from_lat"]) or pd.isna(r["to_lat"]):
            continue
        lats += [r["from_lat"], r["to_lat"], None]
        lons += [r["from_lon"], r["to_lon"], None]

    fig_routes = go.Figure()
    fig_routes.add_trace(
        go.Scattergeo(
            lon=lons,
            lat=lats,
            mode="lines",
            line=dict(width=2, color="#0ea5e9"),
            opacity=0.9,
        )
    )

    # airport points
    airport_points = pd.concat(
        [
            df[["from_airport", "from_lat", "from_lon"]]
            .rename(columns={"from_airport": "airport", "from_lat": "lat", "from_lon": "lon"}),
            df[["to_airport", "to_lat", "to_lon"]]
            .rename(columns={"to_airport": "airport", "to_lat": "lat", "to_lon": "lon"}),
        ]
    ).drop_duplicates(subset=["airport"])

    fig_routes.add_trace(
        go.Scattergeo(
            lon=airport_points["lon"],
            lat=airport_points["lat"],
            mode="markers+text",
            text=airport_points["airport"],
            textposition="top center",
            marker=dict(size=6, color="#f97316"),
            name="Airports",
        )
    )

    fig_routes.update_layout(
        title="Route network",
        template="plotly_dark",
        paper_bgcolor="#020617",
        geo=dict(
            projection_type="natural earth",
            showland=True,
            landcolor="#111827",
            showcountries=True,
            countrycolor="#4b5563",
        ),
    )

    # top routes bar
    top_pairs = (
        df.groupby(["from_airport", "to_airport"])
        .size()
        .reset_index(name="flights")
        .sort_values("flights", ascending=False)
        .head(10)
    )
    fig_pairs = px.bar(
        top_pairs,
        x="flights",
        y=top_pairs["from_airport"] + " → " + top_pairs["to_airport"],
        orientation="h",
        title="Top routes",
    )
    fig_pairs.update_layout(
        template="plotly_dark",
        paper_bgcolor="#020617",
        plot_bgcolor="#020617",
        yaxis_title="Route",
        xaxis_title="Flights",
    )

    return html.Div(
        style={"display": "flex", "gap": "1rem", "flexWrap": "wrap"},
        children=[
            html.Div(style={"flex": "2 1 400px"}, children=[dcc.Graph(figure=fig_routes)]),
            html.Div(style={"flex": "1 1 300px"}, children=[dcc.Graph(figure=fig_pairs)]),
        ],
    )

def delays_layout(df):
    by_airline = (
        df.groupby("airline")["delay_min"]
        .mean()
        .reset_index()
        .sort_values("delay_min", ascending=False)
    )
    fig_airline_delay = px.bar(
        by_airline,
        x="airline",
        y="delay_min",
        title="Average delay by airline (minutes)",
        color="delay_min",
    )
    fig_airline_delay.update_layout(
        template="plotly_dark",
        paper_bgcolor="#020617",
        plot_bgcolor="#020617",
    )

    df_hm = df.dropna(subset=["dep_hour"]).copy()
    df_hm["hour_bucket"] = (df_hm["dep_hour"] // 3 * 3).astype(int)
    delay_matrix = (
        df_hm.groupby(["month", "hour_bucket"])["delay_min"]
        .mean()
        .reset_index()
    )
    fig_heat = px.density_heatmap(
        delay_matrix,
        x="hour_bucket",
        y="month",
        z="delay_min",
        nbinsx=8,
        color_continuous_scale="Inferno",
        title="Delay heatmap (time of day vs month)",
    )
    fig_heat.update_layout(
        template="plotly_dark",
        paper_bgcolor="#020617",
        plot_bgcolor="#020617",
        xaxis_title="Departure hour (bucketed)",
    )

    on_time_pct = (df["delay_min"] <= 15).mean() * 100 if len(df) > 0 else 0
    worst_delay = df["delay_min"].max() if len(df) > 0 else 0
    avg_delay = df["delay_min"].mean() if len(df) > 0 else 0

    cards = html.Div(
        style={
            "display": "flex",
            "gap": "1rem",
            "flexWrap": "wrap",
            "marginBottom": "1rem",
        },
        children=[
            kpi_card("On-time flights (≤15 min)", f"{on_time_pct:.1f}%"),
            kpi_card("Average delay (min)", f"{avg_delay:.1f}"),
            kpi_card("Worst delay (min)", f"{worst_delay:.0f}"),
        ],
    )

    graphs = html.Div(
        style={"display": "flex", "gap": "1rem", "flexWrap": "wrap"},
        children=[
            html.Div(style={"flex": "1 1 350px"}, children=[dcc.Graph(figure=fig_airline_delay)]),
            html.Div(style={"flex": "1 1 350px"}, children=[dcc.Graph(figure=fig_heat)]),
        ],
    )

    return html.Div([cards, graphs])

def patterns_layout(df):
    by_trip = (
        df.groupby("trip_type")
        .size()
        .reset_index(name="flights")
        .sort_values("flights", ascending=False)
    )
    fig_trip = px.pie(
        by_trip,
        names="trip_type",
        values="flights",
        hole=0.5,
        title="Trip type share",
    )
    fig_trip.update_layout(
        template="plotly_dark",
        paper_bgcolor="#020617",
        plot_bgcolor="#020617",
    )

    polar_df = df.dropna(subset=["dep_hour"]).copy()
    polar_df["angle"] = polar_df["dep_hour"] * 15
    fig_polar = go.Figure(
        data=go.Barpolar(
            r=polar_df["distance_km"],
            theta=polar_df["angle"],
            marker=dict(color=polar_df["dep_hour"], colorscale="Ice"),
            opacity=0.8,
        )
    )
    fig_polar.update_layout(
        title="Distance vs time of day (polar)",
        template="plotly_dark",
        paper_bgcolor="#020617",
        polar=dict(
            radialaxis=dict(showticklabels=True, ticks=""),
            angularaxis=dict(direction="clockwise", rotation=90),
        ),
    )

    metrics = (
        df.groupby("airline")
        .agg(
            avg_delay=("delay_min", "mean"),
            distance=("distance_km", "sum"),
            flights=("airline", "size"),
        )
        .reset_index()
    )
    for col in ["avg_delay", "distance", "flights"]:
        if metrics[col].max() > metrics[col].min():
            metrics[col] = (metrics[col] - metrics[col].min()) / (
                metrics[col].max() - metrics[col].min()
            )
        else:
            metrics[col] = 0

    categories = ["avg_delay", "distance", "flights"]
    fig_radar = go.Figure()
    for _, row in metrics.iterrows():
        fig_radar.add_trace(
            go.Scatterpolar(
                r=[row[c] for c in categories] + [row[categories[0]]],
                theta=categories + [categories[0]],
                fill="toself",
                name=row["airline"],
            )
        )
    fig_radar.update_layout(
        title="Airline profile (normalized)",
        template="plotly_dark",
        paper_bgcolor="#020617",
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True,
    )

    return html.Div(
        style={"display": "flex", "gap": "1rem", "flexWrap": "wrap"},
        children=[
            html.Div(style={"flex": "1 1 300px"}, children=[dcc.Graph(figure=fig_trip)]),
            html.Div(style={"flex": "1 1 300px"}, children=[dcc.Graph(figure=fig_polar)]),
            html.Div(style={"flex": "1 1 350px"}, children=[dcc.Graph(figure=fig_radar)]),
        ],
    )

# =======================
# CALLBACK
# =======================

@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "value"),
    Input("year-filter", "value"),
    Input("airline-filter", "value"),
    Input("trip-filter", "value"),
)
def render_tab(tab, year, airline, trip_type):
    df = apply_filters(flights, year, airline, trip_type)

    if tab == "overview":
        return overview_layout(df)
    elif tab == "routes":
        return routes_layout(df)
    elif tab == "delays":
        return delays_layout(df)
    elif tab == "patterns":
        return patterns_layout(df)
    return html.Div("Unknown tab")

if __name__ == "__main__":
    app.run(debug=True, port=8050)
