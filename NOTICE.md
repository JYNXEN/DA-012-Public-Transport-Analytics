# Attribution and source notice

This student adaptation is based on the publicly available project:

- **Original project:** UCM CatTracks Simulator
- **Original repository:** https://github.com/nlt-python/UCM_CatTracks_Simulator
- **Original author/maintainer:** nlt-python (GitHub account)
- **Original project partner identified in its README:** University of California, Merced
- **Original licence stated in the upstream README:** Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Licence text:** https://creativecommons.org/licenses/by/4.0/

## Changes made in this adaptation

- Replaced brittle, fixed-column extraction with dynamic detection of the aggregate `PAX ON` table.
- Added a tidy ridership dataset with route, stop, scheduled departure time, billing period, and passenger count.
- Added validation, summary tables, peak/off-peak classification, five additional charts, and CSV exports.
- Reorganised the analysis into a reusable Python module, a student-facing Jupyter notebook, and a command-line runner.
- Added an author-branded Streamlit dashboard with dynamic filters, Plotly charts, a route-by-hour heatmap, generated filter-specific insights, and CSV export.
- Added a geospatial page with rate-limited historical stop-name geocoding, a separately dated current GTFS route/stop/shape reference map, and transparent source/date limitations.
- Added the student project team roster. Academic identifiers are stored separately in a local-only file excluded from Git.

The source data and original project materials are attributed to the upstream project. This adaptation does not claim ownership of the source dataset.

## Student adaptation credit

The DA-012 adaptation and dashboard interface are prepared for the student project by **Shoaib**. This student credit does not replace or remove the upstream attribution above.
