import streamlit as st
from utils.styling import apply_custom_css

from utils.data_loader import load_prepared_application_data
from utils.filters import sidebar_filters, apply_filters
from utils.metrics import correlation_with_target
from utils.charts import bar_chart, correlation_heatmap

st.set_page_config(page_title="Risk Factor Exploration", layout="wide")
apply_custom_css()
st.title("Page 12 — Risk Factor Exploration")
st.caption("**Business Objective:** study variables showing meaningful relationships with default.")

NUMERIC_FACTORS = [
    "TARGET", "AGE_YEARS", "AMT_INCOME_TOTAL", "AMT_CREDIT", "AMT_ANNUITY", "EMPLOYMENT_YEARS",
    "CNT_FAM_MEMBERS", "CREDIT_TO_INCOME", "ANNUITY_TO_INCOME", "EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3",
]

df = load_prepared_application_data()
filters = sidebar_filters(df)
d = apply_filters(df, filters)

if d.empty:
    st.warning("No applicants match the selected filters.")
else:
    st.subheader("Visualizations")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(bar_chart(d, "AGE_GROUP", "TARGET", "Age Group vs Default Rate", aggfunc="mean"), use_container_width=True)
    with col2:
        st.plotly_chart(bar_chart(d, "CREDIT_BAND", "TARGET", "Credit Band vs Default Rate", aggfunc="mean"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(bar_chart(d, "INCOME_GROUP", "TARGET", "Income Band vs Default Rate", aggfunc="mean"), use_container_width=True)
    with col2:
        st.plotly_chart(bar_chart(d, "EMPLOYMENT_GROUP", "TARGET", "Employment Band vs Default Rate", aggfunc="mean"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(bar_chart(d, "CREDIT_TO_INCOME_BAND", "TARGET", "Credit-to-Income Band vs Default", aggfunc="mean"), use_container_width=True)
    with col2:
        st.plotly_chart(bar_chart(d, "ANNUITY_TO_INCOME_BAND", "TARGET", "Annuity-to-Income Band vs Default", aggfunc="mean"), use_container_width=True)

    available_cols = [c for c in NUMERIC_FACTORS if c in d.columns]
    corr_matrix = d[available_cols].corr(numeric_only=True)
    st.plotly_chart(correlation_heatmap(corr_matrix, "Correlation Heatmap — Candidate Risk Factors"), use_container_width=True)

    target_corr = correlation_with_target(d, NUMERIC_FACTORS)
    st.subheader("Correlation with TARGET (ranked)")
    st.dataframe(target_corr.reset_index().rename(columns={"index": "Factor", "TARGET": "Correlation with TARGET"}), use_container_width=True, hide_index=True)
    st.download_button("Download Correlation Table", target_corr.reset_index().to_csv(index=False), "risk_factor_correlations.csv", "text/csv")

    st.subheader("Important Rule")
    st.info("**Correlation does not prove causation.** The observations below describe relationships found in this data, not causal claims.")

    top_factor = target_corr.abs().idxmax() if not target_corr.empty else "N/A"

    st.subheader("Key Observations")
    st.markdown(
        f"""
        - **{top_factor}** shows the strongest observed (positive or negative) correlation with
          TARGET among the numeric factors examined here.
        - External credit-bureau scores (EXT_SOURCE_1/2/3), where present, tend to show a negative
          relationship with TARGET — higher external score, lower observed default rate.
        - Band-level views (age, credit, income, employment, affordability ratios) confirm the risk
          is not linear or uniform — it concentrates at specific band edges rather than trending
          smoothly.
        """
    )

    st.subheader("Business Insights")
    st.markdown(
        """
        - A variable correlating with TARGET is a candidate for closer underwriting attention, not
          proof that changing it changes risk — e.g. age correlating with default doesn't mean age
          itself causes default; it may proxy for employment stability or credit history length.
        - Combining several moderately-correlated factors (age band + credit-to-income band +
          employment band) into a segmentation view, as done on the Risk Segmentation page, is more
          informative than any single factor alone.
        """
    )

    st.subheader("Recommendations")
    st.markdown(
        """
        1. Use the ranked correlation table to prioritize which factors get closer manual-review
           attention — strongest observed relationships first.
        2. Re-validate these correlations periodically; relationships found in one time period/
           portfolio mix are not guaranteed to hold as the customer base shifts.
        3. Avoid presenting any single correlated factor as a "cause" of default in business
           communications — describe it as an observed association.
        """
    )
