import streamlit as st
from utils.styling import apply_custom_css

from utils.data_loader import load_prepared_application_data
from utils.preprocessing import outlier_summary
from utils.filters import sidebar_filters, apply_filters
from utils.metrics import fmt_number, fmt_currency
from utils.charts import histogram, box_plot, scatter_chart

st.set_page_config(page_title="Outlier Analysis", layout="wide")
apply_custom_css()
st.title("Page 4 — Outlier & Distribution Analysis")
st.caption("**Business Objective:** identify unusual numerical values before deeper analysis, using the IQR method.")

VARIABLES = ["AMT_INCOME_TOTAL", "AMT_CREDIT", "AMT_ANNUITY", "AMT_GOODS_PRICE",
             "DAYS_BIRTH", "DAYS_EMPLOYED", "CNT_CHILDREN", "CNT_FAM_MEMBERS"]

df = load_prepared_application_data()
filters = sidebar_filters(df)
d = apply_filters(df, filters)

if d.empty:
    st.warning("No applicants match the selected filters.")
else:
    outliers = outlier_summary(d, VARIABLES)

    st.subheader("KPI Cards")
    cols = st.columns(5)
    cols[0].metric("Numerical Columns Analysed", fmt_number(len(VARIABLES)))
    cols[1].metric("Variables with Outliers", fmt_number((outliers["Outlier Count"] > 0).sum()))
    cols[2].metric("Maximum Income", fmt_currency(d["AMT_INCOME_TOTAL"].max()))
    cols[3].metric("Maximum Credit", fmt_currency(d["AMT_CREDIT"].max()))
    cols[4].metric("Maximum Annuity", fmt_currency(d["AMT_ANNUITY"].max()))

    st.subheader("IQR Outlier Summary")
    st.dataframe(outliers, use_container_width=True, hide_index=True)
    st.download_button("Download Outlier Summary", outliers.to_csv(index=False), "outlier_summary.csv", "text/csv")

    st.subheader("Visualizations")
    st.plotly_chart(histogram(d, "AMT_INCOME_TOTAL", "Income Distribution"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(box_plot(d, "AMT_INCOME_TOTAL", None, "Income Outliers"), use_container_width=True)
    with col2:
        st.plotly_chart(box_plot(d, "AMT_CREDIT", None, "Credit Outliers"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(box_plot(d, "AMT_ANNUITY", None, "Annuity Outliers"), use_container_width=True)
    with col2:
        st.plotly_chart(scatter_chart(d, "AMT_INCOME_TOTAL", "AMT_CREDIT", "REPAYMENT_STATUS", "Income vs Credit"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(box_plot(d, "CNT_FAM_MEMBERS", None, "Family Members Outliers"), use_container_width=True)
    with col2:
        st.plotly_chart(box_plot(d, "CNT_CHILDREN", None, "Children Count Outliers"), use_container_width=True)

    st.subheader("Techniques Discussed")
    st.markdown(
        """
        - **IQR Method** (used above): flags points beyond Q1 − 1.5×IQR or Q3 + 1.5×IQR.
        - **Percentile Capping / Winsorization**: cap extreme values at, e.g., the 1st/99th
          percentile instead of removing rows — preserves sample size.
        - **Log Transformation**: right-skewed money fields (income, credit) often become closer to
          normal on a log scale, which helps visual comparison without discarding any values.
        - **Business-rule validation**: some "outliers" are legitimate (a high-net-worth applicant),
          others are data-entry issues (e.g. income of 1 or a suspiciously round number repeated
          many times) — these require different treatment.
        """
    )

    st.subheader("Key Observations")
    top_outlier_col = outliers.sort_values("Outlier %", ascending=False).iloc[0]["Column"] if not outliers.empty else "N/A"
    st.markdown(
        f"""
        - **{top_outlier_col}** shows the highest outlier rate among the analysed variables by the
          IQR method.
        - Income and credit distributions are right-skewed, as expected for money fields — most
          customers cluster at lower/middle values with a long tail of high earners/large loans.
        - `CNT_FAM_MEMBERS` and `CNT_CHILDREN` outliers are mostly a small number of unusually large
          households rather than data errors — a business-rule cap (e.g. 10+) is more appropriate
          than blanket IQR removal for count variables.
        """
    )

    st.subheader("Business Insights")
    st.markdown(
        """
        - We do **not** automatically remove every flagged outlier: a customer with high income and
          a large loan is a true extreme customer, not a data error, and removing them would bias
          the portfolio view toward smaller loans only.
        - Distinguishing "true extreme customer" vs "data entry issue" vs "potentially invalid
          value" (e.g. income of exactly 0 or 1) should happen column-by-column with business input,
          not with a single blanket rule.
        """
    )

    st.subheader("Recommendations")
    st.markdown(
        """
        1. Apply **percentile capping (1st/99th)** rather than deletion for AMT_INCOME_TOTAL and
           AMT_CREDIT before any cross-page averages, so a handful of extreme values don't distort
           portfolio-level KPIs.
        2. Flag (don't silently drop) applications with `AMT_INCOME_TOTAL` values that look like
           data-entry errors (e.g. round-number repeats) for manual review.
        3. Keep count-variable outliers (family size, children) as-is unless they exceed a
           business-defined maximum household size, since these are typically valid.
        """
    )
