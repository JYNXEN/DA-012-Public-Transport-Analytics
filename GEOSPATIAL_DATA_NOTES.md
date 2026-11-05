# DA-012 geospatial data notes

## Why the dashboard has two map layers

The project ridership workbooks contain aggregate passenger boarding tables for October 2018 and February 2019. Those worksheets provide stop names and departure-time counts, but they do not contain latitude/longitude or route-shape geometries.

The dashboard therefore keeps historical ridership context separate from a newer GTFS network reference. This avoids drawing a modern route as though it were the exact route used in 2018–19.

## 1. Historical route context — August 2019

Source: **UC Merced 2020 LRDP Transportation Impact Analysis**, prepared by Fehr & Peers for UC Merced, August 2019. Figure 2 is titled *Weekday Bus Routes*.

Official report:

https://planning.ucmerced.edu/sites/g/files/ufvvjh1431/f/page/documents/appendix_4.8_uc_merced_2020_lrdp_transportation_impact_analysis_rev.pdf

The report describes the historical weekday corridors:

- **C1:** campus, retail along W Olive Avenue and G Street, and Granville Apartments.
- **C2:** campus, Merced College, retail along Yosemite Avenue and Loughborough Drive, and multiple housing locations.
- **G:** campus, downtown Merced and Amtrak along O and K Streets.

The ridership workbook uses labels C1 Blue, C1 Gold, C2 Express and G-Line. The report's corridor descriptions are historical context, not proof that each workbook label has an identical stop sequence or geometry. The assessment's figure is a visual map, not a downloadable vector route layer. This project does not reconstruct historical route polylines from that image.

## 2. Historical stop-demand points

The historical map uses the stop names in the workbook and resolves them with OpenStreetMap Nominatim only after the user presses **Locate historical stops with OpenStreetMap**.

- Requests are rate-limited to at least 1.1 seconds apart.
- Successful matches are cached in `data/stop_locations_osm.csv`.
- This cache is local and listed in `.gitignore`.
- A geocoder result may refer to a place, building, or nearby intersection. It is not a surveyed bus-stop pole coordinate.
- Review `display_name`, `query_used` and `location_note` in the map's geocoding-results expander. Manually verify important locations against the official 2019 map before using them to support a route-planning recommendation.

The map marker size represents the recorded boarding counts after the dashboard's selected filters. It is a visual encoding of the ridership data, not a measurement of physical congestion or stop capacity.

## 3. Current GTFS reference network

The dashboard can fetch the public CatTracks static GTFS ZIP from the agency download endpoint, or accept a GTFS ZIP uploaded by the user. It parses:

- `routes.txt` — route identifiers and names;
- `stops.txt` — stop names and coordinates;
- `trips.txt` and `stop_times.txt` — route-to-stop relationships;
- `shapes.txt` — route shape coordinates, when supplied;
- `calendar.txt` and `calendar_dates.txt` — service-date range, when supplied.

Current source pages:

- UC Merced TAPS routes: https://taps.ucmerced.edu/node/4656
- Transitland CatTracks feed archive: https://www.transit.land/data/feeds/f-cattracks~ca~us
- Agency GTFS download endpoint: https://cattracks.ridesystems.net/Secure/Admin/Reports/GTFSDownload.aspx

The Transitland feed snapshot checked for this project lists service beginning **2023-08-15**, later than the historical ridership billing periods. The actual dates shown in the dashboard are read from the GTFS calendar tables in the file loaded. Do not combine current route shapes with 2018–19 ridership as if the geometry were historically identical.

## 4. Dashboard usage

1. Start the app from the project root: `python -m streamlit run app.py`.
2. Open **Geospatial Analysis** from the left sidebar. This is the default landing page.
3. In **Historical demand**, select a historical route, billing period, marker-size metric, and whether to show the boarding-weighted heatmap.
4. Press **Locate historical stops with OpenStreetMap** if the local coordinate cache does not exist. The first run makes rate-limited online requests and writes `data/stop_locations_osm.csv`.
5. The page uses a map + analytics split view. Click a marker or select a stop in the inspector to update its billing-period comparison, route contribution, and scheduled-hour profile.
6. Optionally load a current GTFS ZIP in the source expander and enable **Show real GTFS route lines on this historical demand map**. Those lines are a later 2023+ reference only; they are not represented as exact historical alignments.
7. In **Current GTFS routes**, select a route. The map draws actual `shapes.txt` geometry when it is linked to trips in the loaded feed. Click a stop or select it in the inspector to view its stop ID, served routes, coordinates, and scheduled stop sequence.
8. Use **Map appearance** to choose theme-matched, dark, light, or standard OpenStreetMap tiles.

The map + analytics split view is the core geospatial workflow. The heatmap and stop marker sizes are weighted by the selected historical boarding counts. They are demand visualisations, not measurements of crowd density or stop capacity.

## 5. Attribution and privacy

- OpenStreetMap data is © OpenStreetMap contributors. The Folium basemap includes map attribution.
- Route descriptions and historical route context are from UC Merced's August 2019 Transportation Impact Analysis.
- Current route geometry is from the GTFS ZIP loaded into the dashboard and should be cited with its service date range.
- `data/team_members_private.csv` contains academic identifiers for local dashboard display. It is ignored by Git. Do not force-add it to a public repository. The public roster in `data/team_members.csv` contains names and general project roles only.
