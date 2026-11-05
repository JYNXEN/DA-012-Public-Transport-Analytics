# Map setup and troubleshooting

## Default map

The dashboard starts with OpenStreetMap Standard. It requires no provider API key. Keep the visible `© OpenStreetMap contributors` attribution in place and use the map only for normal interactive viewing; do not bulk-download or prefetch tiles.

## Optional CARTO Light/Dark maps

CARTO provides Positron (light), Dark Matter (dark) and Voyager styles. Request a free key for non-commercial research/teaching at <https://www.carto.com/basemaps/apikey/>. The current free non-commercial tier is up to 5 million tile requests per calendar month. The key can be pasted into the password field under **Map appearance** in the sidebar. For persistent local configuration, create `.streamlit/secrets.toml` containing:

```toml
CARTO_API_KEY = "paste-your-key-here"
```

Do not commit `.streamlit/secrets.toml`; it is ignored by `.gitignore`. Keep `© OpenStreetMap contributors · © CARTO` attribution visible.

## Map viewport behaviour

Panning and zooming are captured through the Streamlit-Folium `on_change` callback before the app reruns. The current centre and zoom are saved in Streamlit session state and passed back to the map. Changing the basemap or a filter should preserve the current map view. Use **Fit visible stops** only when you deliberately want to reframe the map.

## Global filters

The sidebar's **Global filters** section is collapsed by default. Expand it to choose billing-period checkboxes, routes, time-of-day bands, demand class and departure-hour range.

## If map tiles do not load

1. Keep **OpenStreetMap Standard** selected and refresh the page.
2. Check that the Mac has an internet connection.
3. If using CARTO, verify that a valid key was pasted and the `CARTO` style is selected.
4. If tiles are still missing, select OpenStreetMap Standard to distinguish a provider-key problem from a general connectivity problem.
