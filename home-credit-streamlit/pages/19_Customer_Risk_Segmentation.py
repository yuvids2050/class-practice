import streamlit as st
from utils.styling import apply_custom_css

from utils.data_loader import load_master_customer_table
from utils.metrics import fmt_number, fmt_currency, fmt_pct
from utils.charts import bar_chart, donut_chart, box_plot

st.set_page_config(page_title="Customer Risk Segmentation", layout="wide")
apply_custom_css()
st.title("Page 19 — Customer Risk Segmentation Using EDA Rules")
st.caption(
    "**Business Objective:** create descriptive, rule-based customer segments from EDA findings — "
    "these are NOT machine-learning predictions, just a structured summary of observed patterns."
)

st.info(
    """
    **Segmentation rule** — one point is added to a customer's risk score for each elevated-risk
    signal present, then the total score (0-5) maps to a segment:

    High Credit-to-Income Ratio (>5x) + High Annuity-to-Income Ratio (>30%) + Repeated Late
    Installment Payments (>20% late) + Any Bureau Overdue Amount (>0) + High Credit-Card Utilization
    (>75%) → **score 0 = Low, 1 = Moderate, 2 = Elevated, 3+ = High Observed Risk**
    """
)

master = load_master_customer_table()

st.sidebar.header("Filters")
segment_filter = st.sidebar.multiselect(
    "Risk Segment", options=list(master["RISK_SEGMENT"].cat.categories) if hasattr(master["RISK_SEGMENT"], "cat") else sorted(master["RISK_SEGMENT"].dropna().unique()),
    default=list(master["RISK_SEGMENT"].cat.categories) if hasattr(master["RISK_SEGMENT"], "cat") else sorted(master["RISK_SEGMENT"].dropna().unique()),
)
m = master[master["RISK_SEGMENT"].isin(segment_filter)]

if m.empty:
    st.warning("No customers match the selected risk segments.")
else:
    seg_counts = m["RISK_SEGMENT"].value_counts()
    high_risk_exposure = m[m["RISK_SEGMENT"] == "High Observed Risk"]["AMT_CREDIT"].sum()

    st.subheader("KPI Cards")
    cols = st.columns(4)
    cols[0].metric("Low-Risk Customers", fmt_number(seg_counts.get("Low Observed Risk", 0)))
    cols[1].metric("Moderate-Risk Customers", fmt_number(seg_counts.get("Moderate Observed Risk", 0)))
    cols[2].metric("Elevated-Risk Customers", fmt_number(seg_counts.get("Elevated Observed Risk", 0)))
    cols[3].metric("High-Risk Customers", fmt_number(seg_counts.get("High Observed Risk", 0)))
    st.metric("Credit Exposure in High-Risk Segment", fmt_currency(high_risk_exposure))

    st.subheader("Visualizations")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(bar_chart(m, "RISK_SEGMENT", "SK_ID_CURR", "Customer Count by Risk Segment", aggfunc="count"), use_container_width=True)
    with col2:
        st.plotly_chart(donut_chart(m, "RISK_SEGMENT", "Portfolio Exposure by Segment", values_col="AMT_CREDIT", aggfunc="sum"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(bar_chart(m, "RISK_SEGMENT", "AMT_INCOME_TOTAL", "Average Income by Segment", aggfunc="mean"), use_container_width=True)
    with col2:
        st.plotly_chart(bar_chart(m, "RISK_SEGMENT", "AMT_CREDIT", "Average Credit by Segment", aggfunc="mean"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(box_plot(m, "CREDIT_TO_INCOME", "RISK_SEGMENT", "Credit-to-Income by Segment"), use_container_width=True)
    with col2:
        if "LATE_PAYMENT_PERCENTAGE" in m.columns:
            st.plotly_chart(bar_chart(m.dropna(subset=["LATE_PAYMENT_PERCENTAGE"]), "RISK_SEGMENT", "LATE_PAYMENT_PERCENTAGE", "Late Payments (%) by Segment", aggfunc="mean"), use_container_width=True)

    if "TOTAL_BUREAU_DEBT" in m.columns:
        st.plotly_chart(bar_chart(m.dropna(subset=["TOTAL_BUREAU_DEBT"]), "RISK_SEGMENT", "TOTAL_BUREAU_DEBT", "Average Bureau Debt by Segment", aggfunc="mean"), use_container_width=True)

    st.subheader("Detailed Data Table")
    display_cols = ["SK_ID_CURR", "RISK_SEGMENT", "TARGET", "AMT_INCOME_TOTAL", "AMT_CREDIT", "CREDIT_TO_INCOME",
                     "ANNUITY_TO_INCOME", "LATE_PAYMENT_PERCENTAGE", "TOTAL_BUREAU_OVERDUE", "AVG_CC_UTILIZATION"]
    display_cols = [c for c in display_cols if c in m.columns]
    st.dataframe(m[display_cols].head(500), use_container_width=True, hide_index=True)
    st.download_button("Download Segmented Customer Table", m[display_cols].to_csv(index=False), "customer_risk_segments.csv", "text/csv")

    st.subheader("Key Observations")
    if "RISK_SEGMENT" in m.columns and "TARGET" in m.columns:
        segment_default_rate = m.groupby("RISK_SEGMENT", observed=True)["TARGET"].mean() * 100
        st.markdown(
            f"""
            - Actual observed TARGET default rate by segment: {', '.join(f'{seg}: {rate:.1f}%' for seg, rate in segment_default_rate.items())}.
              This is a **validation check** on the rule-based segments, not the basis for creating
              them — the segments were built from affordability/behavior rules, not from TARGET itself.
            - The High/Elevated segments hold **{fmt_currency(high_risk_exposure)}** of credit
              exposure, which is the portion of the portfolio most worth prioritizing for review.
            """
        )

    st.subheader("Business Insights")
    st.markdown(
        """
        - These segments are explicitly **descriptive EDA groupings**, not predictions — they
          summarize "how many elevated-risk signals are present," which is transparent and
          explainable to a manual reviewer in a way a black-box score would not be.
        - If the rule-based segments correlate well with actual observed default rate (shown above),
          that's supporting evidence the underlying signals are meaningful — but the segmentation
          logic itself never used TARGET as an input.
        """
    )

    st.subheader("Recommendations")
    st.markdown(
        """
        1. Route **High Observed Risk** customers to mandatory manual underwriting review; **Elevated**
           to optional review at underwriter discretion.
        2. Re-validate the five signal thresholds (5x credit-to-income, 30% annuity burden, 20% late
           payments, any bureau overdue, 75% card utilization) periodically against actual portfolio
           outcomes rather than treating them as fixed forever.
        3. Track portfolio-wide **movement between segments** month over month as an early-warning
           indicator distinct from the point-in-time snapshot.
        """
    )
