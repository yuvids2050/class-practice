import streamlit as st
from utils.styling import apply_custom_css

from utils.data_loader import load_prepared_application_data
from utils.filters import sidebar_filters, apply_filters
from utils.metrics import fmt_currency, fmt_number
from utils.charts import bar_chart, histogram, scatter_chart, line_chart

st.set_page_config(page_title="Loan Application Analysis", layout="wide")
apply_custom_css()
st.title("Page 9 — Current Loan Application Analysis")
st.caption("**Business Objective:** understand the structure of current loan applications.")

WEEKDAY_ORDER = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]

df = load_prepared_application_data()
filters = sidebar_filters(df)
d = apply_filters(df, filters)

if d.empty:
    st.warning("No applicants match the selected filters.")
else:
    st.subheader("KPI Cards")
    cols = st.columns(3)
    cols[0].metric("Total Applications", fmt_number(len(d)))
    cols[1].metric("Average Credit", fmt_currency(d["AMT_CREDIT"].mean()))
    cols[2].metric("Median Credit", fmt_currency(d["AMT_CREDIT"].median()))
    cols = st.columns(3)
    cols[0].metric("Average Annuity", fmt_currency(d["AMT_ANNUITY"].mean()))
    cols[1].metric("Average Goods Price", fmt_currency(d["AMT_GOODS_PRICE"].mean()))
    cols[2].metric("Most Common Contract Type", d["NAME_CONTRACT_TYPE"].mode()[0])

    st.subheader("Visualizations")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(bar_chart(d, "NAME_CONTRACT_TYPE", "TARGET", "Applications by Contract Type", aggfunc="count"), use_container_width=True)
    with col2:
        st.plotly_chart(histogram(d, "AMT_CREDIT", "Credit Amount Distribution"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(histogram(d, "AMT_ANNUITY", "Annuity Distribution"), use_container_width=True)
    with col2:
        st.plotly_chart(histogram(d, "AMT_GOODS_PRICE", "Goods Price Distribution"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(scatter_chart(d, "AMT_GOODS_PRICE", "AMT_CREDIT", "REPAYMENT_STATUS", "Credit vs Goods Price"), use_container_width=True)
    with col2:
        st.plotly_chart(scatter_chart(d, "AMT_CREDIT", "AMT_ANNUITY", "REPAYMENT_STATUS", "Credit vs Annuity"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        weekday_counts = d["WEEKDAY_APPR_PROCESS_START"].value_counts().reindex(WEEKDAY_ORDER).reset_index()
        weekday_counts.columns = ["Weekday", "Applications"]
        st.plotly_chart(bar_chart(weekday_counts, "Weekday", "Applications", "Applications by Weekday"), use_container_width=True)
    with col2:
        st.plotly_chart(line_chart(d, "HOUR_APPR_PROCESS_START", "TARGET", "Applications by Hour", aggfunc="count"), use_container_width=True)

    st.subheader("Detailed Data Table")
    display_cols = ["SK_ID_CURR", "NAME_CONTRACT_TYPE", "AMT_CREDIT", "AMT_ANNUITY", "AMT_GOODS_PRICE",
                     "WEEKDAY_APPR_PROCESS_START", "HOUR_APPR_PROCESS_START"]
    st.dataframe(d[display_cols], use_container_width=True, hide_index=True)
    st.download_button("Download Filtered Dataset", d[display_cols].to_csv(index=False), "loan_application_filtered.csv", "text/csv")

    peak_hour = d["HOUR_APPR_PROCESS_START"].mode()[0]
    peak_day = d["WEEKDAY_APPR_PROCESS_START"].mode()[0]

    st.subheader("Key Observations")
    st.markdown(
        f"""
        - **{d['NAME_CONTRACT_TYPE'].mode()[0]}** is the most popular loan type in the filtered
          portfolio.
        - Peak application activity occurs on **{peak_day}** around **{peak_hour}:00**.
        - Credit and goods price move together tightly, as expected — goods price is usually the
          basis for the credit amount requested.
        """
    )

    st.subheader("Business Insights")
    st.markdown(
        """
        - Knowing peak application times helps staff underwriting/support capacity — under-staffing
          during peak hours can slow decisioning and hurt conversion.
        - Applications where credit substantially exceeds goods price are worth a closer look, since
          they imply the loan is financing more than the stated purchase.
        """
    )

    st.subheader("Recommendations")
    st.markdown(
        f"""
        1. Align staffing/support capacity with the **{peak_day} around {peak_hour}:00** peak window
           identified above.
        2. Flag applications where Credit-to-Goods ratio is unusually high for manual review (see
           the Credit Affordability page for that ratio).
        3. Monitor whether contract type mix shifts over time, since Cash vs Revolving loans carry
           different risk and servicing profiles.
        """
    )
