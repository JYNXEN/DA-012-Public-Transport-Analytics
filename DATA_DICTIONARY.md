# Data dictionary

The extraction script converts the workbook's aggregate `PAX ON` table into a tidy dataset. One row represents the passenger count for one named stop, one route, one scheduled departure time, and one billing period.

| Field | Meaning |
|---|---|
| `period` | Billing period label: October 2018 or February 2019 |
| `route` | Normalised route label: C1 Blue, C1 Gold, C2 Express, or G-Line |
| `stop` | Stop name as listed in the source workbook (whitespace normalised) |
| `departure_time` | Scheduled departure time formatted as HH:MM |
| `passenger_count` | Reported passenger boardings in the aggregate PAX ON table |
| `source_workbook` | Original Excel workbook filename |
| `source_sheet` | Original worksheet name |
| `departure_minutes` | Scheduled time converted to minutes after midnight for sorting/plotting |
| `departure_hour` | Hour component of the scheduled departure time |
| `time_band` | Derived time category based on the scheduled departure time |
| `peak_status` | Derived Peak / Off-peak flag |
| `period_order` | Sort key for the two billing periods |

## Interpretation notes

- `PAX ON` means passengers boarding the bus. This analysis does not use `PAX OFF` counts.
- `passenger_count` values are aggregated counts from the workbook, not individual passenger-level trip records.
- A stop name may appear more than once within one route's loop. The script standardises a small set of obvious spelling/punctuation variants (for example, `Arrow Wood Dr.` and `Arrow Wood Dr` become `Arrow Wood Drive`) and combines matching stop names at the same route, period, and departure time.
- Peak periods are defined for this project as 07:00–09:59 and 16:00–18:59. These are analytical assumptions, not a claim that the transit operator officially defines peak hours this way.
- The two billing periods are not adjusted for the number of operating days. Compare their recorded totals descriptively; do not treat the difference as a proven growth or decline in demand.

## Optional geospatial data

The original Excel workbooks do not supply coordinates. If the user geocodes the stop labels, `data/stop_locations_osm.csv` is created locally with:

| Field | Meaning |
|---|---|
| `stop` | Stop label from the original ridership workbook |
| `query_used` | Search text sent to OpenStreetMap Nominatim |
| `latitude`, `longitude` | Geocoder coordinates (place/intersection estimate, not a surveyed stop pole) |
| `display_name` | Geocoder's returned place/address label |
| `geocoder` | Service used to resolve the stop name |
| `status` | `matched` or `not found` |
| `location_note` | Interpretation/verification note |

The local coordinate cache is excluded from Git. Separately, a static GTFS ZIP may supply current route/stop/shape geometry and its own calendar service dates; those newer dates must not be treated as matching the 2018–19 ridership periods unless the feed is historically matched.
