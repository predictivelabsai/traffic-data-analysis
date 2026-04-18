"""FastHTML dashboard for Devon traffic (synthetic data)."""

from __future__ import annotations

from fasthtml.common import (
    H1, H2, H3, A, Div, Li, Nav, P, Script, Span, Style, Title, Ul,
    fast_app, serve,
)

from . import charts
from .data import SynthConfig, get_bundle


CSS = """
:root {
  --bg: #f6f7fb;
  --card: #ffffff;
  --ink: #1c2541;
  --muted: #5b6378;
  --accent: #1f4e79;
  --accent-2: #c8553d;
  --border: #e3e6ee;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: Inter, system-ui, -apple-system, "Segoe UI", sans-serif;
  background: var(--bg);
  color: var(--ink);
}
header {
  padding: 22px 34px 8px 34px;
  background: linear-gradient(135deg, #1f4e79 0%, #0b2545 100%);
  color: #fff;
}
header h1 { margin: 0; font-size: 26px; letter-spacing: -0.01em; }
header p { margin: 6px 0 0 0; color: #c9d7ea; font-size: 14px; }
nav {
  background: #0b2545;
  padding: 0 28px;
  border-bottom: 1px solid #102a54;
}
nav ul { list-style: none; padding: 0; margin: 0; display: flex; gap: 4px; flex-wrap: wrap; }
nav li a {
  display: inline-block;
  padding: 12px 18px;
  color: #c9d7ea;
  text-decoration: none;
  font-size: 14px;
  border-bottom: 2px solid transparent;
}
nav li a.active, nav li a:hover {
  color: #fff;
  border-bottom-color: var(--accent-2);
}
main { padding: 24px 28px 40px 28px; max-width: 1400px; margin: 0 auto; }
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 18px 20px;
  margin-bottom: 22px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}
.card h2 { margin: 0 0 4px 0; font-size: 18px; }
.card p.hint { margin: 0 0 10px 0; color: var(--muted); font-size: 13px; }
.grid { display: grid; gap: 22px; }
.grid.cols-2 { grid-template-columns: repeat(auto-fit, minmax(440px, 1fr)); }
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin-bottom: 22px; }
.kpi {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 18px;
}
.kpi .label { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; }
.kpi .value { font-size: 22px; font-weight: 600; color: var(--accent); margin-top: 4px; }
footer { text-align: center; padding: 20px; color: var(--muted); font-size: 12px; }
"""

PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.35.2.min.js"


TABS = [
    ("overview",  "Overview",       "/"),
    ("od",        "Origin-Dest",    "/od"),
    ("speed",     "Speed",          "/speed"),
    ("journey",   "Journey Time",   "/journey"),
    ("map",       "GPS Map",        "/map"),
    ("sources",   "Data Sources",   "/sources"),
]


def _nav(active: str):
    items = [
        Li(A(label, href=href, cls=("active" if key == active else "")))
        for key, label, href in TABS
    ]
    return Nav(Ul(*items))


def _layout(active: str, *content):
    return (
        Title("Devon Traffic Dashboard"),
        Style(CSS),
        Script(src=PLOTLY_CDN),
        Div(
            H1("Devon Traffic Insights"),
            P("Synthetic GPS-derived origin-destination, speed and journey-time analytics for Devon, Torbay and Plymouth."),
            _raw_tag("header"),
        ),
        _nav(active),
        Div(*content, _raw_tag("main")),
        Div(
            "Synthetic data — generated locally for demo purposes. Not traffic advice.",
            _raw_tag("footer"),
        ),
    )


def _raw_tag(tag: str):
    # tiny helper to avoid importing extra fasthtml components
    return None  # tag wrapping done via Div below in create_app


def _kpi(label: str, value: str):
    return Div(
        Div(label, cls="label"),
        Div(value, cls="value"),
        cls="kpi",
    )


def _raw_html(html: str):
    from fasthtml.common import NotStr
    return NotStr(html)


def create_app(cfg: SynthConfig | None = None):
    app, rt = fast_app(live=False, pico=False)
    bundle = get_bundle(cfg)
    zones_df = bundle["zones"]
    od_df = bundle["od"]
    speed_df = bundle["speed"]
    journey_df = bundle["journey"]
    gps_df = bundle["gps"]

    def shell(active: str, *content):
        from fasthtml.common import Header, Main, Footer
        return (
            Title("Devon Traffic Dashboard"),
            Style(CSS),
            Script(src=PLOTLY_CDN),
            Header(
                H1("Devon Traffic Insights"),
                P("Synthetic GPS-derived origin-destination, speed and journey-time analytics for Devon, Torbay and Plymouth."),
            ),
            _nav(active),
            Main(*content),
            Footer("Synthetic data — generated locally for demo purposes. Not traffic advice."),
        )

    # ---------------- Overview ----------------
    @rt("/")
    def overview():
        total_trips = int(od_df.trips_per_day.sum())
        mean_speed = float(speed_df.mean_speed_mph.mean())
        median_jt = float(journey_df.journey_time_min.median())
        torbay_trips = int(
            od_df[od_df.origin.isin(["Torquay", "Paignton", "Brixham"])].trips_per_day.sum()
        )
        plymouth_trips = int(od_df[od_df.origin == "Plymouth"].trips_per_day.sum())

        kpis = Div(
            _kpi("Zones tracked", f"{len(zones_df):,}"),
            _kpi("Total OD trips / day", f"{total_trips:,}"),
            _kpi("Network mean speed", f"{mean_speed:.1f} mph"),
            _kpi("Median journey time", f"{median_jt:.1f} min"),
            _kpi("Plymouth outbound", f"{plymouth_trips:,}"),
            _kpi("Torbay outbound", f"{torbay_trips:,}"),
            cls="kpis",
        )
        return shell(
            "overview",
            kpis,
            Div(
                Div(
                    H2("Region outbound volume"),
                    P("Aggregate daily outbound trips by planning region (Plymouth-area, Torbay, wider Devon).",
                      cls="hint"),
                    _raw_html(charts.region_summary_bars(zones_df, od_df)),
                    cls="card",
                ),
                Div(
                    H2("Corridor speed profile (last 14 days)"),
                    P("Mean hourly speeds across the monitored road corridors.", cls="hint"),
                    _raw_html(charts.speed_timeseries(speed_df, roads=["A38", "A380", "M5"])),
                    cls="card",
                ),
                cls="grid",
            ),
        )

    # ---------------- OD ----------------
    @rt("/od")
    def od():
        return shell(
            "od",
            Div(
                H2("Origin-Destination Matrix"),
                P("Trip counts between Devon zones — gravity model calibrated to population.", cls="hint"),
                _raw_html(charts.od_heatmap(od_df)),
                cls="card",
            ),
            Div(
                H2("Flow Map"),
                P("Geographical view of strong inter-zone flows (line width scales with volume).",
                  cls="hint"),
                _raw_html(charts.od_flow_map(od_df, zones_df)),
                cls="card",
            ),
        )

    # ---------------- Speed ----------------
    @rt("/speed")
    def speed():
        return shell(
            "speed",
            Div(
                H2("Corridor mean speed (time series)"),
                P("Hourly mean speed per monitored corridor across the synthetic 14-day window.",
                  cls="hint"),
                _raw_html(charts.speed_timeseries(speed_df)),
                cls="card",
            ),
            Div(
                H2("Speed by hour of day"),
                P("Averaged over the full period — makes the morning and evening dips clearly visible.",
                  cls="hint"),
                _raw_html(charts.speed_by_hour(speed_df)),
                cls="card",
            ),
        )

    # ---------------- Journey ----------------
    @rt("/journey")
    def journey():
        return shell(
            "journey",
            Div(
                H2("Median journey time by OD pair"),
                P("Synthetic observations aggregated across the simulation window.", cls="hint"),
                _raw_html(charts.journey_median_bar(journey_df)),
                cls="card",
            ),
            Div(
                H2("Hour-of-day distribution — Plymouth → Exeter"),
                P("Distribution of observed journey times for the Plymouth → Exeter corridor.",
                  cls="hint"),
                _raw_html(charts.journey_time_violin(journey_df, ("Plymouth", "Exeter"), div_id="violin-ply-exe")),
                cls="card",
            ),
            Div(
                H2("Hour-of-day distribution — Exeter → Torquay"),
                P("Distribution of observed journey times for the Exeter → Torquay corridor.",
                  cls="hint"),
                _raw_html(charts.journey_time_violin(journey_df, ("Exeter", "Torquay"), div_id="violin-exe-tor")),
                cls="card",
            ),
        )

    # ---------------- Map ----------------
    @rt("/map")
    def gps_map():
        return shell(
            "map",
            Div(
                H2("Synthetic GPS ping density"),
                P("Sampled GPS pings across Devon, weighted by recorded speed. "
                  "Real deployments would consume Vodafone Analytics, O2 Motion, HERE or TomTom probe feeds.",
                  cls="hint"),
                _raw_html(charts.gps_density_map(gps_df)),
                cls="card",
            ),
        )

    # ---------------- Sources ----------------
    @rt("/sources")
    def sources():
        from fasthtml.common import NotStr
        html = """
        <div class="card">
          <h2>Data source integrations</h2>
          <p class="hint">Swap the synthetic generator for any of the feeds below. Free/open sources need no contract;
          commercial feeds give finer granularity and population-calibrated expansion.</p>

          <h3>Build paths we compared</h3>

          <h4>Path 1 — Solo, using DCC's own data</h4>
          <p class="hint">Depends on what Devon County Council will share. Typical DCC assets:</p>
          <ul>
            <li><b>ANPR cameras</b> — Bluetooth/ANPR traces can build OD matrices for corridors they cover.</li>
            <li><b>MOVA / SCOOT / UTMC</b> signal + loop data — link-level speed and flow (no OD).</li>
            <li><b>Bluetooth beacons</b> (e.g. BlueTruth) on key corridors — journey-time series.</li>
            <li><b>Existing traffic counts + DfT Road Traffic Statistics</b> — AADT by link.</li>
          </ul>
          <p class="hint">Assemble OD from ANPR + Bluetooth via matrix-estimation (gravity / Furness / path-choice
          models) — a legitimate transport-modelling technique. <b>Gap:</b> rural Devon coverage is thin; no
          cross-county trip inference without GPS.</p>

          <h4>Path 2 — Solo, using open data + ML synthesis</h4>
          <p class="hint">DfT open data + OSM + Strava Metro (active travel only) + synthetic OD via ML (e.g. graph
          neural nets, gravity-model neural calibration, or entropy-maximisation against Census 2021 commute flows).
          Cheap and differentiated, but weaker on coverage score.</p>

          <h4>Path 3 — Commercial probe-data integration (recommended)</h4>
          <p class="hint">Best coverage and signal quality; requires contracts. See vendor list below.</p>

          <h3>Free / open</h3>
          <ul>
            <li><b>Department for Transport traffic counts</b> — AADT and hourly count data by road link.
              <a href="https://roadtraffic.dft.gov.uk/downloads" target="_blank">dft.gov.uk</a></li>
            <li><b>National Highways WebTRIS</b> — motorway and strategic-road-network loop detectors (incl. M5).
              <a href="https://webtris.highwaysengland.co.uk/" target="_blank">webtris</a></li>
            <li><b>Devon County Council open data</b> — local road counts, bus patronage, cycle counters.
              <a href="https://www.devon.gov.uk/roadsandtransport" target="_blank">devon.gov.uk</a></li>
            <li><b>OS Open Roads / OS Open Zoomstack</b> — free road network geometry for routing.</li>
            <li><b>TfL Unified API / BODS</b> — bus open data (NaPTAN, timetables, real-time).
              <a href="https://data.bus-data.dft.gov.uk/" target="_blank">bus-data.dft.gov.uk</a></li>
            <li><b>OpenStreetMap + Overpass / Valhalla</b> — free routing and turn-by-turn estimates.</li>
            <li><b>ONS Census 2021 origin-destination</b> — commute flows by MSOA/LSOA (ground truth for OD calibration).</li>
            <li><b>Strava Metro</b> — aggregated bike/pedestrian GPS (free for public bodies).</li>
          </ul>

          <h3>Commercial — probe / mobile / GPS</h3>
          <ul>
            <li><b>Vodafone Analytics</b> — UK mobile-network derived OD flows, dwell-times, visitor analytics.</li>
            <li><b>Telefónica / O2 Motion</b> — aggregated O2 mobility insights, good UK coverage incl. South-West.</li>
            <li><b>BT Active Intelligence / EE Mobility</b> — mobile probe data across EE's network.</li>
            <li><b>HERE Traffic API & Probe Data</b> — real-time link speeds, historic 5-min bins, journey times.</li>
            <li><b>TomTom Traffic Stats / O/D Analysis</b> — floating-car data with commercial-fleet GPS; strong on A-roads.</li>
            <li><b>INRIX Roadway Analytics</b> — probe-vehicle speeds, incident feeds, OD analyses.</li>
            <li><b>Google Maps Roads / Distance Matrix API</b> — live & typical travel times between coordinates.</li>
            <li><b>Mapbox Movement</b> — anonymised mobile-SDK GPS aggregates.</li>
            <li><b>Streetlight Data (Jacobs)</b> — mobile + nav-GPS OD matrices, widely used in UK DfT studies.</li>
            <li><b>Cuebiq / Veraset / Huq Industries</b> — raw device-level mobile GPS panels (for custom OD builds).</li>
            <li><b>Teralytics</b> — telco-derived trip chains and OD (global footprint).</li>
          </ul>

          <h3>Paid-ANPR / camera feeds</h3>
          <ul>
            <li><b>Devon &amp; Cornwall Police ANPR</b> (via data-sharing agreement).</li>
            <li><b>Vivacity Labs / VivaCity AI cameras</b> — classified multi-modal counts, journey times.</li>
            <li><b>Clearview Intelligence M100</b> — Bluetooth/Wi-Fi travel-time network (commonly deployed on A38/A30).</li>
          </ul>

          <h3>Suggested integration pattern</h3>
          <ol>
            <li>Replace <code>devon_traffic.data.build_*</code> functions with adapters pulling from each feed's API or nightly dump.</li>
            <li>Cache normalised parquet per feed under <code>data/</code>.</li>
            <li>Reconcile zone geometries to a common MSOA or custom TAZ layer.</li>
            <li>Blend: use Census 2021 OD as prior, calibrate with Vodafone/O2 expansion factors, validate with WebTRIS counts.</li>
          </ol>
        </div>
        """
        return shell("sources", NotStr(html))

    return app


app = create_app()


def run(host: str = "127.0.0.1", port: int = 5001):
    serve(appname="devon_traffic.app", host=host, port=port, reload=False)
