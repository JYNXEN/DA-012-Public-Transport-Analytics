"""Run the DA-012 CatTracks ridership analysis from the project root."""
from pathlib import Path
from src.ridership_analysis import load_ridership_data, build_summary_tables, save_analysis_outputs

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"


def main() -> None:
    df = load_ridership_data(DATA_DIR)
    tables = build_summary_tables(df)
    outputs = save_analysis_outputs(df, tables, OUTPUT_DIR)
    print(f"Loaded {len(df):,} tidy ridership records.")
    print("\nRoute summary:")
    print(tables["route_summary"].to_string(index=False))
    print("\nPeriod summary:")
    print(tables["period_summary"].to_string(index=False))
    print(f"\nSaved {len(outputs)} CSV/PNG outputs under: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
