import streamlit as st
from utils.styling import apply_custom_css

from utils.data_loader import load_bureau_raw, load_application_raw
from utils.feature_engineering import aggregate_bureau_features
from utils.metrics import fmt_currency, fmt_number
from utils.charts import bar_chart, horizontal_bar_chart, histogram

st.set_page_config(page_title="Bureau Credit History", layout="wide")
apply_custom_css()
st.title("Page 13 — Bureau Credit History Analysis")
st.caption("**Business Objective:** analyse loans previously reported by other financial institutions (bureau.csv).")

bureau = load_bureau_raw()

st.sidebar.header("Filters")
active_filter = st.sidebar.multiselect("Credit Active", options=sorted(bureau["CREDIT_ACTIVE"].dropna().unique()), default=sorted(bureau["CREDIT_ACTIVE"].dropna().unique()))
type_filter = st.sidebar.multiselect("Credit Type", options=sorted(bureau["CREDIT_TYPE"].dropna().unique()), default=sorted(bureau["CREDIT_TYPE"].dropna().unique()))

b = bureau[bureau["CREDIT_ACTIVE"].isin(active_filter) & bureau["CREDIT_TYPE"].isin(type_filter)]

if b.empty:
    st.warning("No bureau records match the selected filters.")
else:
    active_count = (b["CREDIT_ACTIVE"] == "Active").sum()
    closed_count = (b["CREDIT_ACTIVE"] == "Closed").sum()

    st.subheader("KPI Cards")
    cols = st.columns(3)
    cols[0].metric("Bureau Accounts", fmt_number(len(b)))
    cols[1].metric("Customers with Bureau History", fmt_number(b["SK_ID_CURR"].nunique()))
    cols[2].metric("Active Credits", fmt_number(active_count))
    cols = st.columns(3)
    cols[0].metric("Closed Credits", fmt_number(closed_count))
    cols[1].metric("Total Bureau Debt", fmt_currency(b["AMT_CREDIT_SUM_DEBT"].sum()))
    cols[2].metric("Total Overdue Amount", fmt_currency(b["AMT_CREDIT_SUM_OVERDUE"].sum()))

    st.subheader("Visualizations")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(bar_chart(b, "CREDIT_ACTIVE", "SK_ID_BUREAU", "Active vs Closed Loans", aggfunc="count"), use_container_width=True)
    with col2:
        st.plotly_chart(horizontal_bar_chart(b, "CREDIT_TYPE", "SK_ID_BUREAU", "Credit Type Distribution", aggfunc="count"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(histogram(b, "AMT_CREDIT_SUM", "Bureau Credit Amount Distribution"), use_container_width=True)
    with col2:
        st.plotly_chart(histogram(b.dropna(subset=["AMT_CREDIT_SUM_DEBT"]), "AMT_CREDIT_SUM_DEBT", "Bureau Debt Distribution"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        overdue_only = b[b["AMT_CREDIT_SUM_OVERDUE"] > 0]
        if not overdue_only.empty:
            st.plotly_chart(histogram(overdue_only, "AMT_CREDIT_SUM_OVERDUE", "Overdue Amount Distribution (accounts with overdue > 0)"), use_container_width=True)
        else:
            st.info("No overdue amounts in the filtered bureau records.")
    with col2:
        st.plotly_chart(bar_chart(b, "CREDIT_TYPE", "AMT_CREDIT_SUM_DEBT", "Credit Type vs Total Debt"), use_container_width=True)

    st.subheader("Customer-Level Bureau Aggregates")
    bureau_agg = aggregate_bureau_features(bureau)
    st.dataframe(bureau_agg.head(200), use_container_width=True, hide_index=True)
    st.download_button("Download Bureau Aggregates (per customer)", bureau_agg.to_csv(index=False), "bureau_customer_aggregates.csv", "text/csv")

    st.subheader("Key Observations")
    top_credit_type = b["CREDIT_TYPE"].mode()[0]
    st.markdown(
        f"""
        - **{top_credit_type}** is the most common credit type reported by the bureau.
        - **{fmt_number(active_count)}** accounts are currently active vs **{fmt_number(closed_count)}**
          closed — a high active share suggests customers are carrying multiple concurrent obligations.
        - **{bureau_agg['SK_ID_CURR'].nunique():,} of {load_application_raw()['SK_ID_CURR'].nunique():,}**
          application customers in this sample have at least one bureau record.
        """
    )

    st.subheader("Business Insights")
    st.markdown(
        """
        - Customers with multiple active external credits carry more concurrent obligations than
          the current application alone reveals — bureau data materially extends the picture beyond
          what application_train.csv shows on its own.
        - Non-zero overdue amounts at the bureau level flag customers who have already struggled to
          repay elsewhere, which is a strong prior signal for the current application.
        """
    )

    st.subheader("Recommendations")
    st.markdown(
        """
        1. Weight the number of **active** external credits (not just their count) into manual
           underwriting review — many concurrent obligations increase repayment competition for the
           customer's income.
        2. Flag any customer with non-zero `AMT_CREDIT_SUM_OVERDUE` at the bureau for mandatory
           manual review before approval.
        3. Join `BUREAU_ACCOUNT_COUNT` / `TOTAL_BUREAU_DEBT` onto the main application view (see the
           Risk Segmentation page) so bureau history informs the same workflow as application data.
        """
    )
