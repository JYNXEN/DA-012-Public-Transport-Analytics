"""Load and analyse the UC Merced CatTracks aggregate PAX ON data.

This module intentionally extracts only the final aggregate PAX ON table from
four weekday route sheets in each source workbook. The original workbooks have
multiple side-by-side daily blocks followed by an aggregate table; selecting
that table dynamically avoids hard-coded column offsets in the original
notebooks.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable
import re

import matplotlib.pyplot as plt
import pandas as pd
from openpyxl import load_workbook

ROUTE_SHEETS = {
    "C1 BLUE": "C1 Blue",
    "C1-GOLD": "C1 Gold",
    "C2 - EXPRESS": "C2 Express",
    "G-Line": "G-Line",
}

WORKBOOKS = {
    "CATTRACKS Fall 2018- October Billing.xlsx": "October 2018",
    "219-CATTRACKS Fall 2019- February Billing.xlsx": "February 2019",
}

EXCLUDED_HEADER_LABELS = {"TOTAL", "REQ", "PAX ON", "PAX OFF"}


def _is_time_code(value: object) -> bool:
    """Return True for Excel numeric schedule labels such as 545 or 2328."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    number = int(value)
    if number != value or number < 0 or number > 2359:
        return False
    hour, minute = divmod(number, 100)
    return 0 <= hour <= 23 and 0 <= minute <= 59


def _format_time_code(value: object) -> str:
    number = int(value)
    hour, minute = divmod(number, 100)
    return f"{hour:02d}:{minute:02d}"


def _normalise_stop_name(name: str) -> str:
    """Standardise a small set of obvious source spelling/punctuation variants."""
    cleaned = re.sub(r"\s+", " ", name).strip()
    key = cleaned.lower().rstrip(".")
    aliases = {
        "arrow wood dr": "Arrow Wood Drive",
        "arrow wood drive": "Arrow Wood Drive",
        "compass pointe apts": "Compass Pointe",
        "compass pointe": "Compass Pointe",
        "scholar/emigrant": "Scholars/Emigrant",
        "scholars/emigrant pass": "Scholars/Emigrant",
        "scholars/emigrant": "Scholars/Emigrant",
        'el portal plaza/"g" st': 'El Portal Plaza / G Street',
        'el portal plaza/"g" street': 'El Portal Plaza / G Street',
        'alexander & "g" st': 'Alexander & G Street',
        'alexander & "g" street': 'Alexander & G Street',
    }
    return aliases.get(key, cleaned)


def _find_aggregate_header(ws) -> tuple[int, int, list[tuple[int, str]]]:
    """Find the right-most aggregate PAX ON table's header row and columns."""
    marker_cells = []
    scan_rows = min(12, ws.max_row)
    for row in ws.iter_rows(min_row=1, max_row=scan_rows):
        for cell in row:
            if isinstance(cell.value, str) and "PAX ON" in cell.value.upper():
                marker_cells.append(cell)

    if not marker_cells:
        raise ValueError(f"No PAX ON marker found in worksheet {ws.title!r}")

    marker_row = max(cell.row for cell in marker_cells)
    header_row = marker_row + 1
    if header_row > ws.max_row:
        raise ValueError(f"Missing header row after PAX ON marker in {ws.title!r}")

    header_values = [cell.value for cell in ws[header_row]]
    candidates: list[tuple[int, int]] = []
    for col_idx, value in enumerate(header_values, start=1):
        if not isinstance(value, str) or value.strip().upper() in EXCLUDED_HEADER_LABELS:
            continue
        valid_times = [v for v in header_values[col_idx:] if _is_time_code(v)]
        if len(valid_times) >= 5:
            candidates.append((col_idx, len(valid_times)))

    if not candidates:
        raise ValueError(f"Could not detect aggregate table header in {ws.title!r}")

    # The aggregate table is the right-most route table in the worksheet.
    label_col = max(candidates, key=lambda item: item[0])[0]
    time_columns = [
        (col_idx, _format_time_code(value))
        for col_idx, value in enumerate(header_values, start=1)
        if col_idx > label_col and _is_time_code(value)
    ]
    if not time_columns:
        raise ValueError(f"No departure-time columns found in {ws.title!r}")
    return header_row, label_col, time_columns


def _extract_route_sheet(ws, period: str, source_file: str) -> list[dict]:
    header_row, label_col, time_columns = _find_aggregate_header(ws)
    records: list[dict] = []
    blank_streak = 0

    for row_idx in range(header_row + 1, ws.max_row + 1):
        stop_value = ws.cell(row=row_idx, column=label_col).value
        stop = str(stop_value).strip() if stop_value is not None else ""

        if stop.upper().startswith("TOTAL"):
            break
        if not stop:
            blank_streak += 1
            if blank_streak >= 2:
                break
            continue
        blank_streak = 0

        # Drop obvious header-like entries if a workbook has repeated labels.
        if stop.upper() in EXCLUDED_HEADER_LABELS:
            continue

        for col_idx, departure_time in time_columns:
            value = ws.cell(row=row_idx, column=col_idx).value
            if value is None or value == "":
                passenger_count = 0.0
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                passenger_count = float(value)
            else:
                continue

            if passenger_count < 0:
                continue
            if passenger_count == 0:
                continue

            records.append({
                "period": period,
                "route": ROUTE_SHEETS[ws.title],
                "stop": _normalise_stop_name(stop),
                "departure_time": departure_time,
                "passenger_count": passenger_count,
                "source_workbook": source_file,
                "source_sheet": ws.title,
            })

    if not records:
        raise ValueError(f"No positive PAX ON records extracted from {ws.title!r}")
    return records


def load_ridership_data(data_dir: str | Path) -> pd.DataFrame:
    """Read the two supplied workbooks into one tidy passenger-count table."""
    data_dir = Path(data_dir)
    all_records: list[dict] = []

    for filename, period in WORKBOOKS.items():
        path = data_dir / filename
        if not path.exists():
            raise FileNotFoundError(
                f"Required workbook not found: {path}\n"
                "Keep both original Excel files inside the project's data/ folder."
            )

        workbook = load_workbook(path, read_only=False, data_only=True)
        try:
            for sheet_name in ROUTE_SHEETS:
                if sheet_name not in workbook.sheetnames:
                    raise ValueError(f"Worksheet {sheet_name!r} missing in {filename}")
                all_records.extend(_extract_route_sheet(workbook[sheet_name], period, filename))
        finally:
            workbook.close()

    df = pd.DataFrame(all_records)
    if df.empty:
        raise ValueError("No ridership records were loaded.")

    df["passenger_count"] = pd.to_numeric(df["passenger_count"], errors="coerce")
    df = df.dropna(subset=["passenger_count", "route", "stop", "departure_time"])
    df = df[df["passenger_count"] >= 0].copy()

    # Repeated occurrences of a stop within a route are combined as total
    # boardings at that named stop and departure time for the billing period.
    group_cols = ["period", "route", "stop", "departure_time", "source_workbook"]
    df = (
        df.groupby(group_cols, as_index=False, dropna=False)["passenger_count"]
        .sum()
        .sort_values(["period", "route", "departure_time", "stop"])
        .reset_index(drop=True)
    )

    minutes = df["departure_time"].map(
        lambda x: int(x[:2]) * 60 + int(x[3:])
    )
    df["departure_minutes"] = minutes
    df["departure_hour"] = minutes // 60

    def classify_time(minute: int) -> str:
        if 7 * 60 <= minute < 10 * 60:
            return "Morning peak"
        if 16 * 60 <= minute < 19 * 60:
            return "Evening peak"
        if 5 * 60 <= minute < 7 * 60:
            return "Early morning"
        if 10 * 60 <= minute < 16 * 60:
            return "Midday"
        return "Night"

    df["time_band"] = minutes.map(classify_time)
    df["peak_status"] = df["time_band"].map(
        lambda x: "Peak" if x in {"Morning peak", "Evening peak"} else "Off-peak"
    )
    df["period_order"] = df["period"].map({"October 2018": 1, "February 2019": 2})
    return df


def build_summary_tables(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Create route, stop, departure, peak/off-peak and period summaries."""
    route_summary = (
        df.groupby(["period", "route"], as_index=False)["passenger_count"]
        .sum()
        .rename(columns={"passenger_count": "total_boardings"})
    )

    stop_summary = (
        df.groupby(["period", "route", "stop"], as_index=False)["passenger_count"]
        .sum()
        .rename(columns={"passenger_count": "total_boardings"})
        .sort_values("total_boardings", ascending=False)
    )

    departure_summary = (
        df.groupby(["period", "route", "departure_time", "departure_minutes"], as_index=False)["passenger_count"]
        .sum()
        .sort_values(["period", "route", "departure_minutes"])
    )

    peak_summary = (
        df.groupby(["period", "route", "peak_status"], as_index=False)["passenger_count"]
        .sum()
        .rename(columns={"passenger_count": "total_boardings"})
    )

    period_summary = (
        df.groupby("period", as_index=False)["passenger_count"]
        .sum()
        .rename(columns={"passenger_count": "total_boardings"})
    )

    return {
        "route_summary": route_summary,
        "stop_summary": stop_summary,
        "departure_summary": departure_summary,
        "peak_offpeak_summary": peak_summary,
        "period_summary": period_summary,
    }


def save_charts(df: pd.DataFrame, tables: dict[str, pd.DataFrame], output_dir: str | Path) -> list[Path]:
    """Generate five PNG charts and return their paths."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    charts: list[Path] = []

    # 1. Passenger boardings by route and billing period.
    route_pivot = tables["route_summary"].pivot(
        index="route", columns="period", values="total_boardings"
    ).fillna(0)
    ax = route_pivot.plot(kind="bar", figsize=(10, 6))
    ax.set_title("Passenger Boardings by Bus Route")
    ax.set_xlabel("Bus route")
    ax.set_ylabel("Recorded passenger boardings")
    ax.tick_params(axis="x", rotation=0)
    ax.legend(title="Billing period")
    ax.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    p = output_dir / "01_route_ridership_comparison.png"
    plt.savefig(p, dpi=180, bbox_inches="tight")
    plt.close()
    charts.append(p)

    # 2. Ten busiest stops across both periods.
    top_stops = (
        tables["stop_summary"].groupby("stop")["total_boardings"]
        .sum().sort_values(ascending=False).head(10).sort_values()
    )
    fig, ax = plt.subplots(figsize=(10, 6))
    top_stops.plot(kind="barh", ax=ax)
    ax.set_title("Top 10 Stops by Recorded Passenger Boardings")
    ax.set_xlabel("Recorded passenger boardings")
    ax.set_ylabel("Bus stop")
    ax.grid(axis="x", alpha=0.25)
    plt.tight_layout()
    p = output_dir / "02_top_10_stops.png"
    plt.savefig(p, dpi=180, bbox_inches="tight")
    plt.close(fig)
    charts.append(p)

    # 3. Departure-time demand, separated by route and period.
    fig, ax = plt.subplots(figsize=(12, 6))
    for (period, route), group in tables["departure_summary"].groupby(["period", "route"]):
        line = group.groupby("departure_minutes")["passenger_count"].sum().sort_index()
        label = f"{route} — {period}"
        ax.plot(line.index / 60, line.values, marker="o", linewidth=1.5, label=label)
    ax.set_title("Passenger Demand by Scheduled Departure Time")
    ax.set_xlabel("Scheduled departure time (hour of day)")
    ax.set_ylabel("Recorded passenger boardings")
    ax.set_xticks(range(5, 24))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(5, 24)], rotation=45)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8, ncol=2)
    plt.tight_layout()
    p = output_dir / "03_demand_by_departure_time.png"
    plt.savefig(p, dpi=180, bbox_inches="tight")
    plt.close(fig)
    charts.append(p)

    # 4. Peak versus off-peak boardings by route, split by billing period.
    peak_pivot = tables["peak_offpeak_summary"].pivot_table(
        index=["period", "route"], columns="peak_status", values="total_boardings", fill_value=0
    )
    periods = ["October 2018", "February 2019"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for ax, period in zip(axes, periods):
        try:
            period_data = peak_pivot.loc[period]
        except KeyError:
            period_data = pd.DataFrame()
        if not period_data.empty:
            period_data.plot(kind="bar", ax=ax)
            legend = ax.get_legend()
            if legend is not None:
                legend.set_title("Time classification")
        ax.set_title(period)
        ax.set_xlabel("Bus route")
        ax.tick_params(axis="x", rotation=0)
        ax.grid(axis="y", alpha=0.25)
    axes[0].set_ylabel("Recorded passenger boardings")
    axes[-1].legend(title="Time classification")
    fig.suptitle("Peak vs Off-Peak Passenger Boardings by Route")
    plt.tight_layout()
    p = output_dir / "04_peak_vs_offpeak.png"
    plt.savefig(p, dpi=180, bbox_inches="tight")
    plt.close(fig)
    charts.append(p)

    # 5. Demand share by route across the combined data.
    route_overall = (
        tables["route_summary"].groupby("route")["total_boardings"]
        .sum().sort_values(ascending=False)
    )
    fig, ax = plt.subplots(figsize=(8, 6))
    route_overall.plot(kind="pie", autopct="%1.1f%%", startangle=90, ax=ax)
    ax.set_title("Share of Recorded Boardings by Route")
    ax.set_ylabel("")
    plt.tight_layout()
    p = output_dir / "05_route_share.png"
    plt.savefig(p, dpi=180, bbox_inches="tight")
    plt.close(fig)
    charts.append(p)

    return charts


def save_analysis_outputs(df: pd.DataFrame, tables: dict[str, pd.DataFrame], output_dir: str | Path) -> list[Path]:
    output_dir = Path(output_dir)
    table_dir = output_dir / "tables"
    chart_dir = output_dir / "charts"
    table_dir.mkdir(parents=True, exist_ok=True)

    outputs = []
    table_map = {
        "ridership_long.csv": df,
        "route_summary.csv": tables["route_summary"],
        "stop_summary.csv": tables["stop_summary"],
        "departure_summary.csv": tables["departure_summary"],
        "peak_offpeak_summary.csv": tables["peak_offpeak_summary"],
        "period_summary.csv": tables["period_summary"],
    }
    for filename, table in table_map.items():
        path = table_dir / filename
        table.to_csv(path, index=False)
        outputs.append(path)

    outputs.extend(save_charts(df, tables, chart_dir))
    return outputs


def quality_report(df: pd.DataFrame) -> pd.DataFrame:
    """Return a compact data-quality summary for the loaded tidy table."""
    return pd.DataFrame({
        "check": [
            "Rows after extraction",
            "Missing values across columns",
            "Negative passenger counts",
            "Unique routes",
            "Unique stop names",
            "Unique scheduled departure times",
        ],
        "result": [
            len(df),
            int(df.isna().sum().sum()),
            int((df["passenger_count"] < 0).sum()),
            df["route"].nunique(),
            df["stop"].nunique(),
            df["departure_time"].nunique(),
        ],
    })
