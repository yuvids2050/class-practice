import streamlit as st
from utils.styling import apply_custom_css

from utils.data_loader import load_prepared_application_data
from utils.filters import sidebar_filters, apply_filters
from utils.metrics import top_bottom_by_default_rate, default_rate_by
from utils.charts import histogram, bar_chart, horizontal_bar_chart, scatter_chart

st.set_page_config(page_title="Employment Analysis", layout="wide")
apply_custom_css()
st.title("Page 7 — Employment Analysis")
st.caption("**Business Objective:** understand employment stability and its relationship with credit behaviour.")
st.latex(r"\text{Employment Years} = \frac{|\text{DAYS\_EMPLOYED}|}{365}")
st.caption(
    "Required preprocessing: DAYS_EMPLOYED contains an anomalous placeholder value (365243, mostly "
    "pensioners/not currently employed) which is cleaned to missing before this conversion — otherwise "
    "it would imply ~1000 years of employment."
)

df = load_prepared_application_data()
filters = sidebar_filters(df)
d = apply_filters(df, filters)

if d.empty:
    st.warning("No applicants match the selected filters.")
else:
    d_emp = d.dropna(subset=["EMPLOYMENT_YEARS"])
    highest_risk_group, _ = top_bottom_by_default_rate(d, "EMPLOYMENT_GROUP", min_count=5)

    st.subheader("KPI Cards")
    cols = st.columns(5)
    cols[0].metric("Average Employment Years", f"{d_emp['EMPLOYMENT_YEARS'].mean():.1f}")
    cols[1].metric("Median Employment Years", f"{d_emp['EMPLOYMENT_YEARS'].median():.1f}")
    cols[2].metric("Most Common Occupation", d["OCCUPATION_TYPE"].mode()[0] if d["OCCUPATION_TYPE"].notna().any() else "N/A")
    cols[3].metric("Most Common Organization Type", d["ORGANIZATION_TYPE"].mode()[0])
    cols[4].metric("Highest Default Employment Group", str(highest_risk_group))

    st.subheader("Visualizations")
    st.plotly_chart(histogram(d_emp, "EMPLOYMENT_YEARS", "Employment Years Distribution"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(bar_chart(d, "EMPLOYMENT_GROUP", "TARGET", "Employment Group Distribution", aggfunc="count"), use_container_width=True)
    with col2:
        st.plotly_chart(bar_chart(d, "EMPLOYMENT_GROUP", "TARGET", "Default Rate by Employment Group", aggfunc="mean"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(
            horizontal_bar_chart(d.dropna(subset=["OCCUPATION_TYPE"]), "OCCUPATION_TYPE", "TARGET", "Occupation vs Default Rate (Top 12)", top_n=12, aggfunc="mean", ascending=False),
            use_container_width=True,
        )
    with col2:
        st.plotly_chart(
            horizontal_bar_chart(d.dropna(subset=["ORGANIZATION_TYPE"]), "ORGANIZATION_TYPE", "TARGET", "Organization Type vs Default (Top 12)", top_n=12, aggfunc="mean", ascending=False),
            use_container_width=True,
        )

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(scatter_chart(d_emp, "EMPLOYMENT_YEARS", "AMT_INCOME_TOTAL", "REPAYMENT_STATUS", "Employment Years vs Income"), use_container_width=True)
    with col2:
        st.plotly_chart(scatter_chart(d_emp, "EMPLOYMENT_YEARS", "AMT_CREDIT", "REPAYMENT_STATUS", "Employment Years vs Credit"), use_container_width=True)

    st.subheader("Detailed Data Table")
    st.dataframe(default_rate_by(d, "EMPLOYMENT_GROUP"), use_container_width=True, hide_index=True)
    st.download_button("Download Employment Group Summary", default_rate_by(d, "EMPLOYMENT_GROUP").to_csv(index=False), "employment_group_summary.csv", "text/csv")

    st.subheader("Key Observations")
    st.markdown(
        f"""
        - The **{highest_risk_group}** employment tenure group shows the highest observed default
          rate — shorter employment history tends to associate with higher observed risk.
        - Occupation and organization type both show meaningfully different default rates across
          categories, suggesting employment context carries real signal beyond income alone.
        """
    )

    st.subheader("Business Insights")
    st.markdown(
        """
        - Employment tenure is a readily available, low-cost signal at application time — it doesn't
          require third-party data and can be captured directly on the application form.
        - Occupation-level risk differences may reflect income volatility (e.g. commission-based
          roles) rather than occupation prestige — worth investigating alongside income data before
          drawing policy conclusions.
        """
    )

    st.subheader("Recommendations")
    st.markdown(
        f"""
        1. Include employment tenure (particularly the **{highest_risk_group}** band) as a factor in
           manual underwriting review checklists.
        2. Flag occupation/organization categories with both high default rates and reasonable
           sample sizes for targeted policy review, rather than acting on small-sample noise.
        3. Consider requesting employment verification for very short tenure applicants
           (< 1 year) given the elevated observed risk in that band.
        """
    )
