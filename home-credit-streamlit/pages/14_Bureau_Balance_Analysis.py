import streamlit as st
from utils.styling import apply_custom_css

from utils.data_loader import load_bureau_balance_raw, load_bureau_raw
from utils.feature_engineering import aggregate_bureau_balance_features, DELINQUENCY_STATUSES
from utils.metrics import fmt_number, fmt_pct
from utils.charts import bar_chart, donut_chart, stacked_bar_chart, line_chart, category_heatmap

st.set_page_config(page_title="Bureau Balance Analysis", layout="wide")
apply_custom_css()
st.title("Page 14 — Bureau Balance Analysis")
st.caption("**Business Objective:** analyse historical monthly bureau account status (bureau_balance.csv).")

bureau_balance = load_bureau_balance_raw()
bureau = load_bureau_raw()

st.sidebar.header("Filters")
status_filter = st.sidebar.multiselect("Status", options=sorted(bureau_balance["STATUS"].unique()), default=sorted(bureau_balance["STATUS"].unique()))
bb = bureau_balance[bureau_balance["STATUS"].isin(status_filter)]

if bb.empty:
    st.warning("No bureau balance records match the selected filters.")
else:
    delinquent = bb["STATUS"].isin(DELINQUENCY_STATUSES).sum()
    closed = (bb["STATUS"] == "C").sum()

    st.subheader("KPI Cards")
    cols = st.columns(3)
    cols[0].metric("Total Bureau Monthly Records", fmt_number(len(bb)))
    cols[1].metric("Unique Bureau Accounts", fmt_number(bb["SK_ID_BUREAU"].nunique()))
    cols[2].metric("Most Common Status", bb["STATUS"].mode()[0])
    cols = st.columns(2)
    cols[0].metric("Delinquency Records (status 1-5)", fmt_number(delinquent))
    cols[1].metric("Closed Records (status C)", fmt_number(closed))

    st.caption(
        "Status codes: C = closed, X = status unknown, 0 = no days-past-due, 1-5 = increasing "
        "days-past-due buckets (1 = mildest, 5 = most severe / written off)."
    )

    st.subheader("Visualizations")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(bar_chart(bb, "STATUS", "SK_ID_BUREAU", "Status Distribution", aggfunc="count"), use_container_width=True)
    with col2:
        st.plotly_chart(donut_chart(bb, "STATUS", "Status Percentage"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        recent = bb[bb["MONTHS_BALANCE"] >= -24]
        st.plotly_chart(stacked_bar_chart(recent, "MONTHS_BALANCE", "STATUS", "Account Status by Month (last 24 months)"), use_container_width=True)
    with col2:
        bb_trend = bb.copy()
        bb_trend["IS_DELINQUENT"] = bb_trend["STATUS"].isin(DELINQUENCY_STATUSES).astype(int)
        st.plotly_chart(line_chart(bb_trend, "MONTHS_BALANCE", "IS_DELINQUENT", "Monthly Delinquency Trend (share of accounts)", aggfunc="mean"), use_container_width=True)

    sample_accounts = bb["SK_ID_BUREAU"].drop_duplicates().sample(min(30, bb["SK_ID_BUREAU"].nunique()), random_state=42)
    st.plotly_chart(category_heatmap(bb[bb["SK_ID_BUREAU"].isin(sample_accounts)], "SK_ID_BUREAU", "STATUS", "Status Heatmap (sample of 30 accounts)"), use_container_width=True)

    st.subheader("Customer-Level Bureau Balance Features")
    bb_agg = aggregate_bureau_balance_features(bureau_balance, bureau)
    st.dataframe(bb_agg.head(200), use_container_width=True, hide_index=True)
    st.download_button("Download Bureau Balance Aggregates (per customer)", bb_agg.to_csv(index=False), "bureau_balance_customer_aggregates.csv", "text/csv")

    st.subheader("Key Observations")
    delinquency_rate = delinquent / len(bb) * 100
    st.markdown(
        f"""
        - **{fmt_pct(delinquency_rate)}** of monthly bureau-balance records show some level of
          delinquency (status 1-5).
        - **{bb_agg.shape[0]:,}** application customers have bureau-balance history that could be
          mapped back to `SK_ID_CURR` in this sample.
        - The monthly delinquency trend line shows whether delinquency is currently rising, falling,
          or flat across the observed months.
        """
    )

    st.subheader("Business Insights")
    st.markdown(
        """
        - Bureau balance provides a *time series* of external repayment behaviour, which is richer
          than the single-point-in-time bureau snapshot on the Bureau Credit History page — a
          customer with worsening delinquency status over recent months is a different risk than one
          with a single old delinquent month.
        - `MAX_DELINQUENCY_LEVEL` per customer is a compact, one-number summary of "how bad has it
          gotten" that's easy to slot into a review checklist.
        """
    )

    st.subheader("Recommendations")
    st.markdown(
        """
        1. Prioritize customers with a **rising** delinquency trend in recent months over those with
           only historical (older) delinquency, since recency matters for current risk.
        2. Feed `MONTHS_WITH_DELINQUENCY` and `MAX_DELINQUENCY_LEVEL` into the customer risk
           segmentation rules (Page 19) alongside the current-application affordability ratios.
        3. Set up a periodic refresh of bureau balance data, since this table is inherently
           time-sensitive and stale data understates current risk.
        """
    )
