"""Plotly figure builders. Each returns a JSON/HTML string embeddable in FastHTML."""

from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go

from .data import ZONES


PLOTLY_THEME = "plotly_white"


def _to_html(fig: go.Figure, div_id: str) -> str:
    fig.update_layout(
        template=PLOTLY_THEME,
        margin=dict(l=40, r=20, t=50, b=40),
        font=dict(family="Inter, system-ui, sans-serif", size=13),
        title_font_size=16,
    )
    return fig.to_html(
        full_html=False,
        include_plotlyjs=False,
        div_id=div_id,
        config={"displaylogo": False, "responsive": True},
    )


def od_heatmap(od_df, top_n: int = 14) -> str:
    top_zones = (
        od_df.groupby("origin")["trips_per_day"].sum()
        .sort_values(ascending=False).head(top_n).index.tolist()
    )
    sub = od_df[od_df.origin.isin(top_zones) & od_df.destination.isin(top_zones)]
    matrix = sub.pivot(index="origin", columns="destination", values="trips_per_day").fillna(0)
    matrix = matrix.loc[top_zones, top_zones]
    fig = go.Figure(data=go.Heatmap(
        z=matrix.values,
        x=matrix.columns.tolist(),
        y=matrix.index.tolist(),
        colorscale="YlOrRd",
        hovertemplate="From %{y}<br>To %{x}<br>%{z:,.0f} trips/day<extra></extra>",
        colorbar=dict(title="trips/day"),
    ))
    fig.update_layout(
        title="Origin → Destination Daily Trip Matrix (top zones)",
        xaxis_title="Destination",
        yaxis_title="Origin",
        height=520,
    )
    return _to_html(fig, "od-heatmap")


def od_flow_map(od_df, zones_df, min_trips: int = 400) -> str:
    strong = od_df[od_df.trips_per_day >= min_trips]
    zpos = zones_df.set_index("zone")
    fig = go.Figure()
    for _, r in strong.iterrows():
        o = zpos.loc[r.origin]
        d = zpos.loc[r.destination]
        fig.add_trace(go.Scattermap(
            lon=[o.lon, d.lon], lat=[o.lat, d.lat],
            mode="lines",
            line=dict(width=max(1, r.trips_per_day / 800), color="rgba(200,60,60,0.45)"),
            hoverinfo="skip", showlegend=False,
        ))
    fig.add_trace(go.Scattermap(
        lon=zones_df.lon, lat=zones_df.lat,
        mode="markers+text",
        marker=dict(size=zones_df.population / 10000 + 6, color="#1f4e79"),
        text=zones_df.zone, textposition="top center",
        hovertemplate="<b>%{text}</b><br>Pop: %{marker.size:,.0f}<extra></extra>",
        showlegend=False,
    ))
    fig.update_layout(
        title=f"Devon OD Flow Map (flows ≥ {min_trips} trips/day)",
        map=dict(
            style="open-street-map",
            center=dict(lat=50.72, lon=-3.75),
            zoom=8,
        ),
        height=560,
        margin=dict(l=0, r=0, t=50, b=0),
    )
    return _to_html(fig, "od-flow-map")


def speed_timeseries(speed_df, roads: list[str] | None = None) -> str:
    if roads:
        speed_df = speed_df[speed_df.road.isin(roads)]
    agg = (
        speed_df.groupby(["timestamp", "link"], as_index=False)["mean_speed_mph"].mean()
    )
    fig = px.line(
        agg, x="timestamp", y="mean_speed_mph", color="link",
        title="Mean Speed by Corridor (mph)",
        labels={"timestamp": "Time", "mean_speed_mph": "Mean speed (mph)", "link": "Corridor"},
    )
    fig.update_layout(height=480, legend=dict(orientation="h", y=-0.25))
    return _to_html(fig, "speed-ts")


def speed_by_hour(speed_df) -> str:
    speed_df = speed_df.assign(hour=speed_df.timestamp.dt.hour)
    agg = speed_df.groupby(["hour", "link"], as_index=False)["mean_speed_mph"].mean()
    fig = px.line(
        agg, x="hour", y="mean_speed_mph", color="link",
        title="Average Speed by Hour-of-Day (mph)",
        labels={"hour": "Hour", "mean_speed_mph": "Mean speed (mph)", "link": "Corridor"},
    )
    fig.update_xaxes(dtick=2)
    fig.update_layout(height=420, legend=dict(orientation="h", y=-0.25))
    return _to_html(fig, "speed-hour")


def journey_time_violin(journey_df, pair: tuple[str, str] | None = None, div_id: str = "journey-violin") -> str:
    if pair:
        sub = journey_df[(journey_df.origin == pair[0]) & (journey_df.destination == pair[1])]
        title = f"Journey-Time Distribution by Hour: {pair[0]} → {pair[1]}"
    else:
        sub = journey_df
        title = "Journey-Time Distribution by Hour (all tracked pairs)"
    fig = px.violin(
        sub, x="hour", y="journey_time_min", color="origin",
        points=False, box=True,
        title=title,
        labels={"hour": "Hour", "journey_time_min": "Journey time (min)"},
    )
    fig.update_layout(height=460, violinmode="overlay", legend=dict(orientation="h", y=-0.2))
    return _to_html(fig, div_id)


def journey_median_bar(journey_df) -> str:
    med = (
        journey_df.groupby(["origin", "destination"], as_index=False)["journey_time_min"]
        .median()
        .assign(pair=lambda d: d.origin + " → " + d.destination)
        .sort_values("journey_time_min", ascending=True)
    )
    fig = px.bar(
        med, x="journey_time_min", y="pair", orientation="h",
        title="Median Journey Time by OD Pair (min)",
        labels={"journey_time_min": "Median journey time (min)", "pair": ""},
        color="journey_time_min", color_continuous_scale="Viridis",
    )
    fig.update_layout(height=420, coloraxis_showscale=False)
    return _to_html(fig, "journey-median")


def gps_density_map(gps_df) -> str:
    fig = px.density_map(
        gps_df, lat="lat", lon="lon", z="speed_mph",
        radius=14, center=dict(lat=50.72, lon=-3.75), zoom=7.7,
        map_style="open-street-map",
        color_continuous_scale="Turbo",
        title="Synthetic GPS Ping Density (weighted by recorded speed)",
    )
    fig.update_layout(height=560, margin=dict(l=0, r=0, t=50, b=0))
    return _to_html(fig, "gps-density")


def region_summary_bars(zones_df, od_df) -> str:
    trips_by_region = (
        od_df.merge(zones_df[["zone", "region"]], left_on="origin", right_on="zone")
        .groupby("region", as_index=False)["trips_per_day"].sum()
        .sort_values("trips_per_day", ascending=False)
    )
    fig = px.bar(
        trips_by_region, x="region", y="trips_per_day",
        title="Total Outbound Trips per Day by Region",
        color="region", labels={"trips_per_day": "Trips/day"},
    )
    fig.update_layout(height=340, showlegend=False)
    return _to_html(fig, "region-bars")
