import streamlit as st
from utils.styling import apply_custom_css

from utils.data_loader import load_prepared_application_data
from utils.filters import sidebar_filters, apply_filters
from utils.metrics import fmt_number
from utils.charts import histogram, donut_chart, horizontal_bar_chart, bar_chart, grouped_bar_chart, scatter_chart

st.set_page_config(page_title="Customer Demographics", layout="wide")
apply_custom_css()
st.title("Page 5 — Customer Demographic Analysis")
st.caption("**Business Objective:** understand who the Home Credit customers are.")

df = load_prepared_application_data()
filters = sidebar_filters(df)
d = apply_filters(df, filters)

if d.empty:
    st.warning("No applicants match the selected filters.")
else:
    st.subheader("KPI Cards")
    cols = st.columns(3)
    cols[0].metric("Average Age", f"{d['AGE_YEARS'].mean():.1f}")
    cols[1].metric("Median Age", f"{d['AGE_YEARS'].median():.1f}")
    cols[2].metric("Most Common Gender", d["CODE_GENDER"].mode()[0])
    cols = st.columns(3)
    cols[0].metric("Most Common Education", d["NAME_EDUCATION_TYPE"].mode()[0])
    cols[1].metric("Most Common Income Type", d["NAME_INCOME_TYPE"].mode()[0])
    cols[2].metric("Most Common Family Status", d["NAME_FAMILY_STATUS"].mode()[0])

    st.subheader("Visualizations")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(histogram(d, "AGE_YEARS", "Age Distribution"), use_container_width=True)
    with col2:
        st.plotly_chart(donut_chart(d, "CODE_GENDER", "Gender Distribution"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(horizontal_bar_chart(d, "NAME_EDUCATION_TYPE", "TARGET", "Education Distribution", aggfunc="count"), use_container_width=True)
    with col2:
        st.plotly_chart(bar_chart(d, "NAME_FAMILY_STATUS", "TARGET", "Family Status Distribution", aggfunc="count"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(horizontal_bar_chart(d, "NAME_INCOME_TYPE", "TARGET", "Income Type Distribution", aggfunc="count"), use_container_width=True)
    with col2:
        st.plotly_chart(grouped_bar_chart(d, "AGE_GROUP", "TARGET", "CODE_GENDER", "Age Group by Gender", aggfunc="count"), use_container_width=True)

    st.plotly_chart(scatter_chart(d, "AGE_YEARS", "AMT_INCOME_TOTAL", "REPAYMENT_STATUS", "Age vs Income"), use_container_width=True)

    st.subheader("Detailed Data Table")
    display_cols = ["SK_ID_CURR", "CODE_GENDER", "AGE_YEARS", "AGE_GROUP", "NAME_EDUCATION_TYPE",
                     "NAME_FAMILY_STATUS", "NAME_INCOME_TYPE", "OCCUPATION_TYPE", "CNT_CHILDREN", "CNT_FAM_MEMBERS"]
    st.dataframe(d[display_cols], use_container_width=True, hide_index=True)
    st.download_button("Download Filtered Dataset", d[display_cols].to_csv(index=False), "demographics_filtered.csv", "text/csv")

    st.subheader("Key Observations")
    typical_age_group = d["AGE_GROUP"].mode()[0]
    gender_pct = d["CODE_GENDER"].value_counts(normalize=True).mul(100).round(1)
    gender_summary = ", ".join(f"{g}: {p}%" for g, p in gender_pct.items())
    st.markdown(
        f"""
        - The typical Home Credit customer is in the **{typical_age_group}** age group, with
          **{d['NAME_EDUCATION_TYPE'].mode()[0]}** as the most common education level.
        - Gender split: **{gender_summary}**.
        - Family status is dominated by **{d['NAME_FAMILY_STATUS'].mode()[0]}** applicants.
        """
    )

    st.subheader("Business Insights")
    st.markdown(
        """
        - A concentrated demographic profile (one dominant age group, education level, and family
          status) means marketing and underwriting policy tuned to that profile will reach most of
          the current portfolio — but may under-serve or mis-price minority segments.
        - Age and income show the expected general upward relationship for working-age applicants,
          useful context for the affordability ratios built on the Credit Affordability page.
        """
    )

    st.subheader("Recommendations")
    st.markdown(
        """
        1. Tailor communication and product bundling to the dominant customer profile identified
           above, while explicitly reviewing pricing fairness for smaller demographic segments.
        2. Cross-reference the age/education distribution here with the Default Risk EDA page to
           see whether the dominant segment is also the highest- or lowest-risk one.
        3. Track demographic mix over time — a shifting age or education profile can be an early
           signal that acquisition channels are changing.
        """
    )
