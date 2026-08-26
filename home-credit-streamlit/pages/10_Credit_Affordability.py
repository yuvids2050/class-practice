import streamlit as st
from utils.styling import apply_custom_css

from utils.data_loader import load_prepared_application_data
from utils.filters import sidebar_filters, apply_filters
from utils.metrics import fmt_pct, fmt_number
from utils.charts import histogram, box_plot, scatter_chart, bar_chart

st.set_page_config(page_title="Credit Affordability", layout="wide")
apply_custom_css()
st.title("Page 10 — Credit Affordability Analysis")
st.caption("**Business Objective:** analyse whether customers receive credit amounts appropriate for their income.")
st.markdown(
    """
    **Feature engineering used on this page:** Credit-to-Income Ratio, Annuity-to-Income Ratio,
    Goods-to-Income Ratio, Credit-to-Goods Ratio, Income per Family Member (all computed once in
    `utils/feature_engineering.py` and reused across the app).
    """
)

df = load_prepared_application_data()
filters = sidebar_filters(df)
d = apply_filters(df, filters)

if d.empty:
    st.warning("No applicants match the selected filters.")
else:
    high_credit_burden = (d["CREDIT_TO_INCOME"] > 5).mean() * 100
    high_annuity_burden = (d["ANNUITY_TO_INCOME"] > 0.30).mean() * 100

    st.subheader("KPI Cards")
    cols = st.columns(5)
    cols[0].metric("Avg Credit-to-Income Ratio", f"{d['CREDIT_TO_INCOME'].mean():.2f}x")
    cols[1].metric("Median Credit-to-Income Ratio", f"{d['CREDIT_TO_INCOME'].median():.2f}x")
    cols[2].metric("Avg Annuity-to-Income Ratio", fmt_pct(d["ANNUITY_TO_INCOME"].mean() * 100))
    cols[3].metric("Customers with High Credit Burden (>5x)", fmt_pct(high_credit_burden))
    cols[4].metric("Customers with High Annuity Burden (>30%)", fmt_pct(high_annuity_burden))

    st.caption(
        "Thresholds (5x credit-to-income, 30% annuity-to-income) reflect commonly used affordability "
        "reference points, not a fitted or arbitrary cut — they mark where burden becomes worth a closer look, "
        "not a hard accept/reject rule."
    )

    st.subheader("Visualizations")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(histogram(d, "CREDIT_TO_INCOME", "Credit-to-Income Distribution"), use_container_width=True)
    with col2:
        st.plotly_chart(histogram(d, "ANNUITY_TO_INCOME", "Annuity-to-Income Distribution"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(box_plot(d, "CREDIT_TO_INCOME", "REPAYMENT_STATUS", "Credit-to-Income by Default Status"), use_container_width=True)
    with col2:
        st.plotly_chart(scatter_chart(d, "AMT_INCOME_TOTAL", "AMT_CREDIT", "REPAYMENT_STATUS", "Income vs Credit"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(bar_chart(d, "INCOME_GROUP", "CREDIT_TO_INCOME", "Credit Burden by Income Group", aggfunc="mean"), use_container_width=True)
    with col2:
        st.plotly_chart(bar_chart(d, "AGE_GROUP", "ANNUITY_TO_INCOME", "Annuity Burden by Age Group", aggfunc="mean"), use_container_width=True)

    st.subheader("Detailed Data Table")
    display_cols = ["SK_ID_CURR", "AMT_INCOME_TOTAL", "AMT_CREDIT", "AMT_ANNUITY", "AMT_GOODS_PRICE",
                     "CREDIT_TO_INCOME", "ANNUITY_TO_INCOME", "GOODS_TO_INCOME", "CREDIT_TO_GOODS", "CREDIT_TO_INCOME_BAND"]
    st.dataframe(d[display_cols], use_container_width=True, hide_index=True)
    st.download_button("Download Filtered Dataset", d[display_cols].to_csv(index=False), "credit_affordability_filtered.csv", "text/csv")

    repaid_ratio = d[d["TARGET"] == 0]["CREDIT_TO_INCOME"].mean()
    default_ratio = d[d["TARGET"] == 1]["CREDIT_TO_INCOME"].mean()

    st.subheader("Key Observations")
    st.markdown(
        f"""
        - Defaulted customers show an average credit-to-income ratio of **{default_ratio:.2f}x**
          versus **{repaid_ratio:.2f}x** for customers who repaid — a directional gap, not proof
          that the ratio alone causes default.
        - **{fmt_pct(high_credit_burden)}** of the filtered portfolio carries a credit-to-income
          ratio above 5x.
        - **{fmt_pct(high_annuity_burden)}** of the filtered portfolio commits more than 30% of
          income to the annuity payment alone.
        """
    )

    st.subheader("Business Insights")
    st.markdown(
        """
        - Affordability ratios flag *potentially* risky patterns; they should feed manual
          underwriting review rather than an automatic decision, since income and credit both have
          measurement noise (self-reported income, promotional pricing on goods, etc.).
        - Annuity-to-income burden is arguably more directly relevant to repayment capacity than
          credit-to-income, since it reflects the actual monthly cash outflow rather than the total
          loan size.
        """
    )

    st.subheader("Recommendations")
    st.markdown(
        """
        1. Route applications with credit-to-income > 5x **and** annuity-to-income > 30% to manual
           affordability review rather than auto-approval.
        2. Track the credit-to-income gap between repaid and defaulted customers over time — a
           widening gap would suggest the ratio is becoming more informative and could get more
           underwriting weight.
        3. Revisit the 5x / 30% reference thresholds periodically against actual portfolio
           performance rather than treating them as fixed.
        """
    )
