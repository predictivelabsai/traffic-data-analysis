"""Generate a PDF user guide / product demo from the dashboard screenshots.

The resulting PDF (docs/devon-traffic-user-guide.pdf) has:
  - a title page with product summary + KPIs
  - one page per dashboard section with narration + its screenshot
  - a closing page with install / CLI reference

Run:
    python scripts/make_pdf.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image as RLImage, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "screenshots"
OUT = ROOT / "docs" / "devon-traffic-user-guide.pdf"

INK = HexColor("#1c2541")
ACCENT = HexColor("#1f4e79")
ACCENT_2 = HexColor("#c8553d")
MUTED = HexColor("#5b6378")
RULE = HexColor("#e3e6ee")


def _styles():
    ss = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title", parent=ss["Title"], fontName="Helvetica-Bold",
            fontSize=26, leading=32, textColor=ACCENT, spaceAfter=8,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=ss["Normal"], fontName="Helvetica",
            fontSize=12, leading=16, textColor=MUTED, spaceAfter=18,
        ),
        "h1": ParagraphStyle(
            "h1", parent=ss["Heading1"], fontName="Helvetica-Bold",
            fontSize=18, leading=22, textColor=ACCENT, spaceAfter=6, spaceBefore=4,
        ),
        "h2": ParagraphStyle(
            "h2", parent=ss["Heading2"], fontName="Helvetica-Bold",
            fontSize=13, leading=16, textColor=ACCENT_2, spaceAfter=4, spaceBefore=8,
        ),
        "body": ParagraphStyle(
            "body", parent=ss["BodyText"], fontName="Helvetica",
            fontSize=10.5, leading=14.5, textColor=INK, alignment=TA_LEFT,
        ),
        "caption": ParagraphStyle(
            "caption", parent=ss["Italic"], fontName="Helvetica-Oblique",
            fontSize=9, leading=12, textColor=MUTED, spaceBefore=4,
        ),
        "code": ParagraphStyle(
            "code", parent=ss["Code"], fontName="Courier",
            fontSize=9, leading=12, textColor=INK, backColor=HexColor("#f6f7fb"),
        ),
    }


def _fit_image(path: Path, max_w_mm: float, max_h_mm: float) -> RLImage:
    img = Image.open(path)
    w, h = img.size
    ratio = min(max_w_mm * mm / w, max_h_mm * mm / h)
    return RLImage(str(path), width=w * ratio, height=h * ratio)


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(2 * cm, 1.2 * cm, "Devon Traffic Insights — user guide (synthetic demo data)")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(2 * cm, 1.6 * cm, A4[0] - 2 * cm, 1.6 * cm)
    canvas.restoreState()


def build() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    styles = _styles()

    doc = BaseDocTemplate(
        str(OUT), pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=1.8 * cm, bottomMargin=2 * cm,
        title="Devon Traffic Insights — User Guide",
        author="plai",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin,
                  doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="page", frames=[frame], onPage=_footer)])

    story = []

    # -------- title page --------
    story += [
        Paragraph("Devon Traffic Insights", styles["title"]),
        Paragraph(
            "A FastHTML + Plotly reference dashboard for origin–destination, "
            "speed, and journey-time analytics across Devon, Torbay and Plymouth.",
            styles["subtitle"],
        ),
        Spacer(1, 6 * mm),
        Paragraph("What this product delivers", styles["h1"]),
        Paragraph(
            "This application demonstrates software that offers origin and destination "
            "traffic data, speed and journey time data for Devon county (including "
            "Torbay and Plymouth) from GPS signal data — or an equivalent source such as "
            "mobile-network probes.",
            styles["body"],
        ),
        Spacer(1, 3 * mm),
        Paragraph(
            "Out of the box it ships with a deterministic synthetic generator so the "
            "system can be demonstrated, tested and benchmarked end-to-end without any "
            "vendor contracts. Each data module is designed as a drop-in adapter so the "
            "synthetic feed can be replaced by a Vodafone Analytics / O2 Motion / HERE / "
            "TomTom / Streetlight extract with no code changes above the data layer.",
            styles["body"],
        ),
        Spacer(1, 6 * mm),
        Paragraph("Demo KPIs (synthetic 14-day window)", styles["h2"]),
    ]

    kpi_rows = [
        ["Zones tracked", "18 Devon towns + Torbay + Plymouth"],
        ["Origin–destination pairs", "306"],
        ["Total trips / day", "~8,200"],
        ["Monitored road corridors", "12 (M5, A38, A30, A380, A386 …)"],
        ["Journey-time observations", "~23,000"],
        ["Synthetic GPS pings", "5,000"],
    ]
    t = Table(kpi_rows, colWidths=[60 * mm, 100 * mm])
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 10),
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 10),
        ("TEXTCOLOR", (0, 0), (0, -1), ACCENT),
        ("TEXTCOLOR", (1, 0), (1, -1), INK),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [HexColor("#f6f7fb"), HexColor("#ffffff")]),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, RULE),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(t)

    story += [
        Spacer(1, 8 * mm),
        Paragraph("How this guide is organised", styles["h2"]),
        Paragraph(
            "The following pages walk through each of the six dashboard sections "
            "exactly as a new user would see them — the screenshots are captured "
            "from the running FastHTML app via Playwright.",
            styles["body"],
        ),
        PageBreak(),
    ]

    # -------- one page per section --------
    sections = [
        (
            "01-overview.png",
            "Overview",
            "Executive summary of the Devon network.",
            "Six KPI tiles summarise the demo dataset — zones tracked, total OD trips per "
            "day, network-average speed, median journey time, and outbound volumes for the "
            "Plymouth and Torbay travel-to-work areas. Two anchor charts follow: a regional "
            "outbound-volume bar, and a 14-day speed time-series across the key corridors "
            "(A38, A380 and M5) that makes the commuter-peak pattern immediately visible.",
        ),
        (
            "02-od.png",
            "Origin–Destination",
            "Where the trips go.",
            "The heatmap shows daily trip counts between the 14 highest-volume Devon zones. "
            "Strong intra-Torbay flows (Torquay↔Paignton↔Brixham) and the Plymouth↔Ivybridge "
            "corridor are clearly visible. Below, the interactive flow map overlays every "
            "OD pair above 400 trips/day onto OpenStreetMap, with line width scaled to "
            "volume — making regional structure obvious at a glance.",
        ),
        (
            "03-speed.png",
            "Speed",
            "How fast the network actually runs.",
            "Top chart: hourly mean speed per corridor over the simulated 14-day window — "
            "weekday rush-hour troughs are clearly separated from weekend patterns. Bottom "
            "chart: the same data collapsed onto hour-of-day, which is the view operations "
            "teams typically use to tune signal timings, set variable speed-limits or plan "
            "roadworks windows. A30 and A379 show the sharpest commuter dips.",
        ),
        (
            "04-journey.png",
            "Journey time",
            "How long trips take, and how that varies by hour.",
            "The bar chart ranks the eight tracked OD pairs by median journey time. Below, "
            "violin plots show the full hour-by-hour journey-time distribution for "
            "Plymouth → Exeter and Exeter → Torquay. The distribution width tells you "
            "reliability, not just the mean — the key operational question for any "
            "journey-time product.",
        ),
        (
            "05-map.png",
            "GPS map",
            "The ping-level view that a real probe feed would populate.",
            "A density heatmap of synthetic GPS pings across Devon, weighted by recorded "
            "speed. In production this layer is fed by a Vodafone Analytics / O2 Motion / "
            "HERE / TomTom probe extract, or by raw device-level feeds from Cuebiq / "
            "Veraset / Huq / Streetlight. The UX stays identical; only the data adapter "
            "changes.",
        ),
        (
            "06-sources.png",
            "Data sources",
            "Three build paths and the vendor shortlist.",
            "The application ships with an in-app catalogue comparing (1) a solo build on "
            "DCC's own ANPR / Bluetooth / UTMC assets, (2) a solo open-data + ML-synthesis "
            "approach, and (3) a commercial probe-data integration (Vodafone, O2, HERE, "
            "TomTom, INRIX, Streetlight). A 4-step integration pattern — adapter → parquet "
            "cache → MSOA reconciliation → Census-calibrated blend — closes the page.",
        ),
    ]

    for fname, title, subtitle, body in sections:
        path = SHOTS / fname
        if not path.exists():
            continue
        story += [
            Paragraph(title, styles["h1"]),
            Paragraph(subtitle, styles["subtitle"]),
            Paragraph(body, styles["body"]),
            Spacer(1, 4 * mm),
            _fit_image(path, max_w_mm=170, max_h_mm=185),
            Paragraph(f"Screenshot: {fname}", styles["caption"]),
            PageBreak(),
        ]

    # -------- install / CLI reference --------
    story += [
        Paragraph("Installing and running", styles["h1"]),
        Paragraph(
            "<b>Requirements:</b> Python 3.10 or newer. All commands run from the "
            "repository root.",
            styles["body"],
        ),
        Spacer(1, 3 * mm),
        Paragraph(
            "<font face='Courier'>"
            "git clone &lt;repo&gt; traffic-data-analysis<br/>"
            "cd traffic-data-analysis<br/>"
            "python -m venv .venv<br/>"
            "source .venv/bin/activate<br/>"
            "pip install -e .<br/>"
            "devon-traffic serve"
            "</font>",
            styles["body"],
        ),
        Spacer(1, 5 * mm),
        Paragraph("CLI reference", styles["h2"]),
        Paragraph(
            "<font face='Courier'>"
            "devon-traffic --help<br/>"
            "devon-traffic serve --port 5001<br/>"
            "devon-traffic summary<br/>"
            "devon-traffic generate-data --out data<br/>"
            "devon-traffic export od --out od.csv"
            "</font>",
            styles["body"],
        ),
        Spacer(1, 5 * mm),
        Paragraph("Regenerating this guide", styles["h2"]),
        Paragraph(
            "Screenshots are captured via Playwright (see "
            "<font face='Courier'>tests/test_playwright.py</font>). The PDF is "
            "assembled by <font face='Courier'>scripts/make_pdf.py</font>, and the "
            "animated GIF by <font face='Courier'>scripts/make_gif.py</font>.",
            styles["body"],
        ),
        Spacer(1, 10 * mm),
        Paragraph(
            "<i>All figures in this guide are generated from synthetic data. "
            "Do not cite for operational decisions.</i>",
            styles["caption"],
        ),
    ]

    doc.build(story)
    print(f"Wrote {OUT}  ({OUT.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    build()
