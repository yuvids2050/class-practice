import streamlit as st
from utils.styling import apply_custom_css

from utils.data_loader import load_prepared_application_data
from utils.filters import sidebar_filters, apply_filters
from utils.metrics import fmt_currency, default_rate_by
from utils.charts import histogram, bar_chart, box_plot, horizontal_bar_chart, scatter_chart

st.set_page_config(page_title="Income Analysis", layout="wide")
apply_custom_css()
st.title("Page 6 — Income Analysis")
st.caption("**Business Objective:** understand income distribution and its relationship with lending.")

df = load_prepared_application_data()
filters = sidebar_filters(df)
d = apply_filters(df, filters)

if d.empty:
    st.warning("No applicants match the selected filters.")
else:
    largest_income_group = d["INCOME_GROUP"].value_counts().idxmax()

    st.subheader("KPI Cards")
    cols = st.columns(5)
    cols[0].metric("Average Income", fmt_currency(d["AMT_INCOME_TOTAL"].mean()))
    cols[1].metric("Median Income", fmt_currency(d["AMT_INCOME_TOTAL"].median()))
    cols[2].metric("Maximum Income", fmt_currency(d["AMT_INCOME_TOTAL"].max()))
    cols[3].metric("Avg Income per Family Member", fmt_currency(d["INCOME_PER_FAMILY_MEMBER"].mean()))
    cols[4].metric("Largest Income Group", str(largest_income_group))

    st.subheader("Visualizations")
    st.plotly_chart(histogram(d, "AMT_INCOME_TOTAL", "Income Histogram"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(bar_chart(d, "INCOME_GROUP", "TARGET", "Income Group Distribution", aggfunc="count"), use_container_width=True)
    with col2:
        st.plotly_chart(box_plot(d, "AMT_INCOME_TOTAL", "NAME_EDUCATION_TYPE", "Income by Education"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(horizontal_bar_chart(d.dropna(subset=["OCCUPATION_TYPE"]), "OCCUPATION_TYPE", "AMT_INCOME_TOTAL", "Income by Occupation (Top 12)", top_n=12, aggfunc="mean", ascending=False), use_container_width=True)
    with col2:
        st.plotly_chart(box_plot(d, "AMT_INCOME_TOTAL", "NAME_INCOME_TYPE", "Income by Income Type"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(scatter_chart(d, "AMT_INCOME_TOTAL", "AMT_CREDIT", "REPAYMENT_STATUS", "Income vs Credit"), use_container_width=True)
    with col2:
        st.plotly_chart(bar_chart(d, "INCOME_GROUP", "TARGET", "Income Group vs Default Rate", aggfunc="mean"), use_container_width=True)

    st.subheader("Detailed Data Table")
    st.dataframe(default_rate_by(d, "INCOME_GROUP"), use_container_width=True, hide_index=True)
    st.download_button("Download Income Group Summary", default_rate_by(d, "INCOME_GROUP").to_csv(index=False), "income_group_summary.csv", "text/csv")

    highest_borrow_group = d.groupby("INCOME_GROUP", observed=True)["AMT_CREDIT"].mean().idxmax()
    highest_default_group = d.dropna(subset=["INCOME_GROUP"]).groupby("INCOME_GROUP", observed=True)["TARGET"].mean().idxmax()

    st.subheader("Key Observations")
    st.markdown(
        f"""
        - The **{highest_borrow_group}** income group borrows the largest average credit amount.
        - The **{highest_default_group}** income group shows the highest observed default rate.
        - Income is right-skewed, as expected — a small number of high earners pull the mean above
          the median.
        """
    )

    st.subheader("Business Insights")
    st.markdown(
        """
        - Higher income does not automatically mean lower observed loan burden — some higher-income
          groups still take proportionally large loans, which the Credit Affordability page examines
          directly via the credit-to-income ratio.
        - Occupation-level income gaps are informative for tailoring credit limits, but occupation
          categories with very few observations should be treated cautiously (small-sample noise).
        """
    )

    st.subheader("Recommendations")
    st.markdown(
        f"""
        1. Apply closer affordability review for the **{highest_borrow_group}** income group given
           its larger average loan size.
        2. Monitor the **{highest_default_group}** income group's default rate trend over time as an
           early warning signal.
        3. Use income-per-family-member (not raw income) when comparing affordability across
           household sizes, since raw income understates burden for larger families.
        """
    )
