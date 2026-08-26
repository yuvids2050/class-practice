import streamlit as st
from utils.styling import apply_custom_css

from utils.data_loader import load_prepared_application_data
from utils.filters import sidebar_filters, apply_filters
from utils.metrics import fmt_pct, fmt_currency
from utils.charts import histogram, bar_chart, donut_chart, box_plot

st.set_page_config(page_title="Family & Housing Analysis", layout="wide")
apply_custom_css()
st.title("Page 8 — Family & Housing Analysis")
st.caption("**Business Objective:** study household characteristics and how they relate to affordability.")

df = load_prepared_application_data()
filters = sidebar_filters(df)
d = apply_filters(df, filters)

if d.empty:
    st.warning("No applicants match the selected filters.")
else:
    home_ownership_pct = (d["FLAG_OWN_REALTY"] == "Y").mean() * 100
    car_ownership_pct = (d["FLAG_OWN_CAR"] == "Y").mean() * 100

    st.subheader("KPI Cards")
    cols = st.columns(5)
    cols[0].metric("Average Family Size", f"{d['CNT_FAM_MEMBERS'].mean():.2f}")
    cols[1].metric("Average Number of Children", f"{d['CNT_CHILDREN'].mean():.2f}")
    cols[2].metric("Home Ownership %", fmt_pct(home_ownership_pct))
    cols[3].metric("Car Ownership %", fmt_pct(car_ownership_pct))
    cols[4].metric("Most Common Housing Type", d["NAME_HOUSING_TYPE"].mode()[0])

    st.subheader("Visualizations")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(histogram(d, "CNT_FAM_MEMBERS", "Family Size Distribution"), use_container_width=True)
    with col2:
        st.plotly_chart(bar_chart(d, "CNT_CHILDREN", "TARGET", "Children Distribution", aggfunc="count"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(bar_chart(d, "NAME_HOUSING_TYPE", "TARGET", "Housing Type Distribution", aggfunc="count"), use_container_width=True)
    with col2:
        st.plotly_chart(donut_chart(d, "FLAG_OWN_REALTY", "Property Ownership"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(donut_chart(d, "FLAG_OWN_CAR", "Car Ownership"), use_container_width=True)
    with col2:
        st.plotly_chart(box_plot(d, "AMT_INCOME_TOTAL", "CNT_FAM_MEMBERS", "Family Size vs Income"), use_container_width=True)

    st.plotly_chart(bar_chart(d, "CNT_FAM_MEMBERS", "TARGET", "Family Size vs Default Rate", aggfunc="mean"), use_container_width=True)

    st.subheader("Detailed Data Table")
    display_cols = ["SK_ID_CURR", "CNT_FAM_MEMBERS", "CNT_CHILDREN", "NAME_HOUSING_TYPE",
                     "FLAG_OWN_CAR", "FLAG_OWN_REALTY", "AMT_INCOME_TOTAL", "INCOME_PER_FAMILY_MEMBER"]
    st.dataframe(d[display_cols], use_container_width=True, hide_index=True)
    st.download_button("Download Filtered Dataset", d[display_cols].to_csv(index=False), "family_housing_filtered.csv", "text/csv")

    st.subheader("Key Observations")
    st.markdown(
        f"""
        - Average income per family member is **{fmt_currency(d['INCOME_PER_FAMILY_MEMBER'].mean())}**,
          which more fairly reflects affordability than raw household income for larger families.
        - Property ownership sits at **{fmt_pct(home_ownership_pct)}** and car ownership at
          **{fmt_pct(car_ownership_pct)}** across the filtered portfolio.
        - The most common housing arrangement is **{d['NAME_HOUSING_TYPE'].mode()[0]}**.
        """
    )

    st.subheader("Business Insights")
    st.markdown(
        """
        - Larger households show materially lower income-per-member even when total household
          income looks comparable, which affects real repayment capacity beyond what raw income
          suggests.
        - Housing type (e.g. living with parents vs owning) is a useful stability proxy that's
          available at application time without needing a credit bureau pull.
        """
    )

    st.subheader("Recommendations")
    st.markdown(
        """
        1. Use **income per family member**, not raw household income, in affordability scoring for
           larger households.
        2. Treat housing type as a light-touch stability signal in the manual review checklist,
           particularly for applicants not owning their residence.
        3. Track whether family-size-adjusted default rates diverge from raw default rates —
           if they do, affordability policy should weight family size explicitly.
        """
    )
