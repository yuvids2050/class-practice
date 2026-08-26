import streamlit as st
from utils.styling import apply_custom_css

from utils.data_loader import load_credit_card_raw
from utils.feature_engineering import add_credit_card_features, aggregate_credit_card_features
from utils.metrics import fmt_number, fmt_pct
from utils.charts import histogram, scatter_chart

st.set_page_config(page_title="Credit Card Analysis", layout="wide")
apply_custom_css()
st.title("Page 18 — Credit Card Balance Analysis")
st.caption("**Business Objective:** understand customers' credit-card usage and repayment behaviour (credit_card_balance.csv).")
st.latex(r"\text{Credit Utilization} = \text{AMT\_BALANCE} \, / \, \text{AMT\_CREDIT\_LIMIT\_ACTUAL}")

credit_card = load_credit_card_raw()
cc = add_credit_card_features(credit_card)

st.sidebar.header("Filters")
status_filter = st.sidebar.multiselect("Contract Status", options=sorted(cc["NAME_CONTRACT_STATUS"].dropna().unique()), default=sorted(cc["NAME_CONTRACT_STATUS"].dropna().unique()))
c = cc[cc["NAME_CONTRACT_STATUS"].isin(status_filter)]

if c.empty:
    st.warning("No credit card records match the selected filters.")
else:
    customers_with_dpd = c[c["SK_DPD"] > 0]["SK_ID_CURR"].nunique()

    st.subheader("KPI Cards")
    cols = st.columns(3)
    cols[0].metric("Credit Card Customers", fmt_number(c["SK_ID_CURR"].nunique()))
    cols[1].metric("Average Balance", f"${c['AMT_BALANCE'].mean():,.0f}")
    cols[2].metric("Average Credit Limit", f"${c['AMT_CREDIT_LIMIT_ACTUAL'].mean():,.0f}")
    cols = st.columns(3)
    cols[0].metric("Average Utilization", fmt_pct(c["CREDIT_UTILIZATION"].mean() * 100) if c["CREDIT_UTILIZATION"].notna().any() else "N/A")
    cols[1].metric("Average Monthly Payment", f"${c['AMT_PAYMENT_CURRENT'].mean():,.0f}" if c["AMT_PAYMENT_CURRENT"].notna().any() else "N/A")
    cols[2].metric("Customers with DPD > 0", fmt_number(customers_with_dpd))

    st.subheader("Visualizations")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(histogram(c.dropna(subset=["AMT_BALANCE"]), "AMT_BALANCE", "Credit Balance Distribution"), use_container_width=True)
    with col2:
        st.plotly_chart(histogram(c.dropna(subset=["AMT_CREDIT_LIMIT_ACTUAL"]), "AMT_CREDIT_LIMIT_ACTUAL", "Credit Limit Distribution"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        util = c[c["CREDIT_UTILIZATION"].notna() & (c["CREDIT_UTILIZATION"] < 3)]
        st.plotly_chart(histogram(util, "CREDIT_UTILIZATION", "Credit Utilization Distribution"), use_container_width=True)
    with col2:
        sample_pool = c.dropna(subset=["AMT_CREDIT_LIMIT_ACTUAL", "AMT_BALANCE"])
        sample = sample_pool.sample(min(3000, len(sample_pool)), random_state=42)
        st.plotly_chart(scatter_chart(sample, "AMT_CREDIT_LIMIT_ACTUAL", "AMT_BALANCE", None, "Credit Limit vs Balance"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        sample2_pool = c.dropna(subset=["AMT_BALANCE", "AMT_PAYMENT_CURRENT"])
        sample2 = sample2_pool.sample(min(3000, len(sample2_pool)), random_state=42)
        st.plotly_chart(scatter_chart(sample2, "AMT_BALANCE", "AMT_PAYMENT_CURRENT", None, "Balance vs Payment"), use_container_width=True)
    with col2:
        dpd_positive = c[c["SK_DPD"] > 0]
        if not dpd_positive.empty:
            st.plotly_chart(histogram(dpd_positive, "SK_DPD", "DPD Distribution (DPD > 0)"), use_container_width=True)
        else:
            st.info("No positive DPD records in the filtered data.")

    st.subheader("Customer-Level Credit Card Features")
    cc_agg = aggregate_credit_card_features(cc)
    st.dataframe(cc_agg.head(200), use_container_width=True, hide_index=True)
    st.download_button("Download Credit Card Aggregates (per customer)", cc_agg.to_csv(index=False), "credit_card_customer_aggregates.csv", "text/csv")

    st.subheader("Key Observations")
    high_util_customers = (cc_agg["AVG_CC_UTILIZATION"] > 0.75).sum()
    st.markdown(
        f"""
        - **{fmt_number(high_util_customers)}** customers carry an average credit-card utilization
          above 75% — persistently near their credit limit.
        - **{fmt_number(customers_with_dpd)}** customers have at least one credit-card record with
          DPD > 0.
        - Utilization and balance move together as expected; the more informative view is
          utilization **relative to limit**, not raw balance alone.
        """
    )

    st.subheader("Business Insights")
    st.markdown(
        """
        - Consistently high utilization (not just a single high-balance month) suggests the customer
          may be relying on revolving credit to cover shortfalls — a forward-looking stress signal
          distinct from a one-time large purchase.
        - Combining high card utilization with bureau overdue amounts (Page 13) paints a more
          complete picture of financial pressure across all the customer's credit relationships.
        """
    )

    st.subheader("Recommendations")
    st.markdown(
        """
        1. Monitor customers with **sustained** utilization above 75% (not just a single high month)
           as a proactive risk-review trigger.
        2. Cross-reference credit-card DPD with POS/CASH DPD (Page 16) — delinquency appearing
           across multiple product types is a stronger signal than delinquency in one product alone.
        3. Include `AVG_CC_UTILIZATION` and `MAX_CC_DPD` in the master customer table used for risk
           segmentation (Page 19).
        """
    )
