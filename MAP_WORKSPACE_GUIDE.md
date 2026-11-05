# DA-012 map workspace

## What the map shows

The Geospatial Analysis page is designed as a map-led workspace with the map on the left and an interactive analysis inspector on the right.

### Historical demand layer (October 2018 / February 2019)
- Route and billing-period filters update map markers and calculations.
- Marker size and the optional heatmap are weighted by recorded `PAX ON` boarding counts.
- Clicking a marker or selecting a stop updates the stop inspector: period comparison, route contribution, and scheduled-hour profile.
- Historical locations are OpenStreetMap geocoder matches from stop labels, not surveyed stop-pole coordinates.

### GTFS route network layer
- Upload a current static GTFS ZIP or fetch the agency's published feed.
- `shapes.txt` linked to `trips.txt` is required for actual route polylines.
- `stops.txt`, `trips.txt`, and `stop_times.txt` provide stop coordinates and route-stop relationships.
- Clicking/selecting a GTFS stop updates the stop inspector. Selecting a route shows its route-specific stop sequence.

## Date integrity

The source ridership periods are October 2018 and February 2019. The archived CatTracks GTFS snapshot checked for this project begins on 2023-08-15. Therefore, current route lines can be overlaid for geographical context only; they must not be described as verified 2018–19 alignments. The August 2019 UC Merced Transportation Impact Assessment contains Figure 2, *Weekday Bus Routes*, as a static reference map. The Excel workbooks and this static figure do not provide machine-readable historical route polylines.

## Map appearance

Use the **Map appearance** selector to choose: Match app theme, Light streets, Dark streets, or Standard OpenStreetMap. The map tile choice is separate from the dashboard's Dark/Light application theme.

## Attribution

- Historical route context: UC Merced 2020 LRDP Transportation Impact Analysis, August 2019, Figure 2.
- Current routes and stops: the GTFS ZIP loaded into the app; cite the service date range displayed by the app.
- Geocoder: OpenStreetMap Nominatim.
- Map data: OpenStreetMap contributors (attribution is displayed on the map).


## Sidebar and viewport improvements

- Expand **Global filters** to reveal the two billing-period checkboxes and the shared route/time/demand filters. The collapsed sidebar stays compact when filters are not being changed.
- Expand **Map appearance** to choose Standard OSM, Humanitarian OSM or optional CARTO styles. Standard OSM is selected by default and needs no key.
- The CARTO key field is optional. Request a free non-commercial key at <https://www.carto.com/basemaps/apikey/> (up to 5 million tile requests/month), then paste it into the local sidebar field to enable Positron and Dark Matter.
- `st_folium` saves the map's center and zoom in an `on_change` callback before Streamlit reruns. Stable component keys and saved viewport values prevent a pan/zoom or filter rerun from sending the map back to its default extent.
- Press **Fit visible stops** only when you want to reset the historical viewport to the currently mapped stop extent. The equivalent GTFS button reframes the selected route.
- The historical map is 510 px high and now has a full-width billing-period/route and departure-hour analysis row underneath, reducing the blank area beneath the map.
