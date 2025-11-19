import warnings

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --------------------------------------------------
# BASIC CONFIG & WARNING HANDLING
# --------------------------------------------------

st.set_page_config(
    page_title="KPI Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Silence the openpyxl data-validation warning (optional)
warnings.filterwarnings(
    "ignore",
    message="Data Validation extension is not supported and will be removed",
)


# --------------------------------------------------
# DATA LOADING & FILTERING
# --------------------------------------------------

@st.cache_data
def load_data(uploaded_file):
    """Load and prepare the Excel data from an uploaded file only."""
    if uploaded_file is None:
        return None

    try:
        df = pd.read_excel(uploaded_file, sheet_name="2026 BEPLANNING")

        # Ensure numeric columns
        df["TEIKEN"] = pd.to_numeric(df["TEIKEN"], errors="coerce")
        df["UITSET"] = pd.to_numeric(df["UITSET"], errors="coerce")
        df["% BEHAAL"] = pd.to_numeric(df["% BEHAAL"], errors="coerce")

        # Fill missing text (object) columns with 'Onbekend'
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].fillna("Onbekend")

        return df

    except Exception as e:
        st.error(f"Fout met die laai van data: {e}")
        return None


def apply_filters(df, kwartaal_filter, provinsie_filter, fokus_filter, visie_filter):
    """(Kept for compatibility, but not used now – no global filters)."""
    filtered_df = df.copy()

    if kwartaal_filter:
        filtered_df = filtered_df[filtered_df["KWARTAAL"].isin(kwartaal_filter)]

    if provinsie_filter:
        filtered_df = filtered_df[filtered_df["PROVINSIE"].isin(provinsie_filter)]

    if fokus_filter:
        filtered_df = filtered_df[filtered_df["2026 FOKUS"].isin(fokus_filter)]

    if visie_filter:
        filtered_df = filtered_df[filtered_df["2030 TOEKOMSVISIE"].isin(visie_filter)]

    return filtered_df


def calculate_group_metrics(df, group_col):
    """Calculate aggregated metrics for a grouping column.

    Only:
    - Gem. % BEHAAL
    - Aantal KPI-items
    - Totale Teiken
    - Totale Uitset
    """
    if df.empty:
        return pd.DataFrame(
            columns=[
                group_col,
                "Gem. % BEHAAL",
                "Aantal KPI-items",
                "Totale Teiken",
                "Totale Uitset",
            ]
        )

    grouped = (
        df.groupby(group_col)
        .agg(
            {
                "% BEHAAL": ["mean", "count"],
                "TEIKEN": "sum",
                "UITSET": "sum",
            }
        )
        .reset_index()
    )

    grouped.columns = [
        group_col,
        "Gem. % BEHAAL",
        "Aantal KPI-items",
        "Totale Teiken",
        "Totale Uitset",
    ]
    grouped = grouped.sort_values("Gem. % BEHAAL")

    return grouped


def format_percentage(val):
    """Format a value as percentage."""
    if pd.isna(val):
        return "-"
    return f"{val:.1f}%"


def format_number(val):
    """Format a numeric value with thousand separators."""
    if pd.isna(val):
        return "-"
    return f"{val:,.0f}"


# --------------------------------------------------
# MAIN APP
# --------------------------------------------------

def main():
    st.title("GMS Oorsigpaneel")

    # Initialise session state
    if "df" not in st.session_state:
        st.session_state.df = None
    if "file_name" not in st.session_state:
        st.session_state.file_name = None

    # ----------------------------
    # Upload section (only when no data loaded)
    # ----------------------------
    if st.session_state.df is None:
        st.markdown(
            "Laai jou **Excel-databasis** hieronder op en klik dan op **'Laai data'** om die paneel te gebruik."
        )

        uploaded_file = st.file_uploader("Laai Excel lêer op", type=["xlsx", "xls"])
        load_clicked = st.button("Laai data", type="primary")

        if load_clicked:
            if uploaded_file is None:
                st.warning("Laai eers 'n Excel-lêer op voordat jy 'Laai data' klik.")
            else:
                df = load_data(uploaded_file)
                if df is not None and not df.empty:
                    st.session_state.df = df
                    st.session_state.file_name = uploaded_file.name
                    # Rerun so that the upload section disappears
                    st.rerun()
                else:
                    st.session_state.df = None
                    st.session_state.file_name = None

        # If still no data after possible click, stop here
        if st.session_state.df is None:
            st.info("Geen data gelaai nie. Laai 'n Excel-lêer op en klik **'Laai data'**.")
            return

    # ----------------------------
    # Data is loaded – show summary, no upload area
    # ----------------------------
    df = st.session_state.df

    st.success(
        f"Data gelaai uit: **{st.session_state.file_name}** "
        f"({len(df)} rye, {len(df.columns)} kolomme)"
    )

    # No global filters anymore – work with full dataset
    filtered_df = df.copy()

    if filtered_df.empty:
        st.warning("⚠️ Geen data beskikbaar nie.")
        return

    # ----------------------------
    # Tabs
    # ----------------------------
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "Bestuursoorsig",
            "Strategie",
            "Geografie",
            "Projekte & Eienaars",
            "Kwartaalvordering",
        ]
    )

    with tab1:
        render_executive_overview(filtered_df)

    with tab2:
        render_strategy_tab(filtered_df)

    with tab3:
        render_geography_tab(filtered_df)

    with tab4:
        render_projects_tab(filtered_df)

    with tab5:
        render_quarterly_progress_tab(filtered_df)


# --------------------------------------------------
# TAB 1 – EXECUTIVE OVERVIEW
# --------------------------------------------------

def render_executive_overview(df):
    """Tab 1: Executive Overview (Bestuursoorsig)."""
    st.header("Bestuursoorsig")

    col1, col2, col3 = st.columns(3)

    avg_behaal = df["% BEHAAL"].mean()

    with col1:
        st.metric("Gem. % BEHAAL (Algeheel)", format_percentage(avg_behaal))

    visie_grouped = calculate_group_metrics(df, "2030 TOEKOMSVISIE")
    fokus_grouped = calculate_group_metrics(df, "2026 FOKUS")

    # Beste 2030 Toekomsvisie op grond van hoogste Gem. % BEHAAL
    if not visie_grouped.empty:
        idx = visie_grouped["Gem. % BEHAAL"].idxmax()
        best_visie = visie_grouped.loc[idx]
        with col2:
            st.metric(
                "Beste 2030 Toekomsvisie",
                best_visie["2030 TOEKOMSVISIE"],
                format_percentage(best_visie["Gem. % BEHAAL"]),
            )

    # Beste 2026 Fokus op grond van hoogste Gem. % BEHAAL
    if not fokus_grouped.empty:
        idx = fokus_grouped["Gem. % BEHAAL"].idxmax()
        best_fokus = fokus_grouped.loc[idx]
        with col3:
            st.metric(
                "Beste 2026 Fokus",
                best_fokus["2026 FOKUS"],
                format_percentage(best_fokus["Gem. % BEHAAL"]),
            )

    st.subheader("Prestasie per 2030 Toekomsvisie")

    if not visie_grouped.empty:
        fig = px.bar(
            visie_grouped,
            x="2030 TOEKOMSVISIE",
            y="Gem. % BEHAAL",
            labels={"Gem. % BEHAAL": "Gemiddelde % Behaal", "2030 TOEKOMSVISIE": ""},
            hover_data={
                "Aantal KPI-items": True,
                "Gem. % BEHAAL": ":.1f",
                "Totale Teiken": ":,.0f",
                "Totale Uitset": ":,.0f",
            },
        )
        fig.update_layout(xaxis_tickangle=-45, height=400)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Prestasie per 2026 Fokus")

    if not fokus_grouped.empty:
        fig = px.bar(
            fokus_grouped,
            x="2026 FOKUS",
            y="Gem. % BEHAAL",
            labels={"Gem. % BEHAAL": "Gemiddelde % Behaal", "2026 FOKUS": ""},
            hover_data={
                "Aantal KPI-items": True,
                "Gem. % BEHAAL": ":.1f",
                "Totale Teiken": ":,.0f",
                "Totale Uitset": ":,.0f",
            },
        )
        fig.update_layout(xaxis_tickangle=-45, height=400)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top-5 Beste Ankerdorpe")

    anchor_grouped = (
        df.groupby("ANKERGEMEENSKAP")["% BEHAAL"].mean().reset_index()
    )
    anchor_grouped.columns = ["ANKERGEMEENSKAP", "Gem. % BEHAAL"]
    anchor_grouped = anchor_grouped.sort_values(
        "Gem. % BEHAAL", ascending=False
    ).head(5)

    if not anchor_grouped.empty:
        for _, row in anchor_grouped.iterrows():
            st.metric(row["ANKERGEMEENSKAP"], format_percentage(row["Gem. % BEHAAL"]))


# --------------------------------------------------
# TAB 2 – STRATEGY
# --------------------------------------------------

def render_strategy_tab(df):
    """Tab 2: Strategy (Strategie)."""
    st.header("Strategie")

    grouping_mode = st.radio(
        "Groepering", options=["2030 TOEKOMSVISIE", "2026 FOKUS"], horizontal=True
    )

    grouped = calculate_group_metrics(df, grouping_mode)

    st.subheader(f"Opsomming per {grouping_mode}")

    display_df = grouped.copy()
    display_df["Gem. % BEHAAL"] = display_df["Gem. % BEHAAL"].apply(format_percentage)
    display_df["Totale Teiken"] = display_df["Totale Teiken"].apply(format_number)
    display_df["Totale Uitset"] = display_df["Totale Uitset"].apply(format_number)

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    if grouped.empty:
        st.info("Geen data vir hierdie groepering nie.")
        return

    st.subheader("Detail per Groep")

    selected_group = st.selectbox(
        f"Kies {grouping_mode}", options=grouped[grouping_mode].tolist()
    )

    detail_df = df[df[grouping_mode] == selected_group][
        [
            "% BEHAAL",
            "BESKRYWING VAN PROJEK",
            "ANKERGEMEENSKAP",
            "PROVINSIE",
            "DISTRIK",
            "PROJEKEIENAAR",
            "TEIKEN",
            "UITSET",
            "KWARTAAL",
        ]
    ].copy()

    detail_df["% BEHAAL"] = detail_df["% BEHAAL"].apply(format_percentage)

    st.dataframe(detail_df, use_container_width=True, hide_index=True)
    st.caption(f"**{len(detail_df)}** items in {selected_group}")


# --------------------------------------------------
# TAB 3 – GEOGRAPHY
# --------------------------------------------------

def render_geography_tab(df):
    """Tab 3: Geography (Geografie)."""
    st.header("Geografie")

    # ---------- Prestasie per Streek ----------
    st.subheader("Prestasie per Streek")

    streek_grouped = calculate_group_metrics(df, "STREEK")

    streek_display = streek_grouped.copy()
    streek_display["Gem. % BEHAAL"] = streek_display["Gem. % BEHAAL"].apply(
        format_percentage
    )
    streek_display["Totale Teiken"] = streek_display["Totale Teiken"].apply(
        format_number
    )
    streek_display["Totale Uitset"] = streek_display["Totale Uitset"].apply(
        format_number
    )

    st.dataframe(streek_display, use_container_width=True, hide_index=True)

    # ---------- Prestasie per Provinsie ----------
    st.subheader("Prestasie per Provinsie")

    prov_grouped = calculate_group_metrics(df, "PROVINSIE")

    prov_display = prov_grouped.copy()
    prov_display["Gem. % BEHAAL"] = prov_display["Gem. % BEHAAL"].apply(
        format_percentage
    )
    prov_display["Totale Teiken"] = prov_display["Totale Teiken"].apply(format_number)
    prov_display["Totale Uitset"] = prov_display["Totale Uitset"].apply(format_number)

    st.dataframe(prov_display, use_container_width=True, hide_index=True)

    # ---------- Prestasie per Distrik (volledige lys) ----------
    st.subheader("Prestasie per Distrik")

    district_grouped = calculate_group_metrics(df, "DISTRIK")

    if not district_grouped.empty:
        dist_display = district_grouped.copy()
        dist_display["Gem. % BEHAAL"] = dist_display["Gem. % BEHAAL"].apply(
            format_percentage
        )
        dist_display["Totale Teiken"] = dist_display["Totale Teiken"].apply(
            format_number
        )
        dist_display["Totale Uitset"] = dist_display["Totale Uitset"].apply(
            format_number
        )

        st.dataframe(dist_display, use_container_width=True, hide_index=True)
    else:
        st.info("Geen distrik data beskikbaar nie.")

    # ---------- Prestasie per Ankergemeenskap (volledige lys) ----------
    st.subheader("Prestasie per Ankergemeenskap")

    anchor_grouped_metrics = calculate_group_metrics(df, "ANKERGEMEENSKAP")

    if not anchor_grouped_metrics.empty:
        anchor_display_metrics = anchor_grouped_metrics.copy()
        anchor_display_metrics["Gem. % BEHAAL"] = anchor_display_metrics[
            "Gem. % BEHAAL"
        ].apply(format_percentage)
        anchor_display_metrics["Totale Teiken"] = anchor_display_metrics[
            "Totale Teiken"
        ].apply(format_number)
        anchor_display_metrics["Totale Uitset"] = anchor_display_metrics[
            "Totale Uitset"
        ].apply(format_number)

        st.dataframe(anchor_display_metrics, use_container_width=True, hide_index=True)
    else:
        st.info("Geen ankergemeenskap data beskikbaar nie.")

    # ---------- Detail per Ankergemeenskap ----------
    st.subheader("Detail per Ankergemeenskap")

    all_anchors = sorted(df["ANKERGEMEENSKAP"].dropna().unique().tolist())
    if all_anchors:
        selected_anchor = st.selectbox("Kies Ankergemeenskap", options=all_anchors)

        anchor_detail = df[df["ANKERGEMEENSKAP"] == selected_anchor][
            [
                "% BEHAAL",
                "BESKRYWING VAN PROJEK",
                "2030 TOEKOMSVISIE",
                "2026 FOKUS",
                "PROVINSIE",
                "DISTRIK",
                "STREEK",
                "PROJEKEIENAAR",
                "TEIKEN",
                "UITSET",
                "KWARTAAL",
            ]
        ].copy()

        anchor_detail["% BEHAAL"] = anchor_detail["% BEHAAL"].apply(format_percentage)

        st.dataframe(anchor_detail, use_container_width=True, hide_index=True)
        st.caption(f"**{len(anchor_detail)}** items in {selected_anchor}")
    else:
        st.info("Geen ankergemeenskappe beskikbaar in die data nie.")


# --------------------------------------------------
# TAB 4 – PROJECTS & OWNERS
# --------------------------------------------------

def render_projects_tab(df):
    """Tab 4: Projects & Owners (Projekte & Eienaars)."""
    st.header("Projekte & Eienaars")

    st.subheader("Prestasie per Projekeienaar")

    owner_grouped = calculate_group_metrics(df, "PROJEKEIENAAR")

    owner_display = owner_grouped.copy()
    owner_display["Gem. % BEHAAL"] = owner_display["Gem. % BEHAAL"].apply(
        format_percentage
    )
    owner_display["Totale Teiken"] = owner_display["Totale Teiken"].apply(
        format_number
    )
    owner_display["Totale Uitset"] = owner_display["Totale Uitset"].apply(
        format_number
    )

    st.dataframe(owner_display, use_container_width=True, hide_index=True)

    st.subheader("Soek Projekte")

    # Three filters: search text, projekeienaar, distrik
    col1, col2, col3 = st.columns(3)

    with col1:
        search_text = st.text_input(
            "Soek in beskrywing, gemeenskap of eienaar:", ""
        )

    with col2:
        selected_owners = st.multiselect(
            "Filter op projekeienaar:",
            options=sorted(df["PROJEKEIENAAR"].unique()),
            default=[],
        )

    with col3:
        selected_districts = st.multiselect(
            "Filter op distrik:",
            options=sorted(df["DISTRIK"].unique()),
            default=[],
        )

    filtered_projects = df.copy()

    if search_text:
        mask = (
            filtered_projects["BESKRYWING VAN PROJEK"]
            .str.contains(search_text, case=False, na=False)
            | filtered_projects["ANKERGEMEENSKAP"].str.contains(
                search_text, case=False, na=False
            )
            | filtered_projects["PROJEKEIENAAR"].str.contains(
                search_text, case=False, na=False
            )
        )
        filtered_projects = filtered_projects[mask]

    if selected_owners:
        filtered_projects = filtered_projects[
            filtered_projects["PROJEKEIENAAR"].isin(selected_owners)
        ]

    if selected_districts:
        filtered_projects = filtered_projects[
            filtered_projects["DISTRIK"].isin(selected_districts)
        ]

    st.subheader(f"Projek Detail ({len(filtered_projects)} items)")

    project_detail = filtered_projects[
        [
            "% BEHAAL",
            "BESKRYWING VAN PROJEK",
            "2030 TOEKOMSVISIE",
            "2026 FOKUS",
            "ANKERGEMEENSKAP",
            "PROVINSIE",
            "DISTRIK",
            "STREEK",
            "PROJEKEIENAAR",
            "TEIKEN",
            "UITSET",
            "KWARTAAL",
        ]
    ].copy()

    project_detail = project_detail.sort_values("% BEHAAL")
    project_detail["% BEHAAL"] = project_detail["% BEHAAL"].apply(
        format_percentage
    )

    st.dataframe(project_detail, use_container_width=True, hide_index=True)


# --------------------------------------------------
# TAB 5 – QUARTERLY PROGRESS
# --------------------------------------------------

def render_quarterly_progress_tab(df):
    """Tab 5: Quarterly Progress (Kwartaalvordering)."""
    st.header("Kwartaalvordering")

    if df.empty:
        st.warning("⚠️ Geen data vir die gekose filters en kwartaal nie.")
        return

    # --- Summary per quarter ---
    quarter_summary = (
        df.groupby("KWARTAAL")["% BEHAAL"]
        .agg(["count", "mean"])
        .reset_index()
    )
    quarter_summary.columns = ["KWARTAAL", "Aantal KPI-items", "Gem. % BEHAAL"]

    completed_counts = (
        df[df["% BEHAAL"] >= 100]
        .groupby("KWARTAAL")
        .size()
        .reset_index(name="KPI-items voltooi (>=100%)")
    )
    quarter_summary = quarter_summary.merge(
        completed_counts, on="KWARTAAL", how="left"
    )
    quarter_summary["KPI-items voltooi (>=100%)"] = (
        quarter_summary["KPI-items voltooi (>=100%)"]
        .fillna(0)
        .astype(int)
    )

    quarter_summary["% KPI voltooi"] = (
        quarter_summary["KPI-items voltooi (>=100%)"]
        / quarter_summary["Aantal KPI-items"]
        * 100
    )

    quarter_order = ["K1", "K2", "K3", "K4"]
    quarter_summary["sort_order"] = quarter_summary["KWARTAAL"].apply(
        lambda x: quarter_order.index(x) if x in quarter_order else 999
    )
    quarter_summary = quarter_summary.sort_values("sort_order").drop(
        "sort_order", axis=1
    )

    st.subheader("Kwartaal Opsomming")

    display_summary = quarter_summary.copy()
    display_summary["Gem. % BEHAAL"] = display_summary["Gem. % BEHAAL"].apply(
        format_percentage
    )
    display_summary["% KPI voltooi"] = display_summary["% KPI voltooi"].apply(
        format_percentage
    )

    st.dataframe(display_summary, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Gem. % BEHAAL per Kwartaal")
        fig = px.bar(
            quarter_summary,
            x="KWARTAAL",
            y="Gem. % BEHAAL",
            labels={
                "Gem. % BEHAAL": "Gemiddelde % Behaal",
                "KWARTAAL": "Kwartaal",
            },
            hover_data={
                "Aantal KPI-items": True,
                "% KPI voltooi": ":.1f",
                "Gem. % BEHAAL": ":.1f",
            },
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("% KPI Voltooi per Kwartaal")
        fig = px.bar(
            quarter_summary,
            x="KWARTAAL",
            y="% KPI voltooi",
            labels={
                "% KPI voltooi": "% KPI Voltooi",
                "KWARTAAL": "Kwartaal",
            },
            hover_data={
                "Aantal KPI-items": True,
                "KPI-items voltooi (>=100%)": True,
                "% KPI voltooi": ":.1f",
            },
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Detail per Strategiese Groepering")

    grouping_choice = st.selectbox(
        "Groepering vir kwartaaldetail:",
        options=["2030 TOEKOMSVISIE", "2026 FOKUS"],
    )

    detail_summary = (
        df.groupby(["KWARTAAL", grouping_choice])["% BEHAAL"]
        .agg(["count", "mean"])
        .reset_index()
    )
    detail_summary.columns = [
        "KWARTAAL",
        grouping_choice,
        "Aantal KPI-items",
        "Gem. % BEHAAL",
    ]

    completed_detail = (
        df[df["% BEHAAL"] >= 100]
        .groupby(["KWARTAAL", grouping_choice])
        .size()
        .reset_index(name="KPI-items voltooi (>=100%)")
    )
    detail_summary = detail_summary.merge(
        completed_detail, on=["KWARTAAL", grouping_choice], how="left"
    )
    detail_summary["KPI-items voltooi (>=100%)"] = (
        detail_summary["KPI-items voltooi (>=100%)"]
        .fillna(0)
        .astype(int)
    )

    detail_summary["% KPI voltooi"] = (
        detail_summary["KPI-items voltooi (>=100%)"]
        / detail_summary["Aantal KPI-items"]
        * 100
    )

    quarter_order = ["K1", "K2", "K3", "K4"]
    detail_summary["sort_order"] = detail_summary["KWARTAAL"].apply(
        lambda x: quarter_order.index(x) if x in quarter_order else 999
    )
    detail_summary = detail_summary.sort_values(
        ["sort_order", grouping_choice]
    ).drop("sort_order", axis=1)

    display_detail = detail_summary.copy()
    display_detail["Gem. % BEHAAL"] = display_detail["Gem. % BEHAAL"].apply(
        format_percentage
    )
    display_detail["% KPI voltooi"] = display_detail["% KPI voltooi"].apply(
        format_percentage
    )

    st.dataframe(display_detail, use_container_width=True, hide_index=True)

    st.subheader(f"Gem. % BEHAAL per {grouping_choice} en Kwartaal")
    fig = px.bar(
        detail_summary,
        x=grouping_choice,
        y="Gem. % BEHAAL",
        color="KWARTAAL",
        barmode="group",
        labels={"Gem. % BEHAAL": "Gemiddelde % Behaal"},
        hover_data={
            "Aantal KPI-items": True,
            "% KPI voltooi": ":.1f",
            "Gem. % BEHAAL": ":.1f",
        },
    )
    fig.update_layout(xaxis_tickangle=-45, height=500)
    st.plotly_chart(fig, use_container_width=True)


# --------------------------------------------------
# ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    main()
