import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="KPI Dashboard", layout="wide", initial_sidebar_state="collapsed")

@st.cache_data
def load_data():
    """Load and prepare the Excel data."""
    try:
        df = pd.read_excel("attached_assets/00 GEKONSOLIDEER copy_1763538344798.xlsx", sheet_name="2026 BEPLANNING")
        
        df['TEIKEN'] = pd.to_numeric(df['TEIKEN'], errors='coerce')
        df['UITSET'] = pd.to_numeric(df['UITSET'], errors='coerce')
        df['% BEHAAL'] = pd.to_numeric(df['% BEHAAL'], errors='coerce')
        
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].fillna('Onbekend')
        
        return df
    except Exception as e:
        st.error(f"Fout met die laai van data: {e}")
        return None

def apply_filters(df, kwartaal_filter, provinsie_filter, fokus_filter, visie_filter):
    """Apply global filters to the dataframe."""
    filtered_df = df.copy()
    
    if kwartaal_filter and len(kwartaal_filter) > 0:
        filtered_df = filtered_df[filtered_df['KWARTAAL'].isin(kwartaal_filter)]
    
    if provinsie_filter and len(provinsie_filter) > 0:
        filtered_df = filtered_df[filtered_df['PROVINSIE'].isin(provinsie_filter)]
    
    if fokus_filter and len(fokus_filter) > 0:
        filtered_df = filtered_df[filtered_df['2026 FOKUS'].isin(fokus_filter)]
    
    if visie_filter and len(visie_filter) > 0:
        filtered_df = filtered_df[filtered_df['2030 TOEKOMSVISIE'].isin(visie_filter)]
    
    return filtered_df

def calculate_group_metrics(df, group_col):
    """Calculate aggregated metrics for a grouping column."""
    grouped = df.groupby(group_col).agg({
        '% BEHAAL': ['mean', 'min', 'max', 'count'],
        'TEIKEN': 'sum',
        'UITSET': 'sum'
    }).reset_index()
    
    grouped.columns = [group_col, 'Gem. % BEHAAL', 'Min % BEHAAL', 'Maks % BEHAAL', 'Aantal KPI-items', 'Totale Teiken', 'Totale Uitset']
    grouped = grouped.sort_values('Gem. % BEHAAL')
    
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

def main():
    st.title("GMS Oorsigpaneel")
    
    df = load_data()
    
    if df is None or df.empty:
        st.error("Geen data beskikbaar nie.")
        return
    
    st.sidebar.header("🔍 Globale Filters")
    
    all_kwartale = sorted([k for k in df['KWARTAAL'].unique() if k != 'Onbekend'])
    kwartaal_filter = st.sidebar.multiselect(
        "Kwartaal",
        options=all_kwartale,
        default=all_kwartale
    )
    
    all_provinsies = sorted([p for p in df['PROVINSIE'].unique() if p != 'Onbekend'])
    provinsie_filter = st.sidebar.multiselect(
        "Provinsie",
        options=all_provinsies,
        default=all_provinsies
    )
    
    all_fokus = sorted([f for f in df['2026 FOKUS'].unique() if f != 'Onbekend'])
    fokus_filter = st.sidebar.multiselect(
        "2026 Fokus",
        options=all_fokus,
        default=all_fokus
    )
    
    all_visie = sorted([v for v in df['2030 TOEKOMSVISIE'].unique() if v != 'Onbekend'])
    visie_filter = st.sidebar.multiselect(
        "2030 Toekomsvisie",
        options=all_visie,
        default=all_visie
    )
    
    filtered_df = apply_filters(df, kwartaal_filter, provinsie_filter, fokus_filter, visie_filter)
    
    if filtered_df.empty:
        st.warning("⚠️ Geen data vir die huidige filters nie.")
        return
    
    tab1, tab2, tab3, tab4 = st.tabs(["Bestuursoorsig", "Strategie", "Geografie", "Projekte & Eienaars"])
    
    with tab1:
        render_executive_overview(filtered_df)
    
    with tab2:
        render_strategy_tab(filtered_df)
    
    with tab3:
        render_geography_tab(filtered_df)
    
    with tab4:
        render_projects_tab(filtered_df)

def render_executive_overview(df):
    """Tab 1: Executive Overview (Bestuursoorsig)."""
    st.header("Bestuursoorsig")
    
    col1, col2, col3 = st.columns(3)
    
    avg_behaal = df['% BEHAAL'].mean()
    
    with col1:
        st.metric("Gem. % BEHAAL (Algeheel)", format_percentage(avg_behaal))
    
    visie_grouped = calculate_group_metrics(df, '2030 TOEKOMSVISIE')
    fokus_grouped = calculate_group_metrics(df, '2026 FOKUS')
    
    if not visie_grouped.empty:
        best_visie = visie_grouped.iloc[-1]
        
        with col2:
            st.metric(
                "Beste 2030 Toekomsvisie",
                best_visie['2030 TOEKOMSVISIE'],
                f"{best_visie['Gem. % BEHAAL']:.1f}%"
            )
    
    if not fokus_grouped.empty:
        best_fokus = fokus_grouped.iloc[-1]
        
        with col3:
            st.metric(
                "Beste 2026 Fokus",
                best_fokus['2026 FOKUS'],
                f"{best_fokus['Gem. % BEHAAL']:.1f}%"
            )
    
    st.subheader("Prestasie per 2030 Toekomsvisie")
    
    if not visie_grouped.empty:
        fig = px.bar(
            visie_grouped,
            x='2030 TOEKOMSVISIE',
            y='Gem. % BEHAAL',
            title='',
            labels={'Gem. % BEHAAL': 'Gemiddelde % Behaal', '2030 TOEKOMSVISIE': ''},
            hover_data={
                'Aantal KPI-items': True,
                'Min % BEHAAL': ':.1f',
                'Maks % BEHAAL': ':.1f',
                'Gem. % BEHAAL': ':.1f',
                'Totale Teiken': ':,.0f',
                'Totale Uitset': ':,.0f'
            }
        )
        fig.update_layout(xaxis_tickangle=-45, height=400)
        st.plotly_chart(fig, width='stretch')
    
    st.subheader("Prestasie per 2026 Fokus")
    
    if not fokus_grouped.empty:
        fig = px.bar(
            fokus_grouped,
            x='2026 FOKUS',
            y='Gem. % BEHAAL',
            title='',
            labels={'Gem. % BEHAAL': 'Gemiddelde % Behaal', '2026 FOKUS': ''},
            hover_data={
                'Aantal KPI-items': True,
                'Min % BEHAAL': ':.1f',
                'Maks % BEHAAL': ':.1f',
                'Gem. % BEHAAL': ':.1f',
                'Totale Teiken': ':,.0f',
                'Totale Uitset': ':,.0f'
            }
        )
        fig.update_layout(xaxis_tickangle=-45, height=400)
        st.plotly_chart(fig, width='stretch')
    
    st.subheader("Top-5 Beste Ankerdorpe")
    
    anchor_grouped = df.groupby('ANKERGEMEENSKAP').agg({
        '% BEHAAL': 'mean'
    }).reset_index()
    
    anchor_grouped.columns = ['ANKERGEMEENSKAP', 'Gem. % BEHAAL']
    anchor_grouped = anchor_grouped.sort_values('Gem. % BEHAAL', ascending=False).head(5)
    
    if not anchor_grouped.empty:
        for idx, row in anchor_grouped.iterrows():
            st.metric(
                row['ANKERGEMEENSKAP'],
                format_percentage(row['Gem. % BEHAAL'])
            )

def render_strategy_tab(df):
    """Tab 2: Strategy (Strategie)."""
    st.header("Strategie")
    
    grouping_mode = st.radio(
        "Groepering",
        options=['2030 TOEKOMSVISIE', '2026 FOKUS'],
        horizontal=True
    )
    
    grouped = calculate_group_metrics(df, grouping_mode)
    
    st.subheader(f"Opsomming per {grouping_mode}")
    
    display_df = grouped.copy()
    display_df['Gem. % BEHAAL'] = display_df['Gem. % BEHAAL'].apply(format_percentage)
    display_df['Min % BEHAAL'] = display_df['Min % BEHAAL'].apply(format_percentage)
    display_df['Maks % BEHAAL'] = display_df['Maks % BEHAAL'].apply(format_percentage)
    display_df['Totale Teiken'] = display_df['Totale Teiken'].apply(format_number)
    display_df['Totale Uitset'] = display_df['Totale Uitset'].apply(format_number)
    
    st.dataframe(display_df, width='stretch', hide_index=True)
    
    st.subheader("Detail per Groep")
    
    selected_group = st.selectbox(
        f"Kies {grouping_mode}",
        options=grouped[grouping_mode].tolist()
    )
    
    detail_df = df[df[grouping_mode] == selected_group][
        ['% BEHAAL', 'BESKRYWING VAN PROJEK', 'ANKERGEMEENSKAP', 'PROVINSIE', 'DISTRIK', 'PROJEKEIENAAR', 'TEIKEN', 'UITSET', 'KWARTAAL']
    ].copy()
    
    detail_df['% BEHAAL'] = detail_df['% BEHAAL'].apply(format_percentage)
    
    st.dataframe(detail_df, width='stretch', hide_index=True)
    st.caption(f"**{len(detail_df)}** items in {selected_group}")

def render_geography_tab(df):
    """Tab 3: Geography (Geografie)."""
    st.header("Geografie")
    
    st.subheader("Prestasie per Provinsie")
    
    prov_grouped = calculate_group_metrics(df, 'PROVINSIE')
    
    prov_display = prov_grouped.copy()
    prov_display['Gem. % BEHAAL'] = prov_display['Gem. % BEHAAL'].apply(format_percentage)
    prov_display['Min % BEHAAL'] = prov_display['Min % BEHAAL'].apply(format_percentage)
    prov_display['Maks % BEHAAL'] = prov_display['Maks % BEHAAL'].apply(format_percentage)
    prov_display['Totale Teiken'] = prov_display['Totale Teiken'].apply(format_number)
    prov_display['Totale Uitset'] = prov_display['Totale Uitset'].apply(format_number)
    
    st.dataframe(prov_display, width='stretch', hide_index=True)
    
    selected_province = st.selectbox(
        "Kies provinsie vir detail:",
        options=prov_grouped['PROVINSIE'].tolist()
    )
    
    province_df = df[df['PROVINSIE'] == selected_province]
    
    st.subheader(f"Distrikte in {selected_province}")
    
    district_grouped = calculate_group_metrics(province_df, 'DISTRIK')
    
    if not district_grouped.empty:
        dist_display = district_grouped.copy()
        dist_display['Gem. % BEHAAL'] = dist_display['Gem. % BEHAAL'].apply(format_percentage)
        dist_display['Min % BEHAAL'] = dist_display['Min % BEHAAL'].apply(format_percentage)
        dist_display['Maks % BEHAAL'] = dist_display['Maks % BEHAAL'].apply(format_percentage)
        dist_display['Totale Teiken'] = dist_display['Totale Teiken'].apply(format_number)
        dist_display['Totale Uitset'] = dist_display['Totale Uitset'].apply(format_number)
        
        st.dataframe(dist_display, width='stretch', hide_index=True)
    else:
        st.info("Geen distrik data beskikbaar nie.")
    
    st.subheader(f"Ankergemeenskappe in {selected_province}")
    
    anchor_grouped = province_df.groupby('ANKERGEMEENSKAP').agg({
        '% BEHAAL': ['mean', 'count']
    }).reset_index()
    
    anchor_grouped.columns = ['ANKERGEMEENSKAP', 'Gem. % BEHAAL', 'Aantal KPI-items']
    anchor_grouped = anchor_grouped.sort_values('Gem. % BEHAAL')
    
    if not anchor_grouped.empty:
        anchor_display = anchor_grouped.copy()
        anchor_display['Gem. % BEHAAL'] = anchor_display['Gem. % BEHAAL'].apply(format_percentage)
        
        st.dataframe(anchor_display, width='stretch', hide_index=True)
    else:
        st.info("Geen ankergemeenskap data beskikbaar nie.")

def render_projects_tab(df):
    """Tab 4: Projects & Owners (Projekte & Eienaars)."""
    st.header("Projekte & Eienaars")
    
    st.subheader("Prestasie per Projekeienaar")
    
    owner_grouped = calculate_group_metrics(df, 'PROJEKEIENAAR')
    
    owner_display = owner_grouped.copy()
    owner_display['Gem. % BEHAAL'] = owner_display['Gem. % BEHAAL'].apply(format_percentage)
    owner_display['Min % BEHAAL'] = owner_display['Min % BEHAAL'].apply(format_percentage)
    owner_display['Maks % BEHAAL'] = owner_display['Maks % BEHAAL'].apply(format_percentage)
    owner_display['Totale Teiken'] = owner_display['Totale Teiken'].apply(format_number)
    owner_display['Totale Uitset'] = owner_display['Totale Uitset'].apply(format_number)
    
    st.dataframe(owner_display, width='stretch', hide_index=True)
    
    st.subheader("Soek Projekte")
    
    col1, col2 = st.columns(2)
    
    with col1:
        search_text = st.text_input("Soek in beskrywing, gemeenskap of eienaar:", "")
    
    with col2:
        selected_owners = st.multiselect(
            "Filter op projekeienaar:",
            options=sorted(df['PROJEKEIENAAR'].unique()),
            default=[]
        )
    
    filtered_projects = df.copy()
    
    if search_text:
        mask = (
            filtered_projects['BESKRYWING VAN PROJEK'].str.contains(search_text, case=False, na=False) |
            filtered_projects['ANKERGEMEENSKAP'].str.contains(search_text, case=False, na=False) |
            filtered_projects['PROJEKEIENAAR'].str.contains(search_text, case=False, na=False)
        )
        filtered_projects = filtered_projects[mask]
    
    if selected_owners:
        filtered_projects = filtered_projects[filtered_projects['PROJEKEIENAAR'].isin(selected_owners)]
    
    st.subheader(f"Projek Detail ({len(filtered_projects)} items)")
    
    project_detail = filtered_projects[
        ['% BEHAAL', 'BESKRYWING VAN PROJEK', '2030 TOEKOMSVISIE', '2026 FOKUS', 
         'ANKERGEMEENSKAP', 'PROVINSIE', 'DISTRIK', 'STREEK', 'PROJEKEIENAAR', 
         'TEIKEN', 'UITSET', 'KWARTAAL']
    ].copy()
    
    project_detail = project_detail.sort_values('% BEHAAL')
    project_detail['% BEHAAL'] = project_detail['% BEHAAL'].apply(format_percentage)
    
    st.dataframe(project_detail, width='stretch', hide_index=True)

if __name__ == "__main__":
    main()
