# CatTracks Ridership Intelligence
### DA-012 — Public Transport Ridership Analysis

An interactive data analytics and geospatial visualization project exploring historical passenger boarding patterns across the UC Merced CatTracks campus bus network.

**Developed as part of the B.Tech Computer Science & Engineering curriculum at Invertis University, Bareilly.**

<p align="center">
  <strong>Project ID:</strong> DA-012 &nbsp; | &nbsp;
  <strong>Group:</strong> BTech_DA_08 &nbsp; | &nbsp;
  <strong>Semester:</strong> III
</p>

---

## Overview

CatTracks Ridership Intelligence is a Python-based public transportation analytics application designed to explore, analyse and visualize historical passenger boarding patterns across the University of California, Merced campus bus network.

The project uses historical CatTracks billing workbooks from October 2018 and February 2019 to investigate passenger demand across four weekday bus routes:

- C1 Blue
- C1 Gold
- C2 Express
- G-Line

The application combines data processing, exploratory data analysis, interactive visualizations and geospatial exploration in a single interface.

Rather than relying exclusively on static charts, the project introduces an interactive map-based analytical workspace where users can explore geographical stop locations, compare passenger demand and investigate route-level patterns.

## Key Features

### 1. Interactive Analytics Dashboard

- Overview of recorded passenger boardings.
- Route-wise ridership comparisons.
- Billing-period comparisons.
- Busiest bus-stop identification.
- Scheduled departure-time analysis.
- Peak and off-peak demand comparison.
- Interactive charts and data visualizations.

### 2. Geospatial Analysis

- Interactive geographical map using OpenStreetMap.
- Historical bus-stop location exploration.
- Route-based geographical filtering.
- Passenger demand heatmap using recorded boarding counts.
- Interactive bus-stop markers.
- Stop-level ridership inspection.
- Map appearance controls.
- Geographical data coverage indicators.

**Geospatial data note:** The historical Excel workbooks contain bus-stop names but do not provide exact latitude/longitude coordinates or vector route geometries. Historical stop locations are therefore resolved using OpenStreetMap geocoding and must be treated as approximate matches, not surveyed bus-stop coordinates.

### 3. Route Intelligence

- Compare demand across all four routes.
- Examine individual route performance.
- Identify high-demand stops.
- Explore route-level boarding patterns.
- Compare historical billing periods.

### 4. Temporal Analysis

- Departure-hour demand analysis.
- Morning and evening demand comparisons.
- Peak versus off-peak analysis.
- Distribution of passenger boardings across scheduled departure times.

### 5. Interactive Data Explorer

- Browse processed ridership observations.
- Filter records using dashboard selections.
- Examine passenger boarding counts.
- Export filtered analytical data as CSV.

### 6. Project Team & Documentation

- Project identification and academic details.
- Project team information.
- Methodology and data dictionary.
- Source attribution and project limitations.

---

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Pandas | Data processing and analysis |
| NumPy | Numerical operations |
| Matplotlib | Statistical visualizations |
| Plotly | Interactive charts |
| Streamlit | Interactive web application |
| Folium | Geographical mapping |
| Streamlit-Folium | Map integration with Streamlit |
| OpenStreetMap | Geographical basemap and geocoding |
| GeoPandas / Geospatial tools | Geographical data processing where applicable |
| Jupyter Notebook | Exploratory analysis and experimentation |
| OpenPyXL | Excel workbook processing |

---

## Dataset Information

The project uses two historical CatTracks billing workbooks:

| Dataset | Billing period |
|---|---|
| CATTRACKS Fall 2018 | October 2018 |
| CATTRACKS Fall 2019 | February 2019 |

The analysis focuses on four weekday route worksheets:

- C1 BLUE
- C1-GOLD
- C2 - EXPRESS
- G-Line

### Processed Dataset

The extraction and cleaning pipeline produces a structured dataset containing:

- Period
- Route
- Bus stop
- Scheduled departure time
- Passenger boarding count
- Source workbook
- Departure hour
- Time band
- Peak/off-peak classification

The current processed dataset contains 1,114 ridership observations.

### Example Analytical Results

Combined recorded boarding totals across the two billing periods:

| Route | October 2018 | February 2019 |
|---|---:|---:|
| C1 Blue | 5,976 | 4,304 |
| C1 Gold | 5,829 | 4,005 |
| C2 Express | 13,552 | 12,053 |
| G-Line | 5,261 | 6,299 |
| **Total** | **30,618** | **26,661** |

These values represent recorded boardings, not unique individual passengers.

The billing periods are not normalized by operating days, so their totals should not be interpreted as a direct growth or decline measurement.

---

## Geospatial Data & Route Mapping

The geospatial component uses OpenStreetMap-based geographical lookups to associate historical bus-stop labels with approximate geographical locations.

The application also supports a separate current-network reference using GTFS (General Transit Feed Specification) data, where a usable feed and route geometry are available.

**Important distinction:**

The historical ridership observations belong to 2018–2019, whereas the available newer GTFS network represents later service information.

These geographical datasets are kept separate to avoid presenting current routes as verified historical routes.

Historical route geometry is not included in the original Excel workbooks. Any reconstructed historical route path must be explicitly labelled as reconstructed rather than exact.

---

## Installation & Setup

### Prerequisites

- Python 3.11 or newer recommended.
- Git.
- pip.
- A modern web browser.

### 1. Clone the repository

```bash
git clone https://github.com/JYNXEN/DA-012-Public-Transport-Analytics.git

cd DA-012-Public-Transport-Analytics
```

### 2. Create a virtual environment

**macOS / Linux**

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

**Windows**

```bash
python -m venv .venv
```

Activate it:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip

python -m pip install -r requirements.txt
```

### 4. Run the analytical pipeline

```bash
python run_analysis.py
```

The script processes the historical Excel datasets and generates analytical CSV tables and charts inside the `outputs/` directory.

### 5. Launch the interactive dashboard

```bash
python -m streamlit run app.py
```

Open the local application:

```text
http://localhost:8501
```

The dashboard runs locally on your computer.

### 6. Open the Jupyter Notebook

```bash
jupyter notebook notebooks/DA012_Ridership_Analysis.ipynb
```

You can also open the notebook through JupyterLab and execute its cells individually.

### 7. Run automated tests

```bash
python -m unittest discover -s tests -v
```

---

## Project Structure

```text
DA-012-Public-Transport-Analytics/
│
├── app.py
│
├── run_analysis.py
│
├── requirements.txt
│
├── README.md
│
├── LICENSE
│
├── NOTICE.md
│
├── .gitignore
│
├── data/
│   ├── Historical Excel datasets
│   └── Public project metadata
│
├── notebooks/
│   └── DA012_Ridership_Analysis.ipynb
│
├── src/
│   ├── Ridership analysis
│   ├── Data extraction
│   └── Geospatial processing
│
├── outputs/
│   ├── charts/
│   └── tables/
│
├── tests/
│
├── docs/
│
└── upstream_reference/
```

---

## Methodology

The project follows a reproducible data analytics workflow:

1. **Data Collection:** Obtain the historical UC Merced CatTracks Excel billing workbooks.
2. **Data Inspection:** Examine the workbook structure, route worksheets and aggregate passenger boarding tables.
3. **Data Extraction:** Extract the relevant PAX ON aggregate tables.
4. **Data Cleaning:** Standardize stop labels, handle missing or invalid values and prepare structured records.
5. **Feature Engineering:** Derive departure-hour and time-band information and classify peak/off-peak periods.
6. **Exploratory Data Analysis:** Calculate route-wise, stop-wise and time-based passenger boarding summaries.
7. **Visualization:** Generate analytical charts, comparisons and geographical demand visualizations.
8. **Interpretation:** Identify demand patterns while acknowledging the limitations of the historical datasets.

### Peak-Hour Definition

For the purposes of this project, peak periods are defined as:

- Morning peak: 07:00–09:59
- Evening peak: 16:00–18:59

These are analytical assumptions used for comparison, not official CatTracks peak-hour definitions.

---

## Limitations

The project acknowledges the following limitations:

- The analysis uses historical billing-period aggregates rather than individual passenger records.
- Only four weekday bus routes are included in the primary analysis.
- Passenger boardings do not represent unique passengers.
- The billing periods are not adjusted for the number of operating days.
- Reliable daily and weekend comparisons cannot be derived from the available aggregate tables.
- Historical stop coordinates are approximate geocoding matches and may represent nearby landmarks or intersections.
- Historical route geometry is not provided in the original Excel datasets.
- Newer GTFS route information must not be treated as an exact representation of the 2018–2019 network.
- Peak-hour classifications are predefined analytical assumptions.

---

## Project Information

| Field | Details |
|---|---|
| Project Title | Public Transport Ridership Analysis |
| Project ID | DA-012 |
| Group ID | BTech_DA_08 |
| Programme | B.Tech Computer Science & Engineering |
| Semester | III |
| Section | F |
| Institution | Invertis University, Bareilly |
| Project Mentor | Puneet Arora |
| Project Lead | Mohd. Shoaib |

Team member names and academic identifiers should be published only with the respective members' permission. Student IDs and university roll numbers are intentionally excluded from this public repository.

---

## Original Project & Attribution

This project is an adaptation and extension of the publicly available UC Merced CatTracks Simulator.

**Original repository:**

https://github.com/nlt-python/UCM_CatTracks_Simulator

The original project and its authors are acknowledged in `NOTICE.md`.

Please consult the included `LICENSE` and `NOTICE.md` files for applicable licensing and attribution requirements.

This repository should be understood as an educational adaptation, not an official UC Merced transportation application.

---

## Future Improvements

Potential future development includes:

- Improved historical geographical route reconstruction using verified source material.
- Higher geographical coverage of historical bus stops.
- More detailed route-level demand analysis.
- Improved spatial demand visualization.
- Additional geographical comparison between historical and newer transit networks.
- Online dashboard deployment.
- Further statistical analysis using additional transit datasets.

---

## Author

**Mohd. Shoaib**

Project Lead — DA-012  
B.Tech Computer Science & Engineering  
Invertis University, Bareilly

GitHub: https://github.com/JYNXEN

---

*Developed as an academic Data Analytics project for Semester III.*

*CatTracks Ridership Intelligence — Exploring public transport demand through data and geospatial analytics.*