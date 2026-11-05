"""DA-012 CatTracks Ridership Analytics.

A Streamlit application for exploring historical UC Merced CatTracks boarding
counts. Historical stop coordinates are geocoder estimates unless independently
verified; current GTFS geometry is shown as a separate, separately dated layer.
"""
from __future__ import annotations

from pathlib import Path
import html
import math
import os
import re
import sys

import folium
from folium.plugins import Fullscreen, HeatMap
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ridership_analysis import load_ridership_data, quality_report  # noqa: E402
from src.geospatial import (  # noqa: E402
    CATTRACKS_GTFS_URL,
    fetch_current_gtfs,
    geocode_historical_stops,
    parse_gtfs_archive,
)

st.set_page_config(
    page_title="DA-012 | CatTracks Analytics",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# A restrained palette: one blue accent, route colours, neutral surfaces.
ROUTE_COLORS = {
    "C1 Blue": "#3478C8",
    "C1 Gold": "#C58A24",
    "C2 Express": "#159A8A",
    "G-Line": "#8063B5",
}
ROUTE_PALETTE = list(ROUTE_COLORS.values())
PERIOD_COLORS = {"February 2019": "#3478C8", "October 2018": "#D47A42"}

THEMES = {
    "Dark": {
        "bg": "#111418", "sidebar": "#171B20", "surface": "#1A2027", "surface2": "#202831",
        "border": "#303A45", "text": "#E8EDF2", "muted": "#A5B0BA", "faint": "#7F8B96",
        "accent": "#76A9E8", "accent_soft": "rgba(118,169,232,.13)", "grid": "#303943",
        "plot": "rgba(0,0,0,0)", "hover": "#222B34",
    },
    "Light": {
        "bg": "#F4F6F8", "sidebar": "#FFFFFF", "surface": "#FFFFFF", "surface2": "#EDF1F5",
        "border": "#D8DEE5", "text": "#202830", "muted": "#596673", "faint": "#75818C",
        "accent": "#245F9E", "accent_soft": "rgba(36,95,158,.09)", "grid": "#E2E7EC",
        "plot": "rgba(0,0,0,0)", "hover": "#FFFFFF",
    },
}


@st.cache_data(show_spinner="Loading CatTracks ridership data…")
def get_ridership_data(data_directory: str) -> pd.DataFrame:
    return load_ridership_data(Path(data_directory))


def fmt_num(value: float | int) -> str:
    return f"{value:,.0f}"


def apply_theme(theme_name: str) -> dict[str, str]:
    t = THEMES[theme_name]
    st.markdown(
        f"""
        <style>
        :root {{
          --app-bg:{t['bg']}; --app-sidebar:{t['sidebar']}; --app-surface:{t['surface']};
          --app-surface-2:{t['surface2']}; --app-border:{t['border']}; --app-text:{t['text']};
          --app-muted:{t['muted']}; --app-faint:{t['faint']}; --app-accent:{t['accent']};
          --app-accent-soft:{t['accent_soft']};
        }}
        html, body, [data-testid="stAppViewContainer"], .stApp {{
          background:var(--app-bg) !important; color:var(--app-text) !important;
        }}
        [data-testid="stHeader"] {{ background:var(--app-bg) !important; }}
        [data-testid="stToolbar"] {{ right:1rem; }}
        .block-container {{ max-width:1500px; padding-top:1.25rem; padding-bottom:1.4rem; }}
        [data-testid="stSidebar"] {{ background:var(--app-sidebar) !important; border-right:1px solid var(--app-border); }}
        [data-testid="stSidebar"] > div:first-child {{ background:var(--app-sidebar) !important; }}
        [data-testid="stSidebar"] .block-container {{ padding-top:1.3rem; }}
        [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li {{ color:var(--app-text); }}
        h1,h2,h3,h4,h5 {{ color:var(--app-text) !important; letter-spacing:-.02em; }}
        h1 {{ font-size:2rem !important; font-weight:720 !important; }}
        h2 {{ font-size:1.48rem !important; font-weight:680 !important; }}
        h3 {{ font-size:1.12rem !important; font-weight:650 !important; }}
        p, label, [data-testid="stCaptionContainer"] {{ color:var(--app-muted); }}
        [data-testid="stMetric"] {{ background:var(--app-surface) !important; border:1px solid var(--app-border); border-radius:7px; padding:15px 17px; box-shadow:none; }}
        [data-testid="stMetricLabel"] p {{ color:var(--app-muted) !important; font-size:.81rem; }}
        [data-testid="stMetricValue"] {{ color:var(--app-text) !important; font-weight:700; letter-spacing:-.025em; }}
        [data-testid="stMetricDelta"] {{ font-size:.78rem; }}
        [data-testid="stVerticalBlockBorderWrapper"] > div {{ border-color:var(--app-border) !important; border-radius:7px !important; }}
        [data-testid="stPlotlyChart"] {{ background:var(--app-surface) !important; border:1px solid var(--app-border); border-radius:7px; padding:7px 7px 0; }}
        [data-testid="stDataFrame"] {{ border:1px solid var(--app-border); border-radius:7px; overflow:hidden; }}
        [data-testid="stSelectbox"] > div > div, [data-testid="stMultiSelect"] > div > div,
        [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
        [data-testid="stDateInput"] input {{ background:var(--app-surface) !important; color:var(--app-text) !important; border-color:var(--app-border) !important; }}
        div.stButton > button, div.stDownloadButton > button {{ border-radius:5px; font-weight:600; border:1px solid var(--app-border); min-height:2.5rem; }}
        div.stButton > button[kind="primary"] {{ background:var(--app-accent) !important; color:white !important; border-color:var(--app-accent) !important; }}
        [data-testid="stRadio"] label {{ color:var(--app-text) !important; }}
        [data-testid="stExpander"] {{ border-color:var(--app-border) !important; border-radius:6px !important; background:var(--app-surface) !important; }}
        [data-testid="stSidebar"] [data-testid="stExpander"] summary {{ font-weight:650; color:var(--app-text) !important; }}
        [data-testid="stAlert"] {{ border-radius:6px; }}
        hr {{ border-color:var(--app-border) !important; }}
        .brand-lockup {{ padding:4px 2px 16px; border-bottom:1px solid var(--app-border); margin-bottom:15px; }}
        .brand-mark {{ display:inline-flex; align-items:center; justify-content:center; width:38px; height:38px; border-radius:5px; background:var(--app-accent); color:#fff; font-size:13px; font-weight:800; margin-bottom:10px; letter-spacing:.03em; }}
        .brand-name {{ font-size:1.02rem; font-weight:720; line-height:1.25; color:var(--app-text); }}
        .brand-sub {{ font-size:.73rem; color:var(--app-muted); margin-top:4px; }}
        .nav-label {{ color:var(--app-faint); font-size:.66rem; text-transform:uppercase; letter-spacing:.13em; font-weight:700; margin:13px 0 6px; }}
        .page-kicker {{ color:var(--app-accent); font-size:.68rem; text-transform:uppercase; letter-spacing:.13em; font-weight:750; margin:0 0 6px; }}
        .page-deck {{ color:var(--app-muted); margin-top:-6px; margin-bottom:18px; font-size:.93rem; }}
        .section-rule {{ border-top:1px solid var(--app-border); margin:20px 0 17px; }}
        .plain-note {{ padding:11px 14px; background:var(--app-surface-2); border-left:3px solid var(--app-accent); border-radius:0 5px 5px 0; color:var(--app-muted); font-size:.82rem; line-height:1.5; margin:8px 0 16px; }}
        .insight-line {{ display:flex; flex-direction:column; gap:4px; padding:2px 0; }}
        .insight-label {{ font-size:.68rem; color:var(--app-faint); text-transform:uppercase; letter-spacing:.09em; font-weight:700; }}
        .insight-value {{ font-size:1.14rem; font-weight:700; color:var(--app-text); }}
        .insight-detail {{ color:var(--app-muted); font-size:.79rem; line-height:1.4; }}
        .identity-strip {{ color:var(--app-muted); font-size:.75rem; padding:10px 0 2px; }}
        .footer-line {{ color:var(--app-faint); border-top:1px solid var(--app-border); margin-top:28px; padding-top:13px; font-size:.73rem; display:flex; justify-content:space-between; gap:10px; flex-wrap:wrap; }}
        .map-status {{ display:flex; align-items:center; gap:8px; color:var(--app-muted); font-size:.78rem; margin:5px 0 11px; }}
        .status-dot {{ width:8px; height:8px; border-radius:50%; background:#C58A24; display:inline-block; }}
        @media(max-width:700px) {{ .block-container {{ padding-left:1rem; padding-right:1rem; }} h1 {{font-size:1.55rem !important;}} }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    return t


def chart_layout(fig: go.Figure, theme: dict[str, str], *, height: int = 390, legend: bool = True) -> go.Figure:
    fig.update_layout(
        dragmode=False,
        template="plotly_dark" if theme["bg"] == "#111418" else "plotly_white",
        height=height,
        margin=dict(l=18, r=18, t=45, b=22),
        paper_bgcolor=theme["plot"],
        plot_bgcolor=theme["plot"],
        font=dict(family="Arial, Helvetica, sans-serif", color=theme["text"], size=12),
        colorway=ROUTE_PALETTE,
        hoverlabel=dict(bgcolor=theme["hover"], bordercolor=theme["border"], font=dict(color=theme["text"])),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(0,0,0,0)") if legend else dict(visible=False),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=theme["border"], tickfont=dict(color=theme["muted"]))
    fig.update_yaxes(showgrid=True, gridcolor=theme["grid"], zeroline=False, linecolor=theme["border"], tickfont=dict(color=theme["muted"]))
    return fig


def render_chart(fig: go.Figure, key: str, *, height: int | None = None) -> None:
    config = {"displaylogo": False, "responsive": True, "scrollZoom": False, "doubleClick": "reset", "displayModeBar": "hover", "modeBarButtonsToRemove": ["zoom2d", "pan2d", "select2d", "lasso2d", "zoomIn2d", "zoomOut2d"]}
    st.plotly_chart(fig, use_container_width=True, key=key, config=config, theme=None)


def section_title(kicker: str, title: str, deck: str | None = None) -> None:
    st.markdown(f'<div class="page-kicker">{html.escape(kicker)}</div>', unsafe_allow_html=True)
    st.title(title)
    if deck:
        st.markdown(f'<div class="page-deck">{html.escape(deck)}</div>', unsafe_allow_html=True)


def insight(label: str, value: str, detail: str) -> None:
    st.markdown(
        f'<div class="insight-line"><div class="insight-label">{html.escape(label)}</div>'
        f'<div class="insight-value">{html.escape(value)}</div>'
        f'<div class="insight-detail">{html.escape(detail)}</div></div>',
        unsafe_allow_html=True,
    )


def no_data() -> None:
    st.warning("No records match the current filters. Adjust the sidebar filters or reset them.")
    st.stop()


def get_carto_api_key() -> str | None:
    """Read an optional CARTO key from the local password field, env or secrets."""
    session_key = str(st.session_state.get("carto_api_key_input", "")).strip()
    if session_key:
        return session_key
    env_key = os.environ.get("CARTO_API_KEY", "").strip()
    if env_key:
        return env_key
    try:
        return str(st.secrets.get("CARTO_API_KEY", "")).strip() or None
    except Exception:
        return None


def available_map_styles() -> list[str]:
    """Keep key-free OSM styles available and reveal CARTO styles only with a key."""
    options = ["OpenStreetMap Standard", "OpenStreetMap Humanitarian"]
    if get_carto_api_key():
        options.extend(["CARTO Positron · Light", "CARTO Dark Matter · Dark", "CARTO Voyager"])
    return options


def base_map(
    location: tuple[float, float] = (37.363, -120.425),
    zoom: float = 12.8,
    map_style: str = "OpenStreetMap Standard",
) -> folium.Map:
    """Build one basemap layer, with explicit attribution and no layer menu."""
    fmap = folium.Map(
        location=location,
        zoom_start=int(round(zoom)),
        tiles=None,
        control_scale=True,
        prefer_canvas=True,
        zoom_control=True,
    )
    if map_style == "OpenStreetMap Humanitarian":
        folium.TileLayer(
            tiles="https://tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
            name="OpenStreetMap Humanitarian",
            attr='© OpenStreetMap contributors · Humanitarian OpenStreetMap Team',
            max_zoom=19,
            control=False,
            show=True,
        ).add_to(fmap)
    elif map_style.startswith("CARTO") and get_carto_api_key():
        key = get_carto_api_key()
        style = {
            "CARTO Positron · Light": "light_all",
            "CARTO Dark Matter · Dark": "dark_all",
            "CARTO Voyager": "rastertiles/voyager",
        }.get(map_style, "light_all")
        folium.TileLayer(
            tiles=f"https://basemaps.cartocdn.com/{style}/{{z}}/{{x}}/{{y}}.png?key={key}",
            name=map_style,
            attr='© OpenStreetMap contributors · © CARTO',
            max_zoom=20,
            control=False,
            show=True,
        ).add_to(fmap)
    else:
        # Do not let an obsolete saved CARTO selection display the API-key watermark.
        folium.TileLayer(
            tiles="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            name="OpenStreetMap Standard",
            attr='© OpenStreetMap contributors',
            max_zoom=19,
            control=False,
            show=True,
        ).add_to(fmap)
    Fullscreen(position="topright", title="Expand map", title_cancel="Exit map", force_separate_button=True).add_to(fmap)
    return fmap


def initial_map_view(points: pd.DataFrame, default_center=(37.363, -120.425), default_zoom=12.8) -> tuple[tuple[float, float], float]:
    """Compute a stable first view from the visible stop coordinates."""
    if points.empty or not {"latitude", "longitude"}.issubset(points.columns):
        return (float(default_center[0]), float(default_center[1])), float(default_zoom)
    lat = pd.to_numeric(points["latitude"], errors="coerce").dropna()
    lon = pd.to_numeric(points["longitude"], errors="coerce").dropna()
    if lat.empty or lon.empty:
        return (float(default_center[0]), float(default_center[1])), float(default_zoom)
    span = max(float(lat.max() - lat.min()), float(lon.max() - lon.min()))
    zoom = 14.0 if span < 0.012 else 13.0 if span < 0.035 else 12.0 if span < 0.08 else 11.0
    return (float(lat.median()), float(lon.median())), zoom


def read_saved_viewport(viewport_key: str, points: pd.DataFrame) -> tuple[tuple[float, float], float]:
    """Return last user map centre/zoom, or a useful first view."""
    saved = st.session_state.get(viewport_key)
    if isinstance(saved, dict) and saved.get("center") and saved.get("zoom") is not None:
        return (float(saved["center"][0]), float(saved["center"][1])), float(saved["zoom"])
    return initial_map_view(points)


def save_map_viewport(viewport_key: str, event: dict | None) -> None:
    """Persist the Leaflet viewport so changing filters does not reframe the map."""
    if not isinstance(event, dict):
        return
    center, zoom = event.get("center"), event.get("zoom")
    if isinstance(center, dict) and center.get("lat") is not None and center.get("lng") is not None and zoom is not None:
        st.session_state[viewport_key] = {"center": (float(center["lat"]), float(center["lng"])), "zoom": float(zoom)}
    elif isinstance(center, (list, tuple)) and len(center) == 2 and zoom is not None:
        st.session_state[viewport_key] = {"center": (float(center[0]), float(center[1])), "zoom": float(zoom)}


def persist_historical_map_viewport() -> None:
    """Component callback: save the latest historical map view before rerender."""
    save_map_viewport(
        "da012_hist_viewport_v5",
        st.session_state.get("historical_demand_map_v5"),
    )


def persist_gtfs_map_viewport() -> None:
    """Component callback: save the latest GTFS map view before rerender."""
    save_map_viewport(
        "da012_gtfs_viewport_v5",
        st.session_state.get("gtfs_route_map_v5"),
    )


def period_state_key(period: str) -> str:
    """Return a stable Streamlit key for one billing-period checkbox."""
    slug = re.sub(r"[^a-z0-9]+", "_", str(period).lower()).strip("_")
    return f"filter_period_{slug}"



def closest_point(points: pd.DataFrame, click: dict | None, max_distance_km: float = 0.25) -> pd.Series | None:
    """Return the nearest mapped point only when a map click is within 250 m."""
    if not click or points.empty or click.get("lat") is None or click.get("lng") is None:
        return None
    lat, lon = float(click["lat"]), float(click["lng"])
    dlat_km = (points["latitude"].astype(float) - lat) * 111.32
    dlon_km = (points["longitude"].astype(float) - lon) * 111.32 * math.cos(math.radians(lat))
    distances = (dlat_km ** 2 + dlon_km ** 2) ** 0.5
    idx = distances.idxmin()
    if float(distances.loc[idx]) > max_distance_km:
        return None
    return points.loc[idx]


# ----------------------------------------------------------------------------
# Load data and initialise app state
# ----------------------------------------------------------------------------
try:
    ridership = get_ridership_data(str(DATA_DIR))
except Exception as exc:
    st.error("Unable to load the CatTracks workbooks. Check that both source Excel files are in data/.")
    st.exception(exc)
    st.stop()

if "da012_theme" not in st.session_state:
    st.session_state["da012_theme"] = "Dark"
theme_name = st.session_state["da012_theme"]
theme = apply_theme(theme_name)

all_periods = sorted(ridership["period"].dropna().unique().tolist(), key=lambda p: ridership.loc[ridership["period"] == p, "period_order"].min())
all_routes = sorted(ridership["route"].dropna().unique().tolist())
all_time_bands = [b for b in ["Early morning", "Morning peak", "Midday", "Evening peak", "Night"] if b in ridership["time_band"].unique()]
all_peak_statuses = [s for s in ["Peak", "Off-peak"] if s in ridership["peak_status"].unique()]
min_hour, max_hour = int(ridership["departure_hour"].min()), int(ridership["departure_hour"].max())

def reset_global_filters() -> None:
    """Reset sidebar filter state through a pre-rerun button callback."""
    for period in all_periods:
        st.session_state[period_state_key(period)] = True
    st.session_state["route_filter"] = list(all_routes)
    st.session_state["time_band_filter"] = list(all_time_bands)
    st.session_state["peak_status_filter"] = list(all_peak_statuses)
    st.session_state["hour_filter"] = (min_hour, max_hour)


# Sidebar is the only primary navigation: no page-body tabs.
with st.sidebar:
    st.markdown(
        '<div class="brand-lockup"><div class="brand-mark">DA<br>012</div>'
        '<div class="brand-name">CatTracks Analytics</div>'
        '<div class="brand-sub">Public Transport Ridership Analysis</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="nav-label">Workspace</div>', unsafe_allow_html=True)
    pages = ["Geospatial Analysis", "Overview", "Routes & Stops", "Time Patterns", "Data Explorer", "Project Team", "Methodology"]
    page = st.radio("Navigation", pages, label_visibility="collapsed", key="da012_page")

    st.markdown('<div class="nav-label">Appearance</div>', unsafe_allow_html=True)
    new_theme = st.radio("Theme", ["Dark", "Light"], horizontal=True, label_visibility="collapsed", key="da012_theme_control", index=0 if theme_name == "Dark" else 1)
    if new_theme != theme_name:
        st.session_state["da012_theme"] = new_theme
        st.rerun()

    with st.expander("Global filters", expanded=False):
        st.caption("These selections apply across every analysis page.")
        st.markdown("**Billing period**")
        period_columns = st.columns(max(1, len(all_periods)))
        selected_periods = []
        for column, period in zip(period_columns, all_periods):
            key = period_state_key(period)
            if key not in st.session_state:
                st.session_state[key] = True
            if column.checkbox(period, key=key):
                selected_periods.append(period)
        st.markdown("**Routes**")
        selected_routes = st.multiselect("Bus routes", all_routes, default=all_routes, key="route_filter", label_visibility="collapsed")
        st.markdown("**Time of day**")
        selected_time_bands = st.multiselect("Time bands", all_time_bands, default=all_time_bands, key="time_band_filter", label_visibility="collapsed")
        st.markdown("**Demand classification**")
        selected_peak_status = st.multiselect("Demand status", all_peak_statuses, default=all_peak_statuses, key="peak_status_filter", label_visibility="collapsed")
        st.markdown("**Scheduled departure hour**")
        selected_hours = st.slider("Departure hour range", min_value=min_hour, max_value=max_hour, value=(min_hour, max_hour), key="hour_filter", label_visibility="collapsed")
        st.button("Reset all filters", use_container_width=True, on_click=reset_global_filters)

    with st.expander("Map appearance", expanded=False):
        st.caption("Standard OpenStreetMap is free to use without a provider API key. CARTO styles are optional.")
        st.text_input("CARTO basemap key (optional)", type="password", key="carto_api_key_input", placeholder="Paste your free CARTO key")
        st.caption("CARTO offers a free non-commercial tier. The key is kept in this local Streamlit session; do not commit it to GitHub.")
        st.markdown("[Request a free CARTO key](https://www.carto.com/basemaps/apikey/)")
        map_style_options = available_map_styles()
        if st.session_state.get("da012_map_style") not in map_style_options:
            st.session_state["da012_map_style"] = "OpenStreetMap Standard"
        map_style_choice = st.selectbox("Basemap", map_style_options, key="da012_map_style")

    st.divider()
    st.markdown('<div class="nav-label">Project lead</div>', unsafe_allow_html=True)
    st.markdown("**Mohd. Shoaib**  \n<span class='muted'>Project Lead · B.Tech III F</span>", unsafe_allow_html=True)
    st.caption("Invertis University · Group BTech_DA_08 · DA-012")

filtered = ridership[
    ridership["period"].isin(selected_periods)
    & ridership["route"].isin(selected_routes)
    & ridership["time_band"].isin(selected_time_bands)
    & ridership["peak_status"].isin(selected_peak_status)
    & ridership["departure_hour"].between(selected_hours[0], selected_hours[1])
].copy()

st.markdown(
    '<div class="identity-strip">INVERTIS UNIVERSITY, BAREILLY　/　B.TECH COMPUTER SCIENCE & ENGINEERING　/　SEMESTER III　/　PROJECT DA-012</div>',
    unsafe_allow_html=True,
)
if filtered.empty:
    no_data()

filtered_total = float(filtered["passenger_count"].sum())
peak_total = float(filtered.loc[filtered["peak_status"] == "Peak", "passenger_count"].sum())
peak_share = peak_total / filtered_total * 100 if filtered_total else 0.0
route_totals = filtered.groupby("route")["passenger_count"].sum().sort_values(ascending=False)
stop_totals = filtered.groupby("stop")["passenger_count"].sum().sort_values(ascending=False)
hour_totals = filtered.groupby("departure_hour")["passenger_count"].sum().sort_values(ascending=False)

# ----------------------------------------------------------------------------
# Page: Overview
# ----------------------------------------------------------------------------
if page == "Overview":
    section_title("DA-012 / Dashboard", "Public Transport Ridership Analysis", "Historical CatTracks campus bus boarding patterns · October 2018 and February 2019")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Recorded boardings", fmt_num(filtered_total))
    m2.metric("Routes in view", f"{filtered['route'].nunique()} / 4")
    m3.metric("Stops represented", fmt_num(filtered["stop"].nunique()))
    m4.metric("Departure times", fmt_num(filtered["departure_time"].nunique()))
    m5.metric("Peak share", f"{peak_share:.1f}%")
    st.markdown('<div class="plain-note"><strong>Interpretation:</strong> these are recorded passenger boardings, not unique passengers. Billing-period totals are not adjusted for operating days and must not be interpreted as a growth rate.</div>', unsafe_allow_html=True)

    highest_route = str(route_totals.index[0])
    highest_stop = str(stop_totals.index[0])
    peak_hour = int(hour_totals.index[0])
    st.markdown("#### Key observations in the selected data")
    c1, c2, c3 = st.columns(3)
    with c1:
        insight("Highest-demand route", highest_route, f"{fmt_num(route_totals.iloc[0])} recorded boardings")
    with c2:
        insight("Busiest recorded stop", highest_stop, f"{fmt_num(stop_totals.iloc[0])} recorded boardings")
    with c3:
        insight("Busiest scheduled hour", f"{peak_hour:02d}:00–{peak_hour:02d}:59", f"{fmt_num(hour_totals.iloc[0])} recorded boardings")

    st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
    left, right = st.columns([1.15, 1], gap="large")
    with left:
        st.markdown("#### Boarding counts by route")
        mode = st.radio("Chart type", ["Grouped", "Stacked"], horizontal=True, key="overview_mode")
        route_period = filtered.groupby(["route", "period"], as_index=False)["passenger_count"].sum().rename(columns={"passenger_count": "boardings"})
        fig = px.bar(route_period, x="route", y="boardings", color="period", barmode="group" if mode == "Grouped" else "stack", text_auto=".2s", color_discrete_map=PERIOD_COLORS, labels={"route": "Route", "boardings": "Boardings", "period": "Billing period"})
        fig.update_traces(hovertemplate="<b>%{x}</b><br>%{fullData.name}: %{y:,.0f} boardings<extra></extra>")
        fig.update_layout(xaxis_title=None, yaxis_title="Recorded boardings", bargap=.32)
        render_chart(chart_layout(fig, theme, height=390), "overview_route_demand")
    with right:
        st.markdown("#### Share by route")
        share = route_totals.rename_axis("route").reset_index(name="boardings")
        fig = px.pie(share, names="route", values="boardings", hole=.62, color="route", color_discrete_map=ROUTE_COLORS)
        fig.update_traces(textposition="inside", textinfo="percent+label", marker=dict(line=dict(color=theme["surface"], width=2)), hovertemplate="<b>%{label}</b><br>%{value:,.0f} boardings<br>%{percent}<extra></extra>")
        fig.update_layout(showlegend=False, annotations=[dict(text=f"{fmt_num(filtered_total)}<br><span style='font-size:10px'>BOARDINGS</span>", x=.5, y=.5, showarrow=False, font=dict(color=theme["text"], size=16))])
        render_chart(chart_layout(fig, theme, height=390, legend=False), "overview_route_share")

    st.markdown("#### Billing-period totals")
    period_table = filtered.groupby("period", as_index=False)["passenger_count"].sum().rename(columns={"passenger_count": "Recorded boardings"})
    st.dataframe(period_table, hide_index=True, use_container_width=True)

# ----------------------------------------------------------------------------
# Page: Routes & Stops
# ----------------------------------------------------------------------------
elif page == "Routes & Stops":
    section_title("Demand distribution", "Routes & Stops", "Compare recorded boardings across the four selected weekday routes and their stops.")
    a, b = st.columns([1.15, 1], gap="large")
    with a:
        top_n = st.slider("Stops to rank", 5, 25, 10, key="top_stop_n")
        top_stops = filtered.groupby("stop", as_index=False)["passenger_count"].sum().rename(columns={"passenger_count": "boardings"}).nlargest(top_n, "boardings").sort_values("boardings")
        fig = px.bar(top_stops, x="boardings", y="stop", orientation="h", text_auto=".2s", color="boardings", color_continuous_scale=["#8CA6BF", theme["accent"]], labels={"stop": "Stop", "boardings": "Boardings"})
        fig.update_layout(coloraxis_showscale=False, xaxis_title="Recorded boardings", yaxis_title=None)
        fig.update_traces(hovertemplate="<b>%{y}</b><br>%{x:,.0f} boardings<extra></extra>")
        render_chart(chart_layout(fig, theme, height=max(390, top_n * 29), legend=False), "top_stops_rank")
    with b:
        st.markdown("#### Peak vs off-peak by route")
        peak_route = filtered.groupby(["route", "peak_status"], as_index=False)["passenger_count"].sum().rename(columns={"passenger_count": "boardings"})
        fig = px.bar(peak_route, x="route", y="boardings", color="peak_status", barmode="group", text_auto=".2s", color_discrete_map={"Peak": "#159A8A", "Off-peak": "#8B9AA8"}, labels={"route": "Route", "boardings": "Boardings", "peak_status": "Demand period"})
        fig.update_layout(xaxis_title=None, yaxis_title="Recorded boardings")
        fig.update_traces(hovertemplate="<b>%{x}</b><br>%{fullData.name}: %{y:,.0f}<extra></extra>")
        render_chart(chart_layout(fig, theme, height=390), "peak_route_comparison")
    st.markdown("#### Route-level summary")
    route_summary = filtered.groupby(["route", "period"], as_index=False)["passenger_count"].sum().rename(columns={"passenger_count": "Recorded boardings"}).sort_values(["period", "Recorded boardings"], ascending=[True, False])
    st.dataframe(route_summary, hide_index=True, use_container_width=True)

# ----------------------------------------------------------------------------
# Page: Time patterns
# ----------------------------------------------------------------------------
elif page == "Time Patterns":
    section_title("Temporal analysis", "Time Patterns", "Explore when scheduled departures carry the highest recorded boarding counts.")
    left, right = st.columns([1.35, 1], gap="large")
    with left:
        visual = st.radio("Visualisation", ["Line", "Bars"], horizontal=True, key="time_visual")
        hourly = filtered.groupby(["period", "route", "departure_hour"], as_index=False)["passenger_count"].sum().rename(columns={"passenger_count": "boardings"})
        if visual == "Line":
            fig = px.line(hourly, x="departure_hour", y="boardings", color="route", line_dash="period", markers=True, color_discrete_map=ROUTE_COLORS, labels={"departure_hour": "Scheduled departure hour", "boardings": "Boardings", "route": "Route", "period": "Billing period"})
        else:
            fig = px.bar(hourly, x="departure_hour", y="boardings", color="route", barmode="group", facet_col="period", color_discrete_map=ROUTE_COLORS, labels={"departure_hour": "Departure hour", "boardings": "Boardings", "route": "Route"})
        fig.update_xaxes(dtick=1, tickformat="d")
        fig.update_layout(xaxis_title="Scheduled departure hour", yaxis_title="Recorded boardings")
        render_chart(chart_layout(fig, theme, height=430), "hourly_demand")
    with right:
        st.markdown("#### Demand by time band")
        band_order = ["Early morning", "Morning peak", "Midday", "Evening peak", "Night"]
        bands = filtered.groupby("time_band", as_index=False)["passenger_count"].sum().rename(columns={"passenger_count": "boardings"})
        bands["time_band"] = pd.Categorical(bands["time_band"], categories=band_order, ordered=True)
        bands = bands.sort_values("time_band")
        fig = px.bar(bands, x="time_band", y="boardings", color="time_band", color_discrete_sequence=ROUTE_PALETTE, labels={"time_band": "Time band", "boardings": "Boardings"}, text_auto=".2s")
        fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title="Recorded boardings")
        render_chart(chart_layout(fig, theme, height=430, legend=False), "time_band_distribution")
    st.markdown("#### Route × departure-hour intensity")
    heat = filtered.groupby(["route", "departure_hour"], as_index=False)["passenger_count"].sum().pivot(index="route", columns="departure_hour", values="passenger_count").fillna(0)
    fig = px.imshow(heat, aspect="auto", color_continuous_scale=[theme["surface2"], theme["accent"]], labels={"x": "Departure hour", "y": "Route", "color": "Boardings"})
    fig.update_xaxes(side="bottom", tickmode="linear", dtick=1)
    render_chart(chart_layout(fig, theme, height=270, legend=False), "route_hour_heatmap")

# ----------------------------------------------------------------------------
# Page: Geospatial analysis — map-led workspace
# ----------------------------------------------------------------------------
elif page == "Geospatial Analysis":
    section_title(
        "Map workspace",
        "Geospatial demand explorer",
        "A map-led view of historical stop demand, with route, period and stop-level analysis beside the map.",
    )

    gtfs_data = st.session_state.get("da012_gtfs_data_v4") or st.session_state.get("da012_gtfs_data_v3")
    with st.expander("Route geometry source · load official GTFS shapes", expanded=False):
        st.markdown(
            "Upload a CatTracks static GTFS ZIP or try the agency download. A usable `shapes.txt` linked through `trips.txt` is needed for actual route paths. "
            "The archived feed represents a later 2023+ network snapshot, not the exact 2018–19 alignments."
        )
        gtfs_upload = st.file_uploader(
            "Static GTFS ZIP", type=["zip"], key="geo_gtfs_upload_v4",
            help="Expected tables: routes.txt, stops.txt, trips.txt, stop_times.txt and ideally shapes.txt.",
        )
        fetch_col, status_col = st.columns([1, 2], vertical_alignment="center")
        with fetch_col:
            fetch_gtfs_clicked = st.button("Fetch official CatTracks feed", key="geo_fetch_gtfs_v4", type="primary")
        with status_col:
            if gtfs_data:
                shape_count = int(gtfs_data.get("shapes", pd.DataFrame()).groupby(["route_label", "shape_id"]).ngroups) if not gtfs_data.get("shapes", pd.DataFrame()).empty else 0
                st.caption(f"GTFS loaded · {len(gtfs_data['routes'])} routes · {len(gtfs_data['stops'])} stops · {shape_count} shape paths")
            else:
                st.caption("No GTFS geometry loaded. Historical demand mapping works independently.")
        if gtfs_upload is not None:
            try:
                gtfs_data = parse_gtfs_archive(gtfs_upload.getvalue())
                st.session_state["da012_gtfs_data_v4"] = gtfs_data
                st.success("GTFS archive loaded and parsed.")
            except Exception as exc:
                st.error(f"Could not parse this GTFS archive: {exc}")
        elif fetch_gtfs_clicked:
            try:
                with st.spinner("Downloading and parsing the official GTFS feed…"):
                    gtfs_data = fetch_current_gtfs()
                st.session_state["da012_gtfs_data_v4"] = gtfs_data
                st.success("Official GTFS feed loaded.")
            except Exception as exc:
                st.error(f"Automatic download failed: {exc}. Download a static GTFS ZIP from the official source and upload it here.")

    source_choice = st.radio(
        "Map workspace", ["Historical demand", "Current GTFS routes"],
        horizontal=True, key="geo_workspace_v4",
        help="Historical ridership is from 2018–19. The GTFS network is a later, separately dated reference.",
    )
    st.caption("Basemap is selected in the left sidebar. Standard OpenStreetMap is the default and needs no API key. Your map view is preserved when filters or basemap settings change.")

    if source_choice == "Historical demand":
        st.markdown(
            '<div class="plain-note"><strong>Historical data note:</strong> the 2018–19 workbooks contain stop labels and boarding totals, not coordinates or vector route geometry. Historical markers are approximate place/intersection matches. Current GTFS lines, if overlaid, are a later 2023+ reference.</div>',
            unsafe_allow_html=True,
        )
        location_path = DATA_DIR / "stop_locations_osm.csv"
        stop_names = sorted(ridership["stop"].dropna().unique().tolist())
        location_df = pd.DataFrame()
        matched_locations = pd.DataFrame()
        if location_path.exists():
            location_df = pd.read_csv(location_path)
            if {"stop", "latitude", "longitude", "status"}.issubset(location_df.columns):
                matched_locations = location_df[location_df["status"].eq("matched")].dropna(subset=["latitude", "longitude"]).copy()

        if matched_locations.empty:
            st.info("Historical stop locations are not cached on this computer yet. Resolve stop labels through OpenStreetMap to create approximate place/intersection locations.")
            if st.button("Locate historical stops with OpenStreetMap", type="primary", key="resolve_historical_names_v4"):
                try:
                    with st.spinner("Resolving stop names. Requests are rate-limited and successful matches are cached locally."):
                        geocode_historical_stops(stop_names, location_path)
                    st.rerun()
                except Exception as exc:
                    st.error(f"Geocoding failed: {exc}")
            st.link_button("Open the August 2019 official weekday route map", "https://planning.ucmerced.edu/sites/g/files/ufvvjh1431/f/page/documents/appendix_4.8_uc_merced_2020_lrdp_transportation_impact_analysis_rev.pdf")
        else:
            ctl1, ctl2, ctl3, ctl4 = st.columns([1.1, 1.08, 1.18, 1.15])
            with ctl1:
                route_options = ["All selected routes"] + [r for r in all_routes if r in selected_routes]
                route_choice = st.selectbox("Historical route", route_options, key="geo_hist_route_v4")
            with ctl2:
                periods_allowed = [p for p in all_periods if p in selected_periods]
                period_choice = st.selectbox("Billing period", ["Both selected periods"] + periods_allowed, key="geo_hist_period_v4")
            with ctl3:
                marker_options = ["Boardings in selection"] + periods_allowed
                marker_metric = st.selectbox("Demand metric", marker_options, key="geo_hist_metric_v4")
            with ctl4:
                demand_layer = st.selectbox("Demand layer", ["Demand bubbles", "Heatmap + bubbles", "Heatmap only"], key="geo_hist_layer_v5")

            map_frame = filtered.copy()
            if route_choice != "All selected routes":
                map_frame = map_frame[map_frame["route"].eq(route_choice)]
            if period_choice != "Both selected periods":
                map_frame = map_frame[map_frame["period"].eq(period_choice)]
            metric_frame = map_frame if marker_metric == "Boardings in selection" else map_frame[map_frame["period"].eq(marker_metric)]

            stop_demand = map_frame.groupby("stop", as_index=False)["passenger_count"].sum().rename(columns={"passenger_count": "recorded_boardings"})
            metric_demand = metric_frame.groupby("stop", as_index=False)["passenger_count"].sum().rename(columns={"passenger_count": "map_weight"})
            stop_demand = stop_demand.merge(metric_demand, on="stop", how="left").fillna({"map_weight": 0})
            map_points = stop_demand.merge(matched_locations, on="stop", how="inner")
            map_points["latitude"] = pd.to_numeric(map_points["latitude"], errors="coerce")
            map_points["longitude"] = pd.to_numeric(map_points["longitude"], errors="coerce")
            map_points = map_points.dropna(subset=["latitude", "longitude"])
            route_membership = map_frame.groupby("stop")["route"].apply(lambda x: sorted(set(x.astype(str)))).rename("routes").reset_index()
            map_points = map_points.merge(route_membership, on="stop", how="left")
            map_points["routes"] = map_points["routes"].apply(lambda value: value if isinstance(value, list) else [])

            if map_points.empty:
                st.warning("No mapped historical stops match these filters. Change the filters or review the geocoding cache.")
            else:
                selected_total = float(map_frame["passenger_count"].sum())
                mapped_total = float(map_points["recorded_boardings"].sum())
                coverage = (mapped_total / selected_total * 100) if selected_total else 0.0
                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Boardings in selection", fmt_num(selected_total))
                k2.metric("Mapped boardings", fmt_num(mapped_total))
                k3.metric("Location coverage", f"{coverage:.1f}%")
                k4.metric("Mapped stop labels", f"{map_points['stop'].nunique()} / {map_frame['stop'].nunique()}")

                current_route_labels = []
                overlay_routes = []
                show_gtfs_overlay = False
                shapes_df = gtfs_data.get("shapes", pd.DataFrame()) if gtfs_data else pd.DataFrame()
                if not shapes_df.empty:
                    current_route_labels = sorted(shapes_df["route_label"].dropna().astype(str).unique().tolist())
                    with st.expander("Optional overlay · current official GTFS lines (2023+)", expanded=False):
                        show_gtfs_overlay = st.checkbox("Overlay current GTFS route geometry", value=False, key="geo_overlay_on_v4")
                        if show_gtfs_overlay:
                            overlay_routes = st.multiselect("GTFS routes", current_route_labels, default=current_route_labels, key="geo_overlay_routes_v4")
                            st.caption("These are actual shapes from a later GTFS snapshot, not confirmed 2018–19 alignments.")

                toolbar_a, toolbar_b = st.columns([1.15, 5])
                viewport_key = "da012_hist_viewport_v5"
                map_component_key = "historical_demand_map_v5"
                with toolbar_a:
                    fit_visible = st.button("Fit visible stops", key="geo_fit_historical_v5", use_container_width=True)
                with toolbar_b:
                    st.caption(f"{len(map_points)} mapped stop labels · {fmt_num(mapped_total)} mapped boardings · {map_style_choice}")
                if fit_visible:
                    fit_center, fit_zoom = initial_map_view(map_points)
                    st.session_state[viewport_key] = {"center": fit_center, "zoom": fit_zoom}
                map_center, map_zoom = read_saved_viewport(viewport_key, map_points)

                map_col, analysis_col = st.columns([1.55, 1.0], gap="medium")
                with map_col:
                    fmap = base_map(location=map_center, zoom=map_zoom, map_style=map_style_choice)
                    bounds = []
                    drawn_shapes = 0
                    if show_gtfs_overlay and gtfs_data:
                        for (label, shape_id), shape in shapes_df.groupby(["route_label", "shape_id"], sort=False):
                            if label not in overlay_routes:
                                continue
                            ordered = shape.sort_values("shape_pt_sequence")
                            coords = list(zip(ordered["latitude"].astype(float), ordered["longitude"].astype(float)))
                            if len(coords) >= 2:
                                route_row = gtfs_data["routes"][gtfs_data["routes"]["route_label"].eq(label)].head(1)
                                raw = str(route_row.iloc[0].get("route_color", "")).strip().lstrip("#") if not route_row.empty else ""
                                color = "#" + raw if len(raw) == 6 and all(ch in "0123456789abcdefABCDEF" for ch in raw) else theme["accent"]
                                folium.PolyLine(coords, color=color, weight=5, opacity=.9, tooltip=f"{label} · current GTFS shape (2023+)").add_to(fmap)
                                bounds.extend(coords[::max(1, len(coords)//80)])
                                drawn_shapes += 1

                    heatmap_on = demand_layer in {"Heatmap + bubbles", "Heatmap only"}
                    markers_on = demand_layer in {"Demand bubbles", "Heatmap + bubbles"}
                    if heatmap_on:
                        heat_points = [[float(r.latitude), float(r.longitude), float(r.map_weight)] for r in map_points.itertuples() if float(r.map_weight) > 0]
                        if heat_points:
                            HeatMap(
                                heat_points,
                                name="Recorded boarding intensity",
                                radius=19,
                                blur=13,
                                min_opacity=.22,
                                max_zoom=16,
                                gradient={0.15: "#2878B5", 0.40: "#45B7A4", 0.68: "#F2C14E", 1.0: "#D94F45"},
                            ).add_to(fmap)

                    max_weight = max(float(map_points["map_weight"].max()), 1.0)
                    for row in map_points.itertuples():
                        lat, lon = float(row.latitude), float(row.longitude)
                        bounds.append([lat, lon])
                        if not markers_on:
                            continue
                        value = float(row.map_weight)
                        radius = 6.0 + 8.0 * math.sqrt(max(value, 0) / max_weight)
                        route_primary = row.routes[0] if row.routes else ""
                        color = ROUTE_COLORS.get(route_primary, theme["accent"])
                        selected_stop_name = st.session_state.get("geo_stop_choice_v5")
                        if selected_stop_name == row.stop:
                            color, radius = "#E5A93D", max(radius, 10)
                        popup = (
                            f"<div style='font-family:Arial;min-width:205px'><b>{html.escape(str(row.stop))}</b><br>"
                            f"Recorded boardings: <b>{float(row.recorded_boardings):,.0f}</b><br>"
                            f"Routes: {html.escape(', '.join(row.routes))}<br>"
                            "<small>Approximate place/intersection match; not a surveyed bus-stop pole.</small></div>"
                        )
                        folium.CircleMarker(
                            [lat, lon], radius=radius, color="#FFFFFF" if theme["bg"] == "#111418" else "#263342",
                            weight=1.5, fill=True, fill_color=color, fill_opacity=.88,
                            tooltip=f"{row.stop} · {value:,.0f} boardings",
                            popup=folium.Popup(popup, max_width=320),
                        ).add_to(fmap)

                    # on_change runs before Streamlit redraws the script. Saving the
                    # viewport here prevents zoom/pan from being overwritten by stale
                    # center/zoom values on the next run.
                    map_event = st_folium(
                        fmap,
                        use_container_width=True,
                        height=510,
                        center=map_center,
                        zoom=int(round(map_zoom)),
                        returned_objects=["last_object_clicked", "last_object_clicked_count", "center", "zoom"],
                        key=map_component_key,
                        on_change=persist_historical_map_viewport,
                    )
                    # Defensive fallback for versions that return state without callback.
                    save_map_viewport(viewport_key, map_event)
                    click = (map_event or {}).get("last_object_clicked")
                    click_count = (map_event or {}).get("last_object_clicked_count")
                    if click and click_count != st.session_state.get("geo_hist_click_count_v5"):
                        st.session_state["geo_hist_click_count_v5"] = click_count
                        nearest = closest_point(map_points, click)
                        if nearest is not None:
                            st.session_state["geo_stop_choice_v5"] = str(nearest["stop"])
                    st.caption(
                        "Heat intensity is weighted by recorded boardings; stop markers are approximate geocoder matches. "
                        + (f"{drawn_shapes} later GTFS route-shape paths are overlaid. " if drawn_shapes else "The historical Excel files do not contain vector route geometry. ")
                        + "Use Fit visible stops only when you want to recenter; map position is preserved across filters and basemap changes."
                    )

                with analysis_col:
                    st.markdown("### Route analytics")
                    route_total = float(map_frame["passenger_count"].sum())
                    route_stop_count = int(map_frame["stop"].nunique())
                    peak_total = float(map_frame.loc[map_frame["peak_status"].eq("Peak"), "passenger_count"].sum())
                    peak_share = peak_total / route_total * 100 if route_total else 0.0
                    st.metric("Recorded boardings", fmt_num(route_total))
                    metric_a, metric_b = st.columns(2)
                    metric_a.metric("Stops in selection", route_stop_count)
                    metric_b.metric("Peak share", f"{peak_share:.1f}%")

                    route_overview = map_frame.groupby("route", as_index=False)["passenger_count"].sum().sort_values("passenger_count", ascending=False)
                    route_fig = px.bar(
                        route_overview, x="route", y="passenger_count", color="route",
                        text_auto=".2s", color_discrete_map=ROUTE_COLORS,
                        labels={"route": "Route", "passenger_count": "Boardings"},
                    )
                    render_chart(chart_layout(route_fig, theme, height=185, legend=False), "geo_route_overview_v5")

                    st.markdown("### Stop inspector")
                    stop_options = map_points.sort_values("recorded_boardings", ascending=False)["stop"].astype(str).tolist()
                    selected_default = st.session_state.get("geo_stop_choice_v5")
                    if selected_default not in stop_options:
                        selected_default = stop_options[0]
                        st.session_state["geo_stop_choice_v5"] = selected_default
                    selected_stop = st.selectbox("Select a stop or click a map marker", stop_options, key="geo_stop_choice_v5")
                    selected_point = map_points[map_points["stop"].eq(selected_stop)].iloc[0]
                    selected_records = map_frame[map_frame["stop"].eq(selected_stop)].copy()
                    stop_total = float(selected_records["passenger_count"].sum())
                    st.metric("Selected-stop boardings", fmt_num(stop_total))
                    st.caption(f"Routes: {', '.join(sorted(selected_records['route'].astype(str).unique()))}")
                    st.caption(f"Approximate location: {float(selected_point['latitude']):.5f}, {float(selected_point['longitude']):.5f}")
                    stop_periods = selected_records.groupby("period", as_index=False)["passenger_count"].sum().rename(columns={"period": "Billing period", "passenger_count": "Boardings"})
                    st.dataframe(stop_periods, hide_index=True, use_container_width=True, height=115)

                # Balanced full-width analysis row beneath the map split. This removes
                # the large dead area under the shorter map column.
                st.markdown("### Demand patterns in the selected network")
                demand_col, hour_col = st.columns(2, gap="large")
                with demand_col:
                    period_route = map_frame.groupby(["period", "route"], as_index=False)["passenger_count"].sum().rename(columns={"period": "Billing period", "passenger_count": "Boardings"})
                    period_fig = px.bar(
                        period_route, x="Billing period", y="Boardings", color="route",
                        barmode="group", text_auto=".2s", color_discrete_map=ROUTE_COLORS,
                        labels={"Billing period": "Billing period", "Boardings": "Recorded boardings"},
                    )
                    st.markdown("**Boardings by billing period and route**")
                    render_chart(chart_layout(period_fig, theme, height=265), "geo_period_route_v5")
                with hour_col:
                    hour_route = map_frame.groupby(["departure_hour", "route"], as_index=False)["passenger_count"].sum()
                    hour_fig = px.line(
                        hour_route, x="departure_hour", y="passenger_count", color="route",
                        markers=True, color_discrete_map=ROUTE_COLORS,
                        labels={"departure_hour": "Scheduled departure hour", "passenger_count": "Boardings", "route": "Route"},
                    )
                    st.markdown("**Passenger demand by scheduled hour**")
                    render_chart(chart_layout(hour_fig, theme, height=265), "geo_hour_route_v5")

                with st.expander("Location quality, unmapped stops and downloads", expanded=False):
                    unmapped = sorted(set(map_frame["stop"].dropna().astype(str)) - set(map_points["stop"].dropna().astype(str)))
                    q1, q2 = st.columns(2)
                    q1.metric("Unmapped stop labels", len(unmapped))
                    q2.metric("Unmapped boardings", fmt_num(max(selected_total - mapped_total, 0)))
                    if unmapped:
                        st.caption("Not mapped: " + ", ".join(unmapped))
                    if not location_df.empty:
                        audit_cols = [c for c in ["stop", "status", "display_name", "query_used", "location_note"] if c in location_df.columns]
                        st.dataframe(location_df[audit_cols], hide_index=True, use_container_width=True)
                        st.download_button("Download geocoding audit CSV", location_df.to_csv(index=False).encode(), "da012_geocoding_audit.csv", "text/csv")
                    st.download_button("Download mapped demand CSV", map_points.to_csv(index=False).encode(), "da012_mapped_historical_demand.csv", "text/csv")

        st.markdown(
            "Source reference: [UC Merced August 2019 Transportation Impact Assessment — Figure 2, Weekday Bus Routes](https://planning.ucmerced.edu/sites/g/files/ufvvjh1431/f/page/documents/appendix_4.8_uc_merced_2020_lrdp_transportation_impact_analysis_rev.pdf) · [Transitland CatTracks GTFS archive](https://www.transit.land/data/feeds/f-cattracks~ca~us)"
        )

    else:
        st.markdown(
            '<div class="plain-note"><strong>Network date:</strong> these are actual route shapes and stop coordinates from the loaded GTFS snapshot, when <code>shapes.txt</code> is present. The archived CatTracks feed currently covers service from 2023 onward. It is not the same vintage as the 2018–19 ridership workbook.</div>',
            unsafe_allow_html=True,
        )
        if not gtfs_data:
            st.info("Load the official GTFS ZIP in the expander above to display real route paths and stop coordinates.")
            st.link_button("Open UC Merced official routes and schedules", "https://taps.ucmerced.edu/node/4656")
        else:
            routes_gtfs = gtfs_data["routes"].copy()
            stops_gtfs = gtfs_data["stops"].copy()
            shapes_gtfs = gtfs_data["shapes"].copy()
            route_labels_gtfs = sorted(routes_gtfs["route_label"].dropna().astype(str).unique().tolist())
            gtfs_ctl1, gtfs_ctl2, gtfs_ctl3 = st.columns([1.3, 1.3, 1.2])
            with gtfs_ctl1:
                gtfs_route_choice = st.selectbox("Route to inspect", ["All routes"] + route_labels_gtfs, key="geo_gtfs_route_v4")
            with gtfs_ctl2:
                show_gtfs_heat = st.checkbox("Highlight stop density", value=False, key="geo_gtfs_stop_heat_v4")
            with gtfs_ctl3:
                st.metric("Route paths available", int(shapes_gtfs.groupby(["route_label", "shape_id"]).ngroups) if not shapes_gtfs.empty else 0)

            chosen_gtfs_routes = route_labels_gtfs if gtfs_route_choice == "All routes" else [gtfs_route_choice]
            selected_gtfs_stops = stops_gtfs[stops_gtfs["served_by"].apply(lambda vals: any(v in chosen_gtfs_routes for v in vals))].copy()
            gtfs_map_col, gtfs_detail_col = st.columns([1.65, 1.0], gap="large")
            with gtfs_map_col:
                gtfs_viewport_key = "da012_gtfs_viewport_v5"
                if st.button("Fit selected GTFS route", key="geo_fit_gtfs_v5"):
                    fit_points = selected_gtfs_stops[["latitude", "longitude"]].copy()
                    if not shapes_gtfs.empty:
                        fit_shapes = shapes_gtfs[shapes_gtfs["route_label"].isin(chosen_gtfs_routes)][["latitude", "longitude"]]
                        fit_points = pd.concat([fit_points, fit_shapes], ignore_index=True)
                    fit_center, fit_zoom = initial_map_view(fit_points)
                    st.session_state[gtfs_viewport_key] = {"center": fit_center, "zoom": fit_zoom}
                gtfs_center, gtfs_zoom = read_saved_viewport(gtfs_viewport_key, selected_gtfs_stops)
                fmap = base_map(location=gtfs_center, zoom=gtfs_zoom, map_style=map_style_choice)
                bounds = []
                drawn_shapes = 0
                if not shapes_gtfs.empty:
                    for (label, shape_id), shape in shapes_gtfs.groupby(["route_label", "shape_id"], sort=False):
                        if label not in chosen_gtfs_routes:
                            continue
                        ordered = shape.sort_values("shape_pt_sequence")
                        coords = list(zip(ordered["latitude"].astype(float), ordered["longitude"].astype(float)))
                        if len(coords) >= 2:
                            route_row = routes_gtfs[routes_gtfs["route_label"].eq(label)].head(1)
                            raw = str(route_row.iloc[0].get("route_color", "")).strip().lstrip("#") if not route_row.empty else ""
                            color = "#" + raw if len(raw) == 6 and all(ch in "0123456789abcdefABCDEF" for ch in raw) else theme["accent"]
                            folium.PolyLine(coords, color=color, weight=5.5, opacity=.92, tooltip=f"{label} · official GTFS shape", smooth_factor=1.5).add_to(fmap)
                            bounds.extend(coords[::max(1, len(coords)//80)])
                            drawn_shapes += 1
                if show_gtfs_heat and not selected_gtfs_stops.empty:
                    heat = [[float(row.latitude), float(row.longitude), 1.0] for row in selected_gtfs_stops.itertuples()]
                    HeatMap(heat, radius=24, blur=18, min_opacity=.18).add_to(fmap)
                for row in selected_gtfs_stops.itertuples():
                    served = [name for name in row.served_by if name in chosen_gtfs_routes]
                    folium.CircleMarker(
                        [float(row.latitude), float(row.longitude)], radius=5,
                        color=theme["surface"], weight=1.6, fill=True,
                        fill_color=theme["accent"], fill_opacity=.95,
                        tooltip=f"{row.stop_name} · {', '.join(served)}",
                        popup=folium.Popup(f"<b>{html.escape(str(row.stop_name))}</b><br>Routes: {html.escape(', '.join(served))}<br>GTFS stop ID: {html.escape(str(row.stop_id))}", max_width=330),
                    ).add_to(fmap)
                    bounds.append([float(row.latitude), float(row.longitude)])
                gtfs_event = st_folium(
                    fmap,
                    use_container_width=True,
                    height=510,
                    center=gtfs_center,
                    zoom=int(round(gtfs_zoom)),
                    returned_objects=["last_object_clicked", "last_object_clicked_count", "center", "zoom"],
                    key="gtfs_route_map_v5",
                    on_change=persist_gtfs_map_viewport,
                )
                save_map_viewport(gtfs_viewport_key, gtfs_event)
                click = (gtfs_event or {}).get("last_object_clicked")
                click_count = (gtfs_event or {}).get("last_object_clicked_count")
                if click and click_count != st.session_state.get("geo_gtfs_click_count_v5"):
                    st.session_state["geo_gtfs_click_count_v5"] = click_count
                    nearest = closest_point(selected_gtfs_stops, click)
                    if nearest is not None:
                        st.session_state["geo_gtfs_stop_choice_v5"] = str(nearest["stop_id"])
                st.caption("Solid coloured lines are actual GTFS route shapes. Stop coordinates and route sequence come from the same dated snapshot.")

            with gtfs_detail_col:
                st.markdown("### Route inspector")
                route_detail = routes_gtfs[routes_gtfs["route_label"].isin(chosen_gtfs_routes)]
                st.metric("Routes selected", len(route_detail))
                st.metric("Stops shown", len(selected_gtfs_stops))
                st.metric("Shape paths drawn", drawn_shapes)
                if not selected_gtfs_stops.empty:
                    stop_lookup = selected_gtfs_stops.set_index("stop_id")["stop_name"].astype(str).to_dict()
                    ids = selected_gtfs_stops["stop_id"].astype(str).tolist()
                    current_id = st.session_state.get("geo_gtfs_stop_choice_v5")
                    if current_id not in ids:
                        current_id = ids[0]
                        st.session_state["geo_gtfs_stop_choice_v5"] = current_id
                    chosen_id = st.selectbox("Inspect a GTFS stop", ids, index=ids.index(current_id), format_func=lambda value: stop_lookup.get(value, value), key="geo_gtfs_stop_choice_v5")
                    chosen_row = selected_gtfs_stops[selected_gtfs_stops["stop_id"].astype(str).eq(str(chosen_id))].iloc[0]
                    st.markdown(f"**{chosen_row['stop_name']}**")
                    st.caption(f"Stop ID: {chosen_id} · Routes: {', '.join(chosen_row['served_by'])}")
                    st.caption(f"Coordinates: {float(chosen_row['latitude']):.5f}, {float(chosen_row['longitude']):.5f}")
                    route_stop_table = gtfs_data.get("route_stops", pd.DataFrame())
                    if gtfs_route_choice != "All routes" and not route_stop_table.empty:
                        ordered_stops = route_stop_table[route_stop_table["route_label"].eq(gtfs_route_choice)].sort_values("stop_sequence")
                        st.markdown("**Stops in scheduled sequence**")
                        st.dataframe(ordered_stops[["stop_sequence", "stop_name"]].drop_duplicates(), hide_index=True, use_container_width=True, height=220)
                service = gtfs_data.get("service_range", pd.DataFrame())
                service_text = "not specified" if service.empty else f"{service.iloc[0]['start']} – {service.iloc[0]['end']}"
                st.caption(f"GTFS calendar: {service_text}")
                st.caption("Source: [UC Merced TAPS](https://taps.ucmerced.edu/node/4656) · [Transitland](https://www.transit.land/data/feeds/f-cattracks~ca~us)")
                if drawn_shapes == 0:
                    st.warning("No linked shapes.txt geometry is available for this selection. GTFS stop locations remain usable, but route paths cannot be drawn from this feed.")

# ----------------------------------------------------------------------------
# Page: Data explorer
# ----------------------------------------------------------------------------
elif page == "Data Explorer":
    section_title("Records", "Data explorer", "Search the cleaned analytical table and export the rows selected by the global filters.")
    c1, c2, c3 = st.columns([1.5, 1, 1])
    with c1:
        query = st.text_input("Search stop name", placeholder="e.g. Muir Pass")
    with c2:
        min_count = st.number_input("Minimum boardings", min_value=0, max_value=int(filtered["passenger_count"].max()), value=0, step=10)
    with c3:
        sorting = st.selectbox("Sort by", ["Highest boardings", "Lowest boardings", "Route / stop"])
    table = filtered.copy()
    if query.strip():
        table = table[table["stop"].str.contains(query.strip(), case=False, na=False)]
    table = table[table["passenger_count"] >= min_count]
    if sorting == "Highest boardings":
        table = table.sort_values("passenger_count", ascending=False)
    elif sorting == "Lowest boardings":
        table = table.sort_values("passenger_count", ascending=True)
    else:
        table = table.sort_values(["route", "stop", "departure_minutes"])
    st.caption(f"{len(table):,} records shown from {len(filtered):,} rows in the current filter selection.")
    display_cols = ["period", "route", "stop", "departure_time", "passenger_count", "time_band", "peak_status", "source_workbook"]
    st.dataframe(table[display_cols], hide_index=True, use_container_width=True, height=500, column_config={"passenger_count": st.column_config.NumberColumn("Boardings", format="%.0f"), "source_workbook": st.column_config.TextColumn("Source workbook", width="large")})
    st.download_button("Download filtered CSV", table.to_csv(index=False).encode("utf-8"), "da012_filtered_ridership.csv", "text/csv")
    with st.expander("Data quality report"):
        st.dataframe(quality_report(ridership), hide_index=True, use_container_width=True)

# ----------------------------------------------------------------------------
# Page: Project team
# ----------------------------------------------------------------------------
elif page == "Project Team":
    section_title("People", "Project team", "B.Tech · Semester III · Section F · Group BTech_DA_08")
    st.markdown('<div class="plain-note"><strong>Project lead:</strong> Mohd. Shoaib. Individual responsibilities will be added once the group confirms its work allocation.</div>', unsafe_allow_html=True)
    a, b, c, d = st.columns(4)
    a.metric("Project ID", "DA-012")
    b.metric("Group ID", "BTech_DA_08")
    c.metric("Team size", "11")
    d.metric("Mentor", "Puneet Arora")
    public_path = DATA_DIR / "team_members.csv"
    private_path = DATA_DIR / "team_members_private.csv"
    if private_path.exists():
        roster = pd.read_csv(private_path)
        cols = [c for c in ["serial_no", "name", "role", "student_id", "roll_no"] if c in roster.columns]
        labels = {"serial_no": "No.", "name": "Student name", "role": "Project role", "student_id": "Student ID", "roll_no": "Roll number"}
        st.caption("Academic identifiers are read from a local-only file and are not included in the public roster.")
    elif public_path.exists():
        roster = pd.read_csv(public_path)
        cols = [c for c in ["serial_no", "name", "role"] if c in roster.columns]
        labels = {"serial_no": "No.", "name": "Student name", "role": "Project role"}
    else:
        roster, cols, labels = pd.DataFrame(), [], {}
    if not roster.empty:
        roster["_order"] = roster["role"].map(lambda value: 0 if value == "Project Lead" else 1)
        roster = roster.sort_values(["_order", "serial_no"]).drop(columns="_order")
        st.dataframe(roster[cols].rename(columns=labels), hide_index=True, use_container_width=True)
    st.markdown("#### Academic details")
    st.write("**University:** Invertis University, Bareilly  ·  **Programme:** B.Tech CSE  ·  **Semester:** III  ·  **Section:** F  ·  **Mentor:** Puneet Arora")
    st.caption("The local private roster file is excluded from Git. Obtain consent before publishing member names; never publish student IDs or roll numbers in a public repository.")

# ----------------------------------------------------------------------------
# Page: Methodology
# ----------------------------------------------------------------------------
elif page == "Methodology":
    section_title("Documentation", "Methodology & sources", "How the dataset is prepared, what the metrics mean, and where the evidence comes from.")
    l, r = st.columns(2)
    with l:
        st.markdown("#### Data workflow")
        st.markdown("1. Read the October 2018 and February 2019 Excel workbooks.\n2. Extract aggregate PAX ON tables for four weekday routes.\n3. Standardise stop labels and departure times.\n4. Validate missing, negative and duplicate observations.\n5. Aggregate counts by route, stop, time and billing period.\n6. Visualise and interpret historical recorded boardings.")
        st.markdown("#### Definitions")
        st.markdown("- **Boarding:** a recorded PAX ON count.\n- **Peak:** scheduled departures 07:00–09:59 and 16:00–18:59.\n- **Off-peak:** all other scheduled departures.\n- **Time band:** a project grouping of scheduled departure times.")
    with r:
        st.markdown("#### Limitations")
        st.markdown("- Historical aggregate counts are not individual passenger records.\n- Only four weekday route worksheets are analysed.\n- Billing-period totals are not normalised by service days.\n- The source workbooks do not provide coordinates or vector route geometry.\n- Geocoded historical stop labels are approximate place/intersection matches.\n- Current GTFS is a later network snapshot, not the 2018–19 network.")
        st.markdown("#### Sources")
        st.markdown("- [Original UCM CatTracks Simulator](https://github.com/nlt-python/UCM_CatTracks_Simulator)\n- [UC Merced 2019 Transportation Impact Assessment](https://planning.ucmerced.edu/sites/g/files/ufvvjh1431/f/page/documents/appendix_4.8_uc_merced_2020_lrdp_transportation_impact_analysis_rev.pdf)\n- [UC Merced TAPS routes](https://taps.ucmerced.edu/node/4656)\n- [Transitland CatTracks feed archive](https://www.transit.land/data/feeds/f-cattracks~ca~us)\n- [OpenStreetMap Nominatim](https://nominatim.org/release-docs/latest/api/Overview/)")
    st.info("The application is a descriptive historical analysis. It is not a live transit tracker, passenger-level model, or service-performance audit.")

st.markdown(
    '<div class="footer-line"><span>DA-012 · Public Transport Ridership Analysis · Invertis University</span>'
    '<span>Project lead: <strong>Mohd. Shoaib</strong> · Python · Pandas · Plotly · Streamlit</span></div>',
    unsafe_allow_html=True,
)
