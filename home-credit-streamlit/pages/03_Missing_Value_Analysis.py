import streamlit as st
from utils.styling import apply_custom_css
import plotly.express as px

from utils.data_loader import load_application_raw
from utils.preprocessing import missing_value_summary, missing_bucket, suggest_treatment
from utils.metrics import fmt_number, fmt_pct
from utils.charts import category_heatmap

st.set_page_config(page_title="Missing Value Analysis", layout="wide")
apply_custom_css()
st.title("Page 3 — Missing Value Analysis")
st.caption("**Business Objective:** perform detailed missing-data EDA to decide a preprocessing strategy per column.")
st.caption("This page profiles the raw, unfiltered dataset.")

df = load_application_raw()
summary = missing_value_summary(df)
summary["Bucket"] = summary["Missing %"].apply(missing_bucket)
summary["Suggested Treatment"] = summary.apply(lambda r: suggest_treatment(r["Missing %"], r["Data Type"]), axis=1)

total_missing = int(summary["Missing Count"].sum())
total_cells = df.shape[0] * df.shape[1]

st.subheader("KPI Cards")
cols = st.columns(5)
cols[0].metric("Total Missing Values", fmt_number(total_missing))
cols[1].metric("Missing Percentage", fmt_pct(total_missing / total_cells * 100))
cols[2].metric("Columns with Missing Data", fmt_number(len(summary)))
cols[3].metric("Columns Above 30% Missing", fmt_number((summary["Missing %"] > 30).sum()))
cols[4].metric("Columns Above 50% Missing", fmt_number((summary["Missing %"] > 50).sum()))

st.subheader("Visualizations")
top20 = summary.head(20)
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(px.bar(top20, y="Column", x="Missing %", orientation="h", title="Top 20 Columns by Missing Percentage"), use_container_width=True)
with col2:
    st.plotly_chart(px.histogram(summary, x="Missing %", nbins=20, title="Missing Percentage Distribution (across columns)"), use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    heatmap_cols = top20["Column"].tolist()
    if heatmap_cols:
        sample = df[heatmap_cols].isna().astype(int).sample(min(300, len(df)), random_state=42)
        fig = px.imshow(sample.T, aspect="auto", title="Missingness Heatmap (row sample, top 20 columns)", color_continuous_scale="Reds")
        st.plotly_chart(fig, use_container_width=True)
with col2:
    by_dtype = summary.groupby("Data Type")["Missing Count"].sum().reset_index()
    st.plotly_chart(px.bar(by_dtype, x="Data Type", y="Missing Count", title="Missing Values by Data Type"), use_container_width=True)

st.subheader("Missing Values by Category Group")
bucket_counts = summary["Bucket"].value_counts().reindex(
    ["0-5% Missing", "5-20% Missing", "20-40% Missing", "40-60% Missing", "60%+ Missing"]
).fillna(0).reset_index()
bucket_counts.columns = ["Missing Bucket", "Column Count"]
st.plotly_chart(px.bar(bucket_counts, x="Missing Bucket", y="Column Count", title="Columns Grouped by Missing %"), use_container_width=True)

st.subheader("Detailed Missing Value Table & Preprocessing Recommendations")
st.dataframe(summary[["Column", "Missing Count", "Missing %", "Data Type", "Bucket", "Suggested Treatment"]], use_container_width=True, hide_index=True)
st.download_button("Download Missing Value Report", summary.to_csv(index=False), "missing_value_report.csv", "text/csv")

st.subheader("Key Observations")
st.markdown(
    f"""
    - **{(summary['Missing %'] > 50).sum()} columns** exceed 50% missingness and are strong drop
      candidates unless individually business-critical.
    - Most severely missing columns are building/apartment-quality fields (e.g. COMMONAREA_*),
      which are structurally missing for renters rather than randomly missing — this is Missing Not
      At Random (MNAR), not Missing Completely At Random.
    - Core financial fields (AMT_INCOME_TOTAL, AMT_CREDIT, AMT_ANNUITY) have very low missingness,
      which is good — these drive most downstream ratio features.
    """
)

st.subheader("Business Insights")
st.markdown(
    """
    - Because building-quality missingness correlates with housing type, dropping those columns
      outright would silently remove housing-related signal — a missing indicator preserves it
      without requiring a (likely wrong) imputed value.
    - Prioritizing data-collection fixes for high-missing fields that also show up in later
      affordability/risk pages (e.g. OCCUPATION_TYPE) has more downstream analytical value than
      fixing high-missing fields nobody uses.
    """
)

st.subheader("Recommendations")
st.markdown(
    """
    1. Drop columns above 60% missing that are not referenced by later dashboard pages.
    2. For 20–60% missing columns used in EDA (e.g. OCCUPATION_TYPE), retain and add a missing
       indicator instead of imputing a category that wasn't observed.
    3. For under-20%-missing numeric fields, impute with the median (robust to the outliers seen
       on the Outlier Analysis page) rather than the mean.
    4. Re-run this missing-value report after each new table join in later pages, since merges can
       introduce new missingness (customers absent from a related table).
    """
)
