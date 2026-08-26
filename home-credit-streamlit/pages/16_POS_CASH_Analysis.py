import streamlit as st
from utils.styling import apply_custom_css

from utils.data_loader import load_pos_cash_raw
from utils.feature_engineering import aggregate_pos_cash_features
from utils.metrics import fmt_number, fmt_pct
from utils.charts import bar_chart, histogram, box_plot, line_chart

st.set_page_config(page_title="POS/CASH Analysis", layout="wide")
apply_custom_css()
st.title("Page 16 — POS/CASH Loan Analysis")
st.caption("**Business Objective:** analyse point-of-sale and cash loan monthly balances (POS_CASH_balance.csv).")

pos = load_pos_cash_raw()

st.sidebar.header("Filters")
status_filter = st.sidebar.multiselect("Contract Status", options=sorted(pos["NAME_CONTRACT_STATUS"].dropna().unique()), default=sorted(pos["NAME_CONTRACT_STATUS"].dropna().unique()))
p = pos[pos["NAME_CONTRACT_STATUS"].isin(status_filter)]

if p.empty:
    st.warning("No POS/CASH records match the selected filters.")
else:
    active = (p["NAME_CONTRACT_STATUS"] == "Active").sum()
    completed = (p["NAME_CONTRACT_STATUS"] == "Completed").sum()
    customers_with_dpd = p[p["SK_DPD"] > 0]["SK_ID_CURR"].nunique()

    st.subheader("KPI Cards")
    cols = st.columns(3)
    cols[0].metric("POS/CASH Records", fmt_number(len(p)))
    cols[1].metric("Active Contracts", fmt_number(active))
    cols[2].metric("Completed Contracts", fmt_number(completed))
    cols = st.columns(2)
    cols[0].metric("Average Installments Remaining", f"{p['CNT_INSTALMENT_FUTURE'].mean():.1f}")
    cols[1].metric("Customers with DPD > 0", fmt_number(customers_with_dpd))

    st.subheader("Visualizations")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(bar_chart(p, "NAME_CONTRACT_STATUS", "SK_ID_PREV", "Contract Status Distribution", aggfunc="count"), use_container_width=True)
    with col2:
        st.plotly_chart(histogram(p.dropna(subset=["CNT_INSTALMENT_FUTURE"]), "CNT_INSTALMENT_FUTURE", "Installments Remaining Distribution"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        dpd_positive = p[p["SK_DPD"] > 0]
        if not dpd_positive.empty:
            st.plotly_chart(histogram(dpd_positive, "SK_DPD", "Days Past Due Distribution (DPD > 0)"), use_container_width=True)
        else:
            st.info("No positive DPD records in the filtered data.")
    with col2:
        st.plotly_chart(box_plot(p, "SK_DPD", "NAME_CONTRACT_STATUS", "DPD by Contract Status"), use_container_width=True)

    st.plotly_chart(line_chart(p, "MONTHS_BALANCE", "SK_DPD", "Monthly Balance Trend (average DPD)", aggfunc="mean"), use_container_width=True)

    st.subheader("Customer-Level POS/CASH Features")
    pos_agg = aggregate_pos_cash_features(pos)
    st.dataframe(pos_agg.head(200), use_container_width=True, hide_index=True)
    st.download_button("Download POS/CASH Aggregates (per customer)", pos_agg.to_csv(index=False), "pos_cash_customer_aggregates.csv", "text/csv")

    st.subheader("Key Observations")
    dpd_share = (p["SK_DPD"] > 0).mean() * 100
    st.markdown(
        f"""
        - **{fmt_pct(dpd_share)}** of POS/CASH monthly records show a positive days-past-due value.
        - **{customers_with_dpd:,}** distinct customers have at least one month with DPD > 0 in this
          sample.
        - The monthly average-DPD trend line shows whether POS/CASH delinquency is currently
          worsening, improving, or stable.
        """
    )

    st.subheader("Business Insights")
    st.markdown(
        """
        - POS/CASH balances track the *current* installment loans directly, making DPD here a more
          immediate signal than bureau data (which reflects other lenders and can lag).
        - `MAX_DPD` per customer flags anyone who has ever gone seriously delinquent on a POS/CASH
          product, even if their most recent months look clean.
        """
    )

    st.subheader("Recommendations")
    st.markdown(
        """
        1. Set up an operational alert for customers whose `SK_DPD` crosses into positive territory
           for two or more consecutive months (a worsening trend, not a one-off).
        2. Use `TOTAL_DPD_EVENTS` (built here) as a repeat-offender signal distinct from `MAX_DPD`
           (worst single event) — a customer can have a high max but only once, versus a lower max
           but repeatedly.
        3. Combine POS/CASH DPD history with installment payment delay data (Page 17) for a fuller
           repayment-behaviour picture before escalating to collections.
        """
    )
