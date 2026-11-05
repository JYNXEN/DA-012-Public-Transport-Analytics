"""Unit tests for GTFS ZIP parsing; no network calls are made."""
from io import BytesIO
import unittest
import zipfile

from src.geospatial import parse_gtfs_archive


def build_gtfs_zip() -> bytes:
    tables = {
        "routes.txt": (
            "route_id,route_short_name,route_long_name,route_color\n"
            "r1,C1,Campus Line,3366CC\n"
        ),
        "stops.txt": (
            "stop_id,stop_name,stop_lat,stop_lon\n"
            "s1,Campus,37.365,-120.425\n"
            "s2,Downtown,37.300,-120.480\n"
        ),
        "trips.txt": (
            "route_id,service_id,trip_id,shape_id\n"
            "r1,wk,t1,sh1\n"
        ),
        "stop_times.txt": (
            "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
            "t1,08:00:00,08:00:00,s1,1\n"
            "t1,08:15:00,08:15:00,s2,2\n"
        ),
        "shapes.txt": (
            "shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence\n"
            "sh1,37.365,-120.425,1\n"
            "sh1,37.300,-120.480,2\n"
        ),
        "calendar.txt": (
            "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n"
            "wk,1,1,1,1,1,0,0,20230815,20261230\n"
        ),
    }
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in tables.items():
            archive.writestr(name, content)
    return buffer.getvalue()


class GTFSParsingTests(unittest.TestCase):
    def test_parses_routes_stops_shapes_and_service_dates(self):
        result = parse_gtfs_archive(build_gtfs_zip())
        self.assertEqual(result["routes"].iloc[0]["route_label"], "C1 · Campus Line")
        self.assertEqual(len(result["stops"]), 2)
        self.assertEqual(len(result["shapes"]), 2)
        self.assertEqual(result["shapes"]["route_label"].unique().tolist(), ["C1 · Campus Line"])
        self.assertEqual(result["service_range"].iloc[0]["start"], "20230815")
        self.assertEqual(result["service_range"].iloc[0]["end"], "20261230")
        self.assertEqual(result["route_stops"]["stop_name"].tolist(), ["Campus", "Downtown"])
        self.assertEqual(result["route_stops"]["stop_sequence"].tolist(), [1, 2])

    def test_stop_to_route_relationship_is_created(self):
        result = parse_gtfs_archive(build_gtfs_zip())
        served = dict(zip(result["stops"]["stop_id"], result["stops"]["served_by"]))
        self.assertEqual(served["s1"], ["C1 · Campus Line"])
        self.assertEqual(served["s2"], ["C1 · Campus Line"])

    def test_rejects_non_zip_input(self):
        with self.assertRaisesRegex(ValueError, "valid GTFS ZIP"):
            parse_gtfs_archive(b"not a zip file")


if __name__ == "__main__":
    unittest.main()
