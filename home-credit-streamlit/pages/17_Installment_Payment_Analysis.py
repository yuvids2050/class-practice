import streamlit as st
from utils.styling import apply_custom_css

from utils.data_loader import load_installments_raw
from utils.feature_engineering import add_installment_features, aggregate_installment_features, classify_payment_amount
from utils.metrics import fmt_number, fmt_pct
from utils.charts import histogram, donut_chart, scatter_chart, horizontal_bar_chart

st.set_page_config(page_title="Installment Payment Analysis", layout="wide")
apply_custom_css()
st.title("Page 17 — Installment Payment Analysis")
st.caption("**Business Objective:** understand actual repayment behaviour — one of the most useful credit-risk indicators available.")
st.markdown(
    """
    **Feature engineering:**
    """
)
st.latex(r"\text{Payment Delay} = \text{DAYS\_ENTRY\_PAYMENT} - \text{DAYS\_INSTALMENT}")
st.latex(r"\text{Payment Difference} = \text{AMT\_PAYMENT} - \text{AMT\_INSTALMENT}")
st.latex(r"\text{Payment Ratio} = \text{AMT\_PAYMENT} \, / \, \text{AMT\_INSTALMENT}")

installments = load_installments_raw()
inst = add_installment_features(installments)
inst["PAYMENT_AMOUNT_CLASS"] = inst["PAYMENT_RATIO"].apply(classify_payment_amount)

st.sidebar.header("Filters")
class_filter = st.sidebar.multiselect("Payment Timing Class", options=sorted(inst["PAYMENT_CLASS"].unique()), default=sorted(inst["PAYMENT_CLASS"].unique()))
i = inst[inst["PAYMENT_CLASS"].isin(class_filter)]

if i.empty:
    st.warning("No installment records match the selected filters.")
else:
    on_time = (i["PAYMENT_CLASS"] == "On-Time Payment").sum()
    late = (i["PAYMENT_CLASS"] == "Late Payment").sum()
    underpay = (i["PAYMENT_AMOUNT_CLASS"] == "Underpayment").sum()
    total = len(i)

    st.subheader("KPI Cards")
    cols = st.columns(4)
    cols[0].metric("Total Installments", fmt_number(total))
    cols[1].metric("Average Installment", f"${i['AMT_INSTALMENT'].mean():,.0f}")
    cols[2].metric("Average Payment", f"${i['AMT_PAYMENT'].mean():,.0f}" if i["AMT_PAYMENT"].notna().any() else "N/A")
    cols[3].metric("On-Time Payment %", fmt_pct(on_time / total * 100 if total else 0))
    cols = st.columns(3)
    cols[0].metric("Late Payment %", fmt_pct(late / total * 100 if total else 0))
    cols[1].metric("Underpayment %", fmt_pct(underpay / total * 100 if total else 0))
    cols[2].metric("Average Delay Days", f"{i['PAYMENT_DELAY'].mean():.1f}")

    st.subheader("Visualizations")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(histogram(i.dropna(subset=["PAYMENT_DELAY"]), "PAYMENT_DELAY", "Payment Delay Distribution"), use_container_width=True)
    with col2:
        st.plotly_chart(donut_chart(i, "PAYMENT_CLASS", "On-Time vs Late Payments"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        sample_pool = i.dropna(subset=["AMT_INSTALMENT", "AMT_PAYMENT"])
        sample = sample_pool.sample(min(3000, len(sample_pool)), random_state=42)
        st.plotly_chart(scatter_chart(sample, "AMT_INSTALMENT", "AMT_PAYMENT", "PAYMENT_CLASS", "Scheduled vs Actual Payment"), use_container_width=True)
    with col2:
        st.plotly_chart(histogram(i.dropna(subset=["PAYMENT_DIFFERENCE"]), "PAYMENT_DIFFERENCE", "Payment Difference Distribution"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        late_by_customer = i[i["PAYMENT_CLASS"] == "Late Payment"].groupby("SK_ID_CURR").size().reset_index(name="Late Payment Count")
        top_late = late_by_customer.sort_values("Late Payment Count", ascending=False).head(15)
        st.plotly_chart(horizontal_bar_chart(top_late, "SK_ID_CURR", "Late Payment Count", "Top 15 Customers by Late Payment Count", aggfunc="sum", ascending=True), use_container_width=True)
    with col2:
        sample2_pool = i.dropna(subset=["PAYMENT_DELAY", "AMT_PAYMENT"])
        sample2 = sample2_pool.sample(min(3000, len(sample2_pool)), random_state=42)
        st.plotly_chart(scatter_chart(sample2, "PAYMENT_DELAY", "AMT_PAYMENT", "PAYMENT_AMOUNT_CLASS", "Delay Days vs Payment Amount"), use_container_width=True)

    st.subheader("Customer-Level Repayment Features")
    inst_agg = aggregate_installment_features(inst)
    st.dataframe(inst_agg.head(200), use_container_width=True, hide_index=True)
    st.download_button("Download Installment Aggregates (per customer)", inst_agg.to_csv(index=False), "installment_customer_aggregates.csv", "text/csv")

    st.subheader("Key Observations")
    high_late_customers = (inst_agg["LATE_PAYMENT_PERCENTAGE"] > 20).sum()
    st.markdown(
        f"""
        - **{fmt_pct(late / total * 100 if total else 0)}** of individual installments were paid
          late in this sample.
        - **{fmt_number(high_late_customers)}** customers have a late-payment percentage above 20% —
          a meaningful repeat-delay pattern rather than an isolated late payment.
        - Underpayments (paid less than scheduled) occur in **{fmt_pct(underpay / total * 100 if total else 0)}**
          of installments and are a distinct risk signal from simple lateness.
        """
    )

    st.subheader("Business Insights")
    st.markdown(
        """
        - Repayment behaviour observed directly (this table) is a more concrete signal than
          demographic or affordability proxies — it shows what customers *actually did*, not just
          what their profile suggests they might do.
        - A customer with a rising trend of late payments across successive installments represents
          increasing repayment stress even before any installment is fully missed.
        """
    )

    st.subheader("Recommendations")
    st.markdown(
        """
        1. Build an **early-warning operational report** that flags customers with 2+ consecutive
           late payments for proactive outreach, rather than waiting for a full default.
        2. Distinguish **underpayment** from simple **lateness** in monitoring — underpayment on an
           otherwise-on-time schedule can signal a different (harder to resolve) affordability issue.
        3. Feed `LATE_PAYMENT_PERCENTAGE` and `AVG_PAYMENT_DELAY` into the risk segmentation rules
           (Page 19) as one of the strongest available repayment-behaviour signals.
        """
    )
