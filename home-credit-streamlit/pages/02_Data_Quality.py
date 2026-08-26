import streamlit as st
from utils.styling import apply_custom_css
import plotly.express as px

from utils.data_loader import load_application_raw
from utils.preprocessing import dataset_overview, column_profile, duplicate_summary
from utils.metrics import fmt_number
from utils.charts import bar_chart, gauge_chart

st.set_page_config(page_title="Data Quality", layout="wide")
apply_custom_css()
st.title("Page 2 — Data Quality Dashboard")
st.caption("**Business Objective:** show the overall quality of the raw Home Credit application data before any cleaning.")
st.caption("This page profiles the raw, unfiltered dataset (data quality should be assessed before filters are applied).")

df = load_application_raw()
overview = dataset_overview(df)
profile = column_profile(df)
dup = duplicate_summary(df)

st.subheader("KPI Cards")
cols = st.columns(4)
cols[0].metric("Number of Rows", fmt_number(overview["rows"]))
cols[1].metric("Number of Columns", fmt_number(overview["columns"]))
cols[2].metric("Numerical Columns", fmt_number(overview["numeric_columns"]))
cols[3].metric("Categorical Columns", fmt_number(overview["categorical_columns"]))
cols = st.columns(4)
cols[0].metric("Missing Cells", fmt_number(overview["missing_cells"]))
cols[1].metric("Duplicate Rows", fmt_number(overview["duplicate_rows"]))
cols[2].metric("Total Memory Usage", f"{overview['memory_usage_mb']:.2f} MB")
cols[3].metric("Unique Customers", fmt_number(overview["unique_customers"]))

st.subheader("Column Profile Table")
st.dataframe(profile, use_container_width=True, hide_index=True)
st.download_button("Download Column Profile", profile.to_csv(index=False), "column_profile.csv", "text/csv")

st.subheader("Visualizations")
col1, col2 = st.columns(2)
with col1:
    dtype_counts = df.dtypes.astype(str).value_counts().reset_index()
    dtype_counts.columns = ["Data Type", "Column Count"]
    st.plotly_chart(px.bar(dtype_counts, x="Data Type", y="Column Count", title="Column Data Types"), use_container_width=True)
with col2:
    total_cells = overview["rows"] * overview["columns"]
    stacked = px.bar(
        x=["Available", "Missing"], y=[total_cells - overview["missing_cells"], overview["missing_cells"]],
        title="Missing vs Available Data (all cells)", labels={"x": "", "y": "Cell Count"},
    )
    st.plotly_chart(stacked, use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    top_unique = profile.sort_values("Unique Values", ascending=False).head(15)
    st.plotly_chart(px.bar(top_unique, y="Column Name", x="Unique Values", orientation="h", title="Top 15 Columns by Unique Values"), use_container_width=True)
with col2:
    completeness = 100 - (overview["missing_cells"] / total_cells * 100)
    st.plotly_chart(gauge_chart(round(completeness, 1), "Dataset Completeness"), use_container_width=True)

st.subheader("Required Analysis")
worst_quality = profile.sort_values("Missing %", ascending=False).head(5)["Column Name"].tolist()
dtype_flags = profile[(profile["Data Type"] == "object") & (profile["Unique Values"] <= 3)]["Column Name"].tolist()
st.markdown(
    f"""
    - **Columns with the most severe missingness:** {', '.join(worst_quality)}.
    - **Duplicate customer IDs present:** {'Yes' if dup['duplicate_ids'] else 'No'} — SK_ID_CURR is
      {'unique' if dup['id_is_unique'] else 'NOT unique'} in this file.
    - **Full-row duplicates:** {fmt_number(dup['full_row_duplicates'])}.
    - **Low-cardinality categorical columns worth checking for inconsistent labels** (e.g. stray
      whitespace, casing): {', '.join(dtype_flags[:8]) if dtype_flags else 'none flagged'}.
    - Columns above 60% missing are candidates to drop; columns between 20-60% missing are
      candidates for a "missing indicator" flag rather than outright imputation, since missingness
      itself can carry signal (e.g. building-quality fields are missing mainly for renters, not owners).
    """
)

st.subheader("Recommendation")
st.markdown(
    """
    **Preprocessing strategy:** drop columns above ~60% missing unless business-critical; for
    columns between 20-60% missing, add a missing-indicator flag before imputing; for columns
    under 20% missing, impute with median (numeric) or mode (categorical). Validate that
    `SK_ID_CURR` remains unique after every join in later pages.
    """
)
