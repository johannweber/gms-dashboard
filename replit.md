# GMS Oorsigpaneel - Replit Project

## Overview

This is a Streamlit-based executive dashboard application (GMS Oorsigpaneel) designed for visualizing departmental KPI (Key Performance Indicator) data. The application reads data from an Excel workbook containing planning and performance metrics for 2026, and presents it through an interactive, executive-friendly interface. The dashboard is built in Python and uses Streamlit for the web interface, Pandas for data manipulation, and Plotly for visualizations. All labels and content are in Afrikaans to match the organizational language requirements.

## Recent Changes

### November 19, 2025 - Bestuursoorsig Tab Updates
- Changed application title from "Departementele KPI Dashboard" to "GMS Oorsigpaneel"
- Removed "Aantal KPI-items" metric indicator (reduced from 4 to 3 top metrics)
- Changed "Swakste 2030 Toekomsvisie" metric to "Beste 2026 Fokus" to highlight best-performing focus area
- Removed "Swakste 10 KPI-items" table section
- Added new "Top-5 Beste Ankerdorpe" section displaying the 5 anchor communities with highest achievement percentages

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web framework
- **Layout**: Wide layout with collapsed sidebar for maximum screen real estate
- **UI Pattern**: Multi-tab dashboard interface (4 tabs planned in MVP spec)
- **Visualization**: Plotly Express for interactive charts and visualizations
- **State Management**: Streamlit's native caching mechanism (`@st.cache_data`) for data loading performance

**Design Rationale**: Streamlit was chosen for rapid development of data-driven dashboards with minimal frontend code. The wide layout maximizes data visibility for executive viewing, while Plotly provides interactive, professional-grade visualizations without requiring complex JavaScript.

### Backend Architecture
- **Language**: Python 3.x
- **Data Processing**: Pandas DataFrames for in-memory data manipulation
- **Data Source**: Excel file-based data storage (no database)
- **File Structure**: Single-file application pattern (`app.py`) for MVP simplicity

**Design Rationale**: A file-based approach using Excel as the data source eliminates database setup complexity while meeting the immediate need to visualize existing planning data. The single-file pattern keeps the MVP simple and maintainable. Pandas provides robust data transformation capabilities for the analytical requirements.

### Data Model
- **Primary Data Source**: Excel workbook with "2026 BEPLANNING" sheet as the main fact table
- **Row Structure**: Each row represents one KPI/project item with associated metrics
- **Key Metrics**:
  - `TEIKEN` (Target): Numeric target value
  - `UITSET` (Output): Numeric actual output value
  - `% BEHAAL` (Achievement): Pre-calculated percentage achieved
- **Dimensions**: Strategic pillars, focus areas, quarters, provinces, regions, districts, anchor communities, project owners

**Design Rationale**: The data is already structured in Excel with calculated KPI percentages, eliminating the need for complex aggregation logic. The dimensional model supports hierarchical filtering from strategic vision down to individual projects.

### Core Features
1. **Data Loading & Caching**: Excel file loaded once at startup with Streamlit caching to prevent repeated file reads
2. **Global Filtering System**: Multi-dimensional filters (quarter, province, focus area, vision pillar) that cascade across all dashboard components
3. **Aggregation Engine**: Group-level metrics calculation for hierarchical views (mean, min, max, count of achievements; sum of targets and outputs)
4. **Error Handling**: Graceful handling of missing/malformed data with explicit error messages

**Design Rationale**: Caching prevents performance degradation on dashboard interactions. The global filter pattern provides consistent data context across all tabs. Type coercion with error handling ensures robustness when dealing with potentially inconsistent Excel data.

### Data Processing Pipeline
1. Load Excel file into Pandas DataFrame
2. Convert metric columns (`TEIKEN`, `UITSET`, `% BEHAAL`) to numeric types with error coercion
3. Fill missing categorical values with "Onbekend" (Unknown) placeholder
4. Apply user-selected filters to create filtered dataset
5. Calculate aggregated metrics per grouping dimension
6. Render visualizations and tables from filtered/aggregated data

## External Dependencies

### Python Libraries
- **streamlit**: Web application framework for building the interactive dashboard
- **pandas**: Data manipulation and analysis, Excel file reading
- **plotly.express**: Interactive charting and visualization library
- **numpy**: Numerical computing support
- **openpyxl** (implicit): Required by Pandas for reading modern Excel (.xlsx) files

### Data Files
- **Excel Workbook**: `attached_assets/00 GEKONSOLIDEER copy_1763538344798.xlsx`
  - Contains the "2026 BEPLANNING" sheet with KPI data
  - Acts as the single source of truth for all dashboard metrics
  - File is read-only; no write operations performed

### Third-Party Services
- **None**: This is a standalone application with no external API integrations, authentication services, or cloud dependencies in the MVP version

### Future Considerations
- The current Excel-based approach may need migration to a proper database (PostgreSQL, SQLite) if data volume grows or multi-user write access is required
- Authentication/authorization is not implemented; assume trusted network deployment or future integration with organizational SSO
- No data versioning or audit trail; Excel file updates replace all historical context