# DA-012 UI redesign notes

This version replaces the horizontal page tabs with a persistent sidebar navigation:

- Overview
- Routes & Stops
- Time Patterns
- Geospatial Analysis
- Data Explorer
- Project Team
- Methodology

## Appearance switch

Use the Dark / Light control in the sidebar. The choice changes the application surfaces, typography, Plotly chart theme and map basemap tiles. The `.streamlit/config.toml` no longer forces a single dark theme.

## Geospatial behavior

### Historical demand points (2018–19)

The source Excel workbooks provide stop labels and boarding counts, but do not provide stop coordinates or route polylines. Historical points are therefore approximate OpenStreetMap Nominatim matches, not verified stop poles. The page:

- labels the points as approximate;
- displays only cached successful lookups;
- aggregates duplicate route associations to one visible marker per stop;
- lets users click a marker to inspect the stop's filtered historical counts;
- displays the selected stop's period/route comparison; and
- links to the official August 2019 UC Merced weekday route map.

It deliberately does not draw guessed 2018–19 route lines.

### Current network (GTFS)

The separate GTFS view can fetch the agency feed or accept a user-uploaded GTFS ZIP. It draws route polylines only when `shapes.txt` contains geometry linked to trips. Stop markers are shown from GTFS `stops.txt`. Feed dates are displayed separately from the 2018–19 ridership periods.

## Privacy

`data/team_members_private.csv` remains locally available and is excluded by `.gitignore`. Do not force-add it to a public repository. The public `data/team_members.csv` contains names and roles only.

## Install this update

Extract the UI update ZIP into the project root, allowing `app.py` and `.streamlit/config.toml` to be replaced. Then run:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
