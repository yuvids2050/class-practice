import streamlit as st
from utils.styling import apply_custom_css

from utils.data_loader import load_prepared_application_data
from utils.filters import sidebar_filters, apply_filters
from utils.metrics import portfolio_kpis, fmt_currency, fmt_pct, fmt_number, top_bottom_by_default_rate
from utils.charts import bar_chart, donut_chart, histogram, treemap_chart, horizontal_bar_chart, scatter_chart

st.set_page_config(page_title="Executive Overview", layout="wide")
apply_custom_css()
st.title("Page 1 — Executive Portfolio Overview")
st.caption("**Business Objective:** provide management with a high-level overview of the Home Credit loan portfolio.")

df = load_prepared_application_data()
filters = sidebar_filters(df)
d = apply_filters(df, filters)

if d.empty:
    st.warning("No applicants match the selected filters.")
else:
    m = portfolio_kpis(d)

    st.subheader("KPI Cards")
    cols = st.columns(4)
    cols[0].metric("Total Customers", fmt_number(m["total_customers"]))
    cols[1].metric("Total Applications", fmt_number(m["total_applications"]))
    cols[2].metric("Default Customers", fmt_number(m["default_customers"]))
    cols[3].metric("Non-Default Customers", fmt_number(m["non_default_customers"]))
    cols = st.columns(4)
    cols[0].metric("Default Rate", fmt_pct(m["default_rate"]))
    cols[1].metric("Total Credit Amount", fmt_currency(m["total_credit"]))
    cols[2].metric("Average Credit Amount", fmt_currency(m["avg_credit"]))
    cols[3].metric("Average Customer Income", fmt_currency(m["avg_income"]))
    cols = st.columns(4)
    cols[0].metric("Average Annuity", fmt_currency(m["avg_annuity"]))
    cols[1].metric("Average Goods Price", fmt_currency(m["avg_goods_price"]))
    cols[2].metric("Median Income", fmt_currency(m["median_income"]))
    cols[3].metric("Median Credit Amount", fmt_currency(m["median_credit"]))

    st.subheader("Visualizations")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(bar_chart(d, "REPAYMENT_STATUS", "TARGET", "Default vs Non-Default", aggfunc="count"), use_container_width=True)
    with col2:
        st.plotly_chart(donut_chart(d, "REPAYMENT_STATUS", "Default Percentage"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(bar_chart(d, "NAME_CONTRACT_TYPE", "TARGET", "Applications by Contract Type", aggfunc="count"), use_container_width=True)
    with col2:
        st.plotly_chart(histogram(d, "AMT_CREDIT", "Credit Amount Distribution"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(histogram(d, "AMT_INCOME_TOTAL", "Income Distribution"), use_container_width=True)
    with col2:
        st.plotly_chart(treemap_chart(d, ["NAME_INCOME_TYPE"], "AMT_CREDIT", "Credit by Income Type"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(horizontal_bar_chart(d, "NAME_INCOME_TYPE", "TARGET", "Default Rate by Income Type", aggfunc="mean", ascending=False), use_container_width=True)
    with col2:
        st.plotly_chart(scatter_chart(d, "AMT_INCOME_TOTAL", "AMT_CREDIT", "REPAYMENT_STATUS", "Income vs Credit"), use_container_width=True)

    st.subheader("Detailed Data Table")
    display_cols = ["SK_ID_CURR", "TARGET", "NAME_CONTRACT_TYPE", "CODE_GENDER", "AGE_YEARS",
                     "NAME_EDUCATION_TYPE", "NAME_INCOME_TYPE", "AMT_INCOME_TOTAL", "AMT_CREDIT", "AMT_ANNUITY"]
    st.dataframe(d[display_cols].sort_values("SK_ID_CURR"), use_container_width=True, hide_index=True)
    st.download_button("Download Filtered Dataset", d[display_cols].to_csv(index=False), "executive_overview_filtered.csv", "text/csv")

    highest_risk_income, _ = top_bottom_by_default_rate(d, "NAME_INCOME_TYPE", min_count=5)
    largest_segment = d["NAME_INCOME_TYPE"].mode()[0]

    st.subheader("Key Observations")
    st.markdown(
        f"""
        - Overall default rate across the filtered portfolio is **{fmt_pct(m['default_rate'])}**.
        - Total credit exposure across these customers is **{fmt_currency(m['total_credit'])}**.
        - The largest customer segment by income type is **{largest_segment}**.
        - The income type showing the highest observed default rate is **{highest_risk_income}**.
        - Typical (median) credit amount is **{fmt_currency(m['median_credit'])}**, typical income is **{fmt_currency(m['median_income'])}**.
        """
    )

    st.subheader("Business Insights")
    st.markdown(
        """
        - Default rate alone understates risk exposure — the same rate applied to a larger credit
          amount represents materially higher potential loss, so exposure (₹ at risk) should be
          tracked alongside the rate.
        - Concentration in a single income-type segment increases sensitivity to shocks affecting
          that segment specifically (e.g. sector-wide layoffs for "Working" applicants).
        """
    )

    st.subheader("Recommendations")
    st.markdown(
        """
        1. Track **default rate and credit exposure together** in portfolio reporting, not default
           rate alone — a small high-risk segment with large loans can matter more than a large
           low-risk one.
        2. Set **segment-specific monitoring thresholds** for the income types showing elevated
           default rates rather than a single portfolio-wide threshold.
        3. Review underwriting policy for the largest customer segment periodically, since it drives
           the majority of portfolio-level metrics.
        """
    )
