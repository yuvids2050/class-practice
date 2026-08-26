import streamlit as st
from utils.styling import apply_custom_css

from utils.data_loader import load_master_customer_table
from utils.metrics import fmt_number, fmt_currency, fmt_pct, top_bottom_by_default_rate
from utils.charts import donut_chart, bar_chart

st.set_page_config(page_title="Executive Insights & Recommendations", layout="wide")
apply_custom_css()
st.title("Page 20 — Executive Insights & Business Recommendations")
st.caption(
    "**Business Objective:** a management summary synthesizing every prior page — fewer exploratory "
    "graphs, more conclusions."
)

master = load_master_customer_table()

total = len(master)
defaults = int(master["TARGET"].sum())
default_rate = defaults / total * 100 if total else 0
high_credit_burden = (master["CREDIT_TO_INCOME"] > 5).sum()
late_payers = (master.get("LATE_PAYMENT_PERCENTAGE", 0) > 20).sum() if "LATE_PAYMENT_PERCENTAGE" in master.columns else 0
bureau_debt_customers = (master.get("TOTAL_BUREAU_DEBT", 0) > 0).sum() if "TOTAL_BUREAU_DEBT" in master.columns else 0
high_util_customers = (master.get("AVG_CC_UTILIZATION", 0) > 0.75).sum() if "AVG_CC_UTILIZATION" in master.columns else 0
elevated_plus = master["RISK_SEGMENT"].isin(["Elevated Observed Risk", "High Observed Risk"]).sum()

st.subheader("Executive KPIs")
cols = st.columns(5)
cols[0].metric("Total Customers", fmt_number(total))
cols[1].metric("Default Rate", fmt_pct(default_rate))
cols[2].metric("Total Credit Exposure", fmt_currency(master["AMT_CREDIT"].sum()))
cols[3].metric("Average Credit", fmt_currency(master["AMT_CREDIT"].mean()))
cols[4].metric("Average Income", fmt_currency(master["AMT_INCOME_TOTAL"].mean()))

cols = st.columns(5)
cols[0].metric("High-Burden Customers (>5x Credit/Income)", fmt_number(high_credit_burden))
cols[1].metric("Customers with Late Payments (>20%)", fmt_number(late_payers))
cols[2].metric("Customers with Bureau Debt", fmt_number(bureau_debt_customers))
cols[3].metric("High Card-Utilization Customers", fmt_number(high_util_customers))
cols[4].metric("Customers in Elevated+ Risk Segments", fmt_number(elevated_plus))

st.divider()
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(donut_chart(master, "RISK_SEGMENT", "Portfolio Composition by Risk Segment"), use_container_width=True)
with col2:
    st.plotly_chart(bar_chart(master, "RISK_SEGMENT", "TARGET", "Observed Default Rate by Risk Segment", aggfunc="mean"), use_container_width=True)

st.divider()

highest_risk_age, _ = top_bottom_by_default_rate(master, "AGE_GROUP", min_count=5)
highest_risk_income, _ = top_bottom_by_default_rate(master, "INCOME_GROUP", min_count=5)
highest_risk_employment, _ = top_bottom_by_default_rate(master, "EMPLOYMENT_GROUP", min_count=5)
highest_risk_occupation, _ = top_bottom_by_default_rate(master, "OCCUPATION_TYPE", min_count=5)

st.subheader("Top 10 Portfolio Insights")
st.markdown(
    f"""
    1. Overall observed default rate across the portfolio is **{fmt_pct(default_rate)}**, against
       **{fmt_currency(master['AMT_CREDIT'].sum())}** of total credit exposure.
    2. Customers with shorter employment histories (**{highest_risk_employment}**) show the highest
       observed default rate among employment-tenure bands (see Page 7).
    3. Higher credit-to-income ratios are associated with increased observed default rates — the
       gap between repaid and defaulted customers' average ratios is directly visible on Page 10.
    4. The **{highest_risk_age}** age group and **{highest_risk_income}** income group each show
       the highest observed default rate within their respective dimension (Page 11).
    5. **{highest_risk_occupation}** shows a notably different repayment pattern from other
       occupations, holding sample size caveats in mind (Page 7 & 12).
    6. Customers with repeated late installment payments (**{fmt_number(late_payers)}** customers
       above the 20% late-payment threshold) form an important risk-monitoring group (Page 17).
    7. **{fmt_number(bureau_debt_customers)}** customers carry active external bureau debt, extending
       their true obligations beyond what the current application alone shows (Page 13).
    8. High credit-card utilization (**{fmt_number(high_util_customers)}** customers above 75%),
       especially combined with bureau debt, may indicate increased financial pressure (Page 18).
    9. Rule-based risk segmentation places **{fmt_number(elevated_plus)}** customers in the Elevated
       or High Observed Risk segments, concentrating a disproportionate share of monitoring priority
       into a manageable subset of the portfolio (Page 19).
    10. Missingness in the raw data is structural in places (e.g. building-quality fields tied to
        housing type) rather than random, meaning naive imputation could distort downstream EDA if
        applied without the missing-indicator approach used in this project (Page 3).
    """
)

st.subheader("Final Business Recommendations")
st.markdown(
    """
    **Affordability**
    1. Route applications with credit-to-income > 5x **and** annuity-to-income > 30% to mandatory
       manual affordability review.
    2. Monitor customers with unusually high annuity burden as a distinct population from those with
       high credit-to-income alone, since the two ratios capture different aspects of burden.
    3. Use income-per-family-member, not raw household income, when comparing affordability across
       differently-sized households.

    **Repayment**
    4. Build an early-warning operational report flagging customers with 2+ consecutive late
       installment payments for proactive outreach.
    5. Track customers whose payment delay is *increasing* release-over-release, not just those
       currently late.
    6. Distinguish underpayment from simple lateness in monitoring dashboards — they may need
       different interventions.

    **Bureau**
    7. Review customers with multiple concurrent active external loans as part of standard
       underwriting checklists.
    8. Identify and prioritize customers with significant overdue bureau balances for manual review
       before approval.
    9. Refresh bureau-balance data periodically, since delinquency trends can shift over just a few
       months.

    **Credit Cards**
    10. Monitor customers consistently using a large share of their available card credit
        (sustained, not one-off, high utilization).
    11. Cross-reference card DPD with POS/CASH DPD — delinquency across multiple product types is a
        stronger signal than delinquency in one alone.

    **Employment**
    12. Include employment tenure, particularly sub-1-year tenure, in manual-review checklists.
    13. Investigate occupation- and organization-level default-rate differences for policy
        relevance, filtering out categories with very small sample sizes first.

    **Data Quality**
    14. Prioritize improving collection of high-missing-value fields that also carry business
        importance (e.g. occupation), rather than fields with high missingness but little
        downstream use.

    **Portfolio Monitoring**
    15. Develop a monthly risk-segment movement dashboard — tracking customers moving between Low,
        Moderate, Elevated, and High Observed Risk segments over time, not just the current snapshot.
    """
)

st.divider()
st.caption(
    "Scope reminder: this application performs data preprocessing, feature engineering, EDA, "
    "rule-based segmentation, and business-insight synthesis only. No predictive models, "
    "feature-importance scores, ROC curves, or confusion matrices are built anywhere in this project."
)
