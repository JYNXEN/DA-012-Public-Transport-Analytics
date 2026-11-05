# DA-012 Streamlit Dashboard Guide

## Start the dashboard

From the project root, activate the virtual environment and install the complete requirements (including the map packages):

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL printed in Terminal (normally `http://localhost:8501`). The dashboard runs on your own computer. Keep the Terminal process running while using it; press `Control + C` in that Terminal window to stop it.

## Dashboard sections

- **Overview:** KPI cards, automatically generated insights, route demand comparison and route share.
- **Routes & stops:** busiest stop rankings, route comparisons and peak/off-peak charts.
- **Time patterns:** scheduled departure trends, time-of-day summaries and route-by-hour heatmap.
- **Geospatial analysis:** the default map-led workspace, with a boarding-weighted historical heatmap, clickable stops, route/stop analytics split view, map appearance controls, and actual GTFS route shapes when available.
- **Data explorer:** search, sort, filter and export the currently selected ridership records.
- **Project team:** project ID, group ID, mentor, 11-person roster, and locally stored student IDs/roll numbers if the private file is present.
- **Methodology:** definitions, source attribution and limitations.

## Geospatial map workspace

The application now opens on **Geospatial Analysis**, and its main view is a map + analytics split layout. The map is the primary surface; charts and stop-level detail update beside it.

### Historical demand map

1. Choose **Historical demand**.
2. Select one historical route or all selected routes, and choose one or both billing periods.
3. Choose whether marker size represents all selected boardings or a single selected billing period.
4. Toggle **Show demand heatmap** to display a boarding-weighted intensity layer.
5. Press **Locate historical stops with OpenStreetMap** when the local coordinate cache does not exist. This calls the public Nominatim geocoder and stores successful results in `data/stop_locations_osm.csv`. Requests are throttled to at least 1.1 seconds apart and the cache is reused later.
6. Click a marker or select a stop in the right-hand **Stop inspector**. The period comparison, route contribution table, and scheduled-hour chart update for that stop.
7. Use **Map appearance** to switch between theme-matched, dark, light, and standard OpenStreetMap tiles.

Historical geocoder results may identify a named place or nearby intersection rather than the exact bus-stop pole. The source workbooks contain no coordinates or vector route geometry.

### Actual route lines from a GTFS snapshot

1. Expand **Route geometry source · load official GTFS shapes**.
2. Press **Fetch official CatTracks feed**, or upload the static GTFS ZIP.
3. In **Historical demand**, optionally enable **Show real GTFS route lines on this historical demand map**. This creates a combined view of historical demand points and the later route network, with the date mismatch labelled.
4. Choose **Current GTFS routes** to see only the current network. Select an individual route, click its stops, and inspect the stop sequence in the right panel.
5. If the feed contains no linked `shapes.txt`, stop markers can still appear, but the app will not invent line geometry.

Transitland's archived CatTracks feed snapshot currently lists service beginning 2023-08-15; it is therefore a later network reference, not the exact 2018–19 network. Keep the date distinction in the report and viva.

The current GTFS layer is a separately dated reference network. Never describe it as the exact route geometry used in the historic billing workbooks without a matching historic feed.

## Team roster and student identifiers

- `data/team_members.csv` contains the public roster (names and roles only).
- `data/team_members_private.csv` contains student IDs and roll numbers for local academic use. This file is listed in `.gitignore`.
- Do not force-add the private file to a public Git repository. Confirm consent before publishing team members' names.

## Interpretation notes

The dashboard analyses aggregate `PAX ON` counts for four weekday routes across October 2018 and February 2019. Boardings are not unique passengers. Peak windows (07:00–09:59 and 16:00–18:59) are project assumptions, not official operator classifications. Billing-period totals are not normalised by operating days and should not be represented as a growth rate. This is a historical descriptive analysis, not a live transit feed or passenger-level forecasting system.

## Upstream attribution

Adapted from [UCM CatTracks Simulator](https://github.com/nlt-python/UCM_CatTracks_Simulator). Keep `NOTICE.md`, `LICENSE`, and `upstream_reference/` with the project.

## Updated app navigation and map interactions

The application now uses the **left sidebar** for page navigation and global filters. Use the **Dark / Light** control in the sidebar to switch the interface, Plotly charts and map basemap together.

The **Geospatial Analysis** page offers two distinct map datasets:

- **Historical demand points · 2018–19:** approximate OpenStreetMap geocoder matches joined to the historical boarding counts. Click a marker to inspect its stop-level period and route comparison. These points are not surveyed stop poles, and historical route polylines are not inferred from the Excel source.
- **Current network · GTFS:** upload or fetch a static GTFS ZIP. Actual route paths are drawn from `shapes.txt` only when those shapes are linked to trips in the feed. Its service dates are shown separately from the 2018–19 ridership periods.


## Map stability and sidebar filter update

- Expand **Global filters** in the left sidebar to open the billing-period checkboxes, route selectors, time-of-day bands, demand classes and departure-hour range. Billing periods are checkboxes, not a popover or dropdown.
- Expand **Map appearance** separately to choose a basemap and, optionally, paste a free CARTO non-commercial API key. Standard OpenStreetMap remains the default and works without a key.
- The map centre and zoom are saved in the `st_folium` `on_change` callback before Streamlit redraws the application. Both historical and GTFS map views use fixed component keys and keep the last viewport. Use **Fit visible stops** / **Fit selected GTFS route** only when you intentionally want to reframe.
- Plotly wheel and drag zoom remain disabled to avoid accidental chart zooming; hover tooltips remain available.
- The historical map is shorter and sits beside a compact route/stop inspector. A full-width demand-pattern section follows the map split, reducing blank space beneath the map.

### Optional CARTO API key

CARTO's current free non-commercial tier allows up to 5 million map-tile requests per calendar month. Request a key at <https://www.carto.com/basemaps/apikey/>. Paste it into the password field under **Map appearance** to enable CARTO Positron (light), Dark Matter (dark) and Voyager. The key is stored in the current local Streamlit session only. For persistent local use, create `.streamlit/secrets.toml` with `CARTO_API_KEY = "your-key"`; this file is ignored by Git.

Standard OpenStreetMap tiles require no key. Keep the visible attribution and follow the [OSM tile usage policy](https://operations.osmfoundation.org/policies/tiles/)—normal interactive viewing only, no bulk downloading or prefetching.

See `MAP_TROUBLESHOOTING.md`.
