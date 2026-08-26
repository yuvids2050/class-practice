import streamlit as st
from utils.styling import apply_custom_css

from utils.data_loader import load_previous_application_raw
from utils.feature_engineering import aggregate_previous_application_features
from utils.metrics import fmt_number, fmt_pct
from utils.charts import bar_chart, donut_chart, scatter_chart, horizontal_bar_chart

st.set_page_config(page_title="Previous Applications", layout="wide")
apply_custom_css()
st.title("Page 15 — Previous Application Analysis")
st.caption("**Business Objective:** study customers' previous Home Credit loan applications (previous_application.csv).")

prev = load_previous_application_raw()

st.sidebar.header("Filters")
status_filter = st.sidebar.multiselect("Contract Status", options=sorted(prev["NAME_CONTRACT_STATUS"].dropna().unique()), default=sorted(prev["NAME_CONTRACT_STATUS"].dropna().unique()))
client_filter = st.sidebar.multiselect("Client Type", options=sorted(prev["NAME_CLIENT_TYPE"].dropna().unique()), default=sorted(prev["NAME_CLIENT_TYPE"].dropna().unique()))
p = prev[prev["NAME_CONTRACT_STATUS"].isin(status_filter) & prev["NAME_CLIENT_TYPE"].isin(client_filter)]

if p.empty:
    st.warning("No previous-application records match the selected filters.")
else:
    approved = (p["NAME_CONTRACT_STATUS"] == "Approved").sum()
    refused = (p["NAME_CONTRACT_STATUS"] == "Refused").sum()
    cancelled = (p["NAME_CONTRACT_STATUS"] == "Canceled").sum()
    total = len(p)

    st.subheader("KPI Cards")
    cols = st.columns(3)
    cols[0].metric("Previous Applications", fmt_number(total))
    cols[1].metric("Approved Applications", fmt_number(approved))
    cols[2].metric("Refused Applications", fmt_number(refused))
    cols = st.columns(3)
    cols[0].metric("Cancelled Applications", fmt_number(cancelled))
    cols[1].metric("Approval Rate", fmt_pct(approved / total * 100 if total else 0))
    cols[2].metric("Rejection Rate", fmt_pct(refused / total * 100 if total else 0))

    st.subheader("Visualizations")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(bar_chart(p, "NAME_CONTRACT_STATUS", "SK_ID_PREV", "Application Status", aggfunc="count"), use_container_width=True)
    with col2:
        st.plotly_chart(donut_chart(p, "NAME_CONTRACT_STATUS", "Approval Percentage"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        approved_only = p[p["NAME_CONTRACT_STATUS"] == "Approved"].dropna(subset=["AMT_APPLICATION", "AMT_CREDIT"])
        st.plotly_chart(scatter_chart(approved_only, "AMT_APPLICATION", "AMT_CREDIT", "NAME_CONTRACT_TYPE", "Application vs Credit Amount (Approved)"), use_container_width=True)
    with col2:
        st.plotly_chart(bar_chart(p, "NAME_CONTRACT_TYPE", "SK_ID_PREV", "Previous Contract Types", aggfunc="count"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(bar_chart(p, "NAME_CLIENT_TYPE", "SK_ID_PREV", "Client Type Distribution", aggfunc="count"), use_container_width=True)
    with col2:
        st.plotly_chart(horizontal_bar_chart(p, "NAME_PRODUCT_TYPE", "SK_ID_PREV", "Product Type Distribution", aggfunc="count"), use_container_width=True)

    if "CODE_REJECT_REASON" in p.columns:
        refused_only = p[p["NAME_CONTRACT_STATUS"] == "Refused"]
        if not refused_only.empty:
            st.plotly_chart(horizontal_bar_chart(refused_only, "CODE_REJECT_REASON", "SK_ID_PREV", "Rejection Reasons", aggfunc="count"), use_container_width=True)

    st.subheader("Customer-Level Previous Application Features")
    prev_agg = aggregate_previous_application_features(prev)
    st.dataframe(prev_agg.head(200), use_container_width=True, hide_index=True)
    st.download_button("Download Previous Application Aggregates (per customer)", prev_agg.to_csv(index=False), "previous_application_customer_aggregates.csv", "text/csv")

    st.subheader("Key Observations")
    top_reject_reason = p[p["NAME_CONTRACT_STATUS"] == "Refused"]["CODE_REJECT_REASON"].mode()[0] if refused > 0 else "N/A"
    st.markdown(
        f"""
        - Historical approval rate across previous applications is **{fmt_pct(approved / total * 100 if total else 0)}**.
        - The most common rejection reason code is **{top_reject_reason}**.
        - **{p['NAME_CLIENT_TYPE'].mode()[0]}** is the most common client type — this distinguishes
          new customers from repeat/returning ones, which matters for approval-rate interpretation.
        """
    )

    st.subheader("Business Insights")
    st.markdown(
        """
        - A customer's own approval/refusal history at Home Credit is a strong, directly relevant
          prior for the current application — very different from bureau history, which reflects
          other lenders.
        - `PREVIOUS_APPROVAL_RATE` per customer (built here) compresses a variable-length history
          into a single comparable number for use in segmentation.
        """
    )

    st.subheader("Recommendations")
    st.markdown(
        """
        1. Give repeat customers with a strong prior approval history an expedited review path.
        2. Investigate the leading rejection reason code operationally — if it's concentrated in a
           specific product or client type, that combination may need policy adjustment.
        3. Carry `PREVIOUS_APPLICATION_COUNT` and `PREVIOUS_APPROVAL_RATE` into the master customer
           table used for risk segmentation (Page 19).
        """
    )
