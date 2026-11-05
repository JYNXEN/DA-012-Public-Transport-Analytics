"""Geospatial helpers for DA-012 CatTracks analysis.

Historical stop labels are geocoded on demand with OpenStreetMap Nominatim.
The current route layer is parsed from the official UC Merced/RideSystems GTFS
static feed. These layers are deliberately kept separate because the ridership
workbooks are from 2018-19 while the public GTFS snapshot begins in 2023.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import time
import zipfile
from typing import Iterable

import pandas as pd
import requests

CATTRACKS_GTFS_URL = (
    "https://cattracks.ridesystems.net/Secure/Admin/Reports/GTFSDownload.aspx"
)
GTFS_USER_AGENT = "DA-012-CatTracks-Student-Analytics/1.0"
NOMINATIM_USER_AGENT = "DA-012-CatTracks-Academic-Project/1.0"

# Search phrases give the geocoder useful Merced/UC Merced context. A geocoder
# hit is a place/intersection estimate, not proof of the exact bus-pole location.
STOP_QUERY_OVERRIDES = {
    '"G" St & Alexander': "G Street and Alexander Avenue, Merced, California, USA",
    "Alexander & G Street": "G Street and Alexander Avenue, Merced, California, USA",
    "Amtrak": "Merced Amtrak Station, 324 W 24th Street, Merced, California, USA",
    "Arrow Wood Drive": "Arrow Wood Drive, Merced, California, USA",
    "Buena Vista": "Buena Vista, Merced, California, USA",
    "Cardella & M St.": "Cardella Road and M Street, Merced, California, USA",
    "Compass Pointe": "Axis at Compass Pointe, 3779 Horizon Avenue, Merced, California, USA",
    "El Portal Plaza": "El Portal, UC Merced, Merced, California, USA",
    "El Portal Plaza / G Street": "El Portal, G Street, Merced, California, USA",
    "El Redondo": "El Redondo, Merced, California, USA",
    "Granville Apts": "Granville Apartments, Merced, California, USA",
    "Ironstone": "Ironstone Drive, Merced, California, USA",
    "K 18th+19th": "K Street between 18th Street and 19th Street, Merced, California, USA",
    "Meadows/Olivewood": "Meadows Avenue and Olivewood Drive, Merced, California, USA",
    "Merced College": "Merced College, 3600 M Street, Merced, California, USA",
    "Merced Mall Target": "Target, 3280 R Street, Merced, California, USA",
    "Mercy Hospital": "Dignity Health Mercy Medical Center, 333 Mercy Avenue, Merced, California, USA",
    "Muir Pass": "Muir Pass, UC Merced, Merced, California, USA",
    "Rite Aid/Walgreen": "Rite Aid Walgreens, G Street, Merced, California, USA",
    "Scholars/Emigrant": "Scholars Lane and Emigrant Pass, UC Merced, Merced, California, USA",
    "Tri College/Mercy": "Tri College Mercy Hospital bus stop, Merced, California, USA",
    "TriCol/Mercy Hospital": "Tri College Mercy Hospital bus stop, Merced, California, USA",
    'Village Apts "R" Street': "R Street Village Apartments, Merced, California, USA",
    'Villages Apts "M"': "Village Apartments M Street, Merced, California, USA",
    "Walmart": "Walmart, Loughborough Drive, Merced, California, USA",
}


def geocode_historical_stops(
    stop_names: Iterable[str],
    output_csv: str | Path,
    *,
    min_delay_seconds: float = 1.1,
) -> pd.DataFrame:
    """Resolve historical stop labels using Nominatim and persist a local cache.

    Calls are throttled to respect the public Nominatim service's one-request-
    per-second usage policy. Existing successful rows are reused on later runs.
    """
    try:
        from geopy.geocoders import Nominatim
        from geopy.extra.rate_limiter import RateLimiter
    except ImportError as exc:  # pragma: no cover - depends on local installation
        raise RuntimeError("Install geopy with: python -m pip install geopy") from exc

    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    if output_csv.exists():
        cached = pd.read_csv(output_csv)
    else:
        cached = pd.DataFrame(columns=[
            "stop", "query_used", "latitude", "longitude", "display_name",
            "geocoder", "status", "location_note",
        ])

    existing = {
        str(row["stop"]): row
        for _, row in cached.iterrows()
        if str(row.get("status", "")) == "matched"
        and pd.notna(row.get("latitude"))
        and pd.notna(row.get("longitude"))
    }
    geolocator = Nominatim(user_agent=NOMINATIM_USER_AGENT, timeout=20)
    geocode = RateLimiter(
        geolocator.geocode,
        min_delay_seconds=max(1.05, float(min_delay_seconds)),
        max_retries=0,
        swallow_exceptions=True,
        return_value_on_exception=None,
    )

    records = []
    for stop in dict.fromkeys(str(name).strip() for name in stop_names if str(name).strip()):
        if stop in existing:
            records.append(existing[stop].to_dict())
            continue
        query = STOP_QUERY_OVERRIDES.get(stop, f"{stop}, Merced, California, USA")
        location = geocode(query, exactly_one=True, country_codes="us", addressdetails=True)
        if location is None:
            records.append({
                "stop": stop,
                "query_used": query,
                "latitude": None,
                "longitude": None,
                "display_name": None,
                "geocoder": "OpenStreetMap Nominatim",
                "status": "not found",
                "location_note": "No result; do not plot until manually verified.",
            })
        else:
            records.append({
                "stop": stop,
                "query_used": query,
                "latitude": float(location.latitude),
                "longitude": float(location.longitude),
                "display_name": str(location.address),
                "geocoder": "OpenStreetMap Nominatim",
                "status": "matched",
                "location_note": "Geocoded place/intersection estimate; verify against the 2019 route map.",
            })

    result = pd.DataFrame(records)
    result.to_csv(output_csv, index=False)
    return result


def read_gtfs_table(archive: zipfile.ZipFile, filename: str) -> pd.DataFrame:
    """Read one optional CSV table from a GTFS ZIP archive."""
    names = {name.rsplit("/", 1)[-1]: name for name in archive.namelist()}
    if filename not in names:
        return pd.DataFrame()
    with archive.open(names[filename]) as file_obj:
        return pd.read_csv(file_obj, dtype=str, keep_default_na=False)


def parse_gtfs_archive(zip_bytes: bytes) -> dict[str, pd.DataFrame]:
    """Parse routes, shapes, stops and route-stop relationships from GTFS ZIP."""
    try:
        archive = zipfile.ZipFile(BytesIO(zip_bytes))
    except zipfile.BadZipFile as exc:
        raise ValueError("The selected file is not a valid GTFS ZIP archive.") from exc

    with archive:
        routes = read_gtfs_table(archive, "routes.txt")
        stops = read_gtfs_table(archive, "stops.txt")
        shapes = read_gtfs_table(archive, "shapes.txt")
        trips = read_gtfs_table(archive, "trips.txt")
        stop_times = read_gtfs_table(archive, "stop_times.txt")
        calendar = read_gtfs_table(archive, "calendar.txt")
        calendar_dates = read_gtfs_table(archive, "calendar_dates.txt")

    required = {"route_id"}
    if routes.empty or not required.issubset(routes.columns):
        raise ValueError("GTFS archive is missing a usable routes.txt file.")
    for column in ["stop_id", "stop_name", "stop_lat", "stop_lon"]:
        if column not in stops.columns:
            raise ValueError(f"GTFS archive is missing stops.txt column {column!r}.")
    if trips.empty or not {"trip_id", "route_id"}.issubset(trips.columns):
        raise ValueError("GTFS archive is missing a usable trips.txt file.")
    if stop_times.empty or not {"trip_id", "stop_id", "stop_sequence"}.issubset(stop_times.columns):
        raise ValueError("GTFS archive is missing a usable stop_times.txt file.")

    route_name_columns = [c for c in ["route_short_name", "route_long_name"] if c in routes.columns]
    if route_name_columns:
        routes = routes.copy()
        routes["route_label"] = routes[route_name_columns].fillna("").apply(
            lambda row: " · ".join(str(v).strip() for v in row if str(v).strip()), axis=1
        )
    else:
        routes = routes.copy()
        routes["route_label"] = routes["route_id"].astype(str)
    routes.loc[routes["route_label"].eq(""), "route_label"] = routes["route_id"]

    numeric_stops = stops.copy()
    numeric_stops["latitude"] = pd.to_numeric(numeric_stops["stop_lat"], errors="coerce")
    numeric_stops["longitude"] = pd.to_numeric(numeric_stops["stop_lon"], errors="coerce")
    numeric_stops = numeric_stops.dropna(subset=["latitude", "longitude"])

    trips_routes = trips[["trip_id", "route_id"]].drop_duplicates()
    stop_route = stop_times[["trip_id", "stop_id"]].merge(trips_routes, on="trip_id", how="left")
    stop_route = stop_route.merge(routes[["route_id", "route_label"]], on="route_id", how="left")
    stop_routes = (
        stop_route.groupby("stop_id")["route_label"]
        .apply(lambda values: sorted(set(v for v in values if isinstance(v, str) and v)))
        .rename("served_by")
        .reset_index()
    )
    numeric_stops = numeric_stops.merge(stop_routes, on="stop_id", how="left")
    numeric_stops["served_by"] = numeric_stops["served_by"].apply(lambda x: x if isinstance(x, list) else [])

    # Preserve route-stop order for the route inspector in the dashboard.
    route_stops = stop_times[["trip_id", "stop_id", "stop_sequence"]].merge(
        trips_routes, on="trip_id", how="left"
    )
    route_stops = route_stops.merge(routes[["route_id", "route_label"]], on="route_id", how="left")
    route_stops = route_stops.merge(
        numeric_stops[["stop_id", "stop_name"]].drop_duplicates("stop_id"),
        on="stop_id", how="left"
    )
    route_stops["stop_sequence"] = pd.to_numeric(route_stops["stop_sequence"], errors="coerce")
    route_stops = (
        route_stops.dropna(subset=["route_label", "stop_sequence"])
        .sort_values(["route_label", "stop_sequence", "stop_name"])
        .drop_duplicates(["route_label", "stop_id", "stop_sequence"])
        .reset_index(drop=True)
    )

    shape_rows = pd.DataFrame()
    if not shapes.empty and {"shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence"}.issubset(shapes.columns) and "shape_id" in trips.columns:
        shape_routes = trips[["route_id", "shape_id"]].dropna().drop_duplicates()
        shape_routes = shape_routes[shape_routes["shape_id"].astype(str).str.strip().ne("")]
        shape_rows = shapes.merge(shape_routes, on="shape_id", how="inner")
        shape_rows = shape_rows.merge(routes[["route_id", "route_label"]], on="route_id", how="left")
        shape_rows["latitude"] = pd.to_numeric(shape_rows["shape_pt_lat"], errors="coerce")
        shape_rows["longitude"] = pd.to_numeric(shape_rows["shape_pt_lon"], errors="coerce")
        shape_rows["shape_pt_sequence"] = pd.to_numeric(shape_rows["shape_pt_sequence"], errors="coerce")
        shape_rows = shape_rows.dropna(subset=["latitude", "longitude", "shape_pt_sequence"])
        shape_rows = shape_rows.sort_values(["route_label", "shape_id", "shape_pt_sequence"])

    service_dates = []
    for frame, cols in [
        (calendar, ["start_date", "end_date"]),
        (calendar_dates, ["date"]),
    ]:
        for col in cols:
            if col in frame.columns:
                service_dates.extend(frame[col].astype(str).tolist())
    service_dates = [d for d in service_dates if len(d) == 8 and d.isdigit()]
    service_range = None
    if service_dates:
        service_range = (min(service_dates), max(service_dates))

    return {
        "routes": routes,
        "stops": numeric_stops,
        "route_stops": route_stops,
        "shapes": shape_rows,
        "service_range": pd.DataFrame([{"start": service_range[0], "end": service_range[1]}]) if service_range else pd.DataFrame(),
    }


def fetch_current_gtfs(url: str = CATTRACKS_GTFS_URL, timeout: int = 45) -> dict[str, pd.DataFrame]:
    """Fetch and parse the public official current CatTracks GTFS ZIP."""
    response = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": GTFS_USER_AGENT, "Accept": "application/zip,application/octet-stream,*/*"},
    )
    response.raise_for_status()
    content_type = response.headers.get("Content-Type", "").lower()
    if "html" in content_type and not response.content.startswith(b"PK"):
        raise ValueError(
            "The CatTracks download endpoint returned an HTML page instead of a GTFS ZIP. "
            "Download the GTFS ZIP from the official route data source and upload it below."
        )
    return parse_gtfs_archive(response.content)
