from pathlib import Path
import unittest


class DashboardStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        cls.source = (cls.root / "app.py").read_text(encoding="utf-8")
        cls.gitignore = (cls.root / ".gitignore").read_text(encoding="utf-8")

    def test_primary_navigation_is_in_sidebar(self):
        self.assertIn('st.radio("Navigation"', self.source)
        self.assertNotIn("st.tabs(", self.source)

    def test_global_filters_are_one_expandable_sidebar_section(self):
        self.assertIn('with st.expander("Global filters", expanded=False)', self.source)
        self.assertIn('column.checkbox(period, key=key)', self.source)
        self.assertNotIn('st.popover(f"Billing period', self.source)
        self.assertNotIn('st.multiselect("Billing period"', self.source)

    def test_default_map_uses_key_free_openstreetmap(self):
        self.assertIn('map_style: str = "OpenStreetMap Standard"', self.source)
        self.assertIn('tiles="https://tile.openstreetmap.org/{z}/{x}/{y}.png"', self.source)
        self.assertIn("© OpenStreetMap contributors", self.source)
        self.assertIn('options = ["OpenStreetMap Standard", "OpenStreetMap Humanitarian"]', self.source)

    def test_carto_is_optional_and_key_is_not_committed(self):
        self.assertIn('key = get_carto_api_key()', self.source)
        self.assertIn('st.text_input("CARTO basemap key (optional)", type="password"', self.source)
        self.assertIn('?key={key}', self.source)
        self.assertIn('.streamlit/secrets.toml', self.gitignore)

    def test_map_appearance_control_is_outside_map(self):
        self.assertIn('with st.expander("Map appearance", expanded=False)', self.source)
        self.assertIn('st.selectbox("Basemap", map_style_options', self.source)
        self.assertNotIn("folium.LayerControl(", self.source)

    def test_viewport_is_saved_in_component_callback_before_redraw(self):
        self.assertIn('def persist_historical_map_viewport()', self.source)
        self.assertIn('def persist_gtfs_map_viewport()', self.source)
        self.assertIn('on_change=persist_historical_map_viewport', self.source)
        self.assertIn('on_change=persist_gtfs_map_viewport', self.source)
        self.assertIn('returned_objects=["last_object_clicked", "last_object_clicked_count", "center", "zoom"]', self.source)
        self.assertIn('key=map_component_key', self.source)
        self.assertIn('key="gtfs_route_map_v5"', self.source)

    def test_recenter_is_explicit_and_does_not_use_fit_bounds(self):
        self.assertIn('st.button("Fit visible stops"', self.source)
        self.assertIn('st.button("Fit selected GTFS route"', self.source)
        self.assertNotIn('fmap.fit_bounds(', self.source)
        self.assertIn('initial_map_view(map_points)', self.source)

    def test_map_uses_bubbles_and_optional_weighted_heatmap(self):
        self.assertIn('["Demand bubbles", "Heatmap + bubbles", "Heatmap only"]', self.source)
        self.assertIn('HeatMap(', self.source)
        self.assertIn('radius=19', self.source)
        self.assertIn('markers_on = demand_layer in {"Demand bubbles", "Heatmap + bubbles"}', self.source)

    def test_map_split_view_and_compact_followup_analytics(self):
        self.assertIn('st.columns([1.55, 1.0]', self.source)
        self.assertIn('height=510', self.source)
        self.assertIn('### Demand patterns in the selected network', self.source)
        self.assertIn('### Stop inspector', self.source)

    def test_gtfs_route_shapes_are_drawn_when_available(self):
        self.assertIn('folium.PolyLine', self.source)
        self.assertIn('geo_gtfs_stop_choice_v5', self.source)
        self.assertIn('gtfs_data.get("route_stops"', self.source)

    def test_plotly_zoom_is_not_triggered_by_scroll_or_drag(self):
        self.assertIn('"scrollZoom": False', self.source)
        self.assertIn('dragmode=False', self.source)


if __name__ == "__main__":
    unittest.main()
