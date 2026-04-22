# ==========================================
# SUPPLY CHAIN ANALYTICS DASHBOARD
# Consulting Style Professional Version
# ==========================================

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="Supply Chain Intelligence Dashboard",
    layout="wide"
)

# ==========================================
# PROFESSIONAL UI STYLING
# ==========================================

st.markdown("""
<style>

.main {
    background-color: #F5F7FA;
}

.metric-card {
    background-color: white;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.05);
}

.section-header {
    font-size: 26px;
    font-weight: 600;
}

.success-box {
    padding: 18px;
    border-radius: 10px;
    background-color: #E8F5E9;
    border-left: 6px solid #2E7D32;
    color: #000000;
    font-size: 16px;
}

.warning-box {
    padding: 18px;
    border-radius: 10px;
    background-color: #FFF3E0;
    border-left: 6px solid #EF6C00;
    color: #000000;
    font-size: 16px;
}

.error-box {
    padding: 18px;
    border-radius: 10px;
    background-color: #FFEBEE;
    border-left: 6px solid #C62828;
    color: #000000;
    font-size: 16px;
}

</style>
""", unsafe_allow_html=True)

# ==========================================
# TITLE
# ==========================================

st.title("Business Analysis Dashboard")

# ==========================================
# SIDEBAR NAVIGATION
# ==========================================

st.sidebar.title("Navigation")

section = st.sidebar.radio(
    "Go To",
    [
        "Executive Overview",
        "Sales Performance",
        "Seasonal Analysis",
        "Operational Insights",
        "AI Insights",
        "Recommendations"
    ]
)

# ==========================================
# FILE UPLOAD
# ==========================================

uploaded_file = st.file_uploader(
    "Upload Dataset",
    type=["csv"]
)

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    # ==========================================
    # PREPROCESSING
    # ==========================================

    df["date"] = pd.to_datetime(df["date"])

    df["month"] = df["date"].dt.month

    df["season"] = df["month"].map({
        12: "Winter", 1: "Winter", 2: "Winter",
        3: "Summer", 4: "Summer", 5: "Summer",
        6: "Monsoon", 7: "Monsoon", 8: "Monsoon",
        9: "Autumn", 10: "Autumn", 11: "Autumn"
    })

    # ==========================================
    # COMMON METRICS
    # ==========================================

    total_sales = df["units_sold"].sum()

    avg_price = df["price_unit"].mean()

    avg_delivery = df["delivery_days"].mean()

    utilization = (
        df["delivered_qty"].sum()
        / df["stock_available"].sum()
    )

    # ==========================================
    # EXECUTIVE OVERVIEW
    # ==========================================

    if section == "Executive Overview":

        st.markdown("## 📊 Executive Overview")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Units Sold",
                f"{int(total_sales):,}"
            )

        with col2:
            st.metric(
                "Average Price",
                f"{avg_price:.2f}"
            )

        with col3:
            st.metric(
                "Avg Delivery Days",
                f"{avg_delivery:.2f}"
            )

        with col4:
            st.metric(
                "Stock Utilization %",
                f"{utilization*100:.2f}%"
            )

        st.markdown("---")

        # Sales Trend

        sales_trend = (
            df.groupby("date")["units_sold"]
            .sum()
            .reset_index()
        )

        fig_trend = px.line(
            sales_trend,
            x="date",
            y="units_sold",
            title="Sales Trend Over Time",
            template="plotly_white"
        )

        st.plotly_chart(
            fig_trend,
            use_container_width=True
        )

    # ==========================================
    # SALES PERFORMANCE
    # ==========================================

    elif section == "Sales Performance":

        st.markdown("##Sales Performance")

        col1, col2 = st.columns(2)

        with col1:

            sales_channel = (
                df.groupby("channel")["units_sold"]
                .sum()
                .reset_index()
            )

            fig_channel = px.bar(
                sales_channel,
                x="channel",
                y="units_sold",
                title="Sales by Channel",
                template="plotly_white"
            )

            st.plotly_chart(
                fig_channel,
                use_container_width=True
            )

        with col2:

            sales_region = (
                df.groupby("region")["units_sold"]
                .sum()
                .reset_index()
            )

            fig_region = px.pie(
                sales_region,
                names="region",
                values="units_sold",
                title="Regional Contribution",
                template="plotly_white"
            )

            st.plotly_chart(
                fig_region,
                use_container_width=True
            )

        # Category Performance

        category_sales = (
            df.groupby("category")["units_sold"]
            .sum()
            .reset_index()
        )

        fig_category = px.bar(
            category_sales,
            x="category",
            y="units_sold",
            title="Category Performance",
            template="plotly_white"
        )

        st.plotly_chart(
            fig_category,
            use_container_width=True
        )

    # ==========================================
    # SEASONAL ANALYSIS
    # ==========================================

    elif section == "Seasonal Analysis":

        st.markdown("## Seasonal Demand Analysis")

        seasonal_sales = (
            df.groupby("season")["units_sold"]
            .sum()
            .reset_index()
        )

        fig_season = px.bar(
            seasonal_sales,
            x="season",
            y="units_sold",
            title="Seasonal Sales Distribution",
            template="plotly_white"
        )

        st.plotly_chart(
            fig_season,
            use_container_width=True
        )

        # Heatmap

        pivot = df.pivot_table(
            values="units_sold",
            index="season",
            columns="region",
            aggfunc="sum"
        )

        fig_heat = px.imshow(
            pivot,
            title="Season vs Region Demand Heatmap",
            template="plotly_white"
        )

        st.plotly_chart(
            fig_heat,
            use_container_width=True
        )

    # ==========================================
    # OPERATIONAL INSIGHTS
    # ==========================================

    elif section == "Operational Insights":

        st.markdown("##Operational Efficiency")

        col1, col2 = st.columns(2)

        with col1:

            fig_delivery = px.histogram(
                df,
                x="delivery_days",
                title="Delivery Time Distribution",
                template="plotly_white"
            )

            st.plotly_chart(
                fig_delivery,
                use_container_width=True
            )

        with col2:

            fig_stock = px.scatter(
                df,
                x="stock_available",
                y="units_sold",
                title="Stock vs Sales",
                template="plotly_white"
            )

            st.plotly_chart(
                fig_stock,
                use_container_width=True
            )

        # ==========================================
    # AI INSIGHTS
    # ==========================================

    elif section == "AI Insights":

        st.markdown("##AI-Based Insights")

        # Create Demand Class
        df["Demand_Class"] = (
            df["units_sold"]
            > df["units_sold"].mean()
        ).astype(int)

        demand_counts = (
            df["Demand_Class"]
            .value_counts()
            .reset_index()
        )

        demand_counts.columns = [
            "Demand_Class",
            "Count"
        ]

        demand_counts["Demand_Class"] = (
            demand_counts["Demand_Class"]
            .replace({
                1: "High Demand",
                0: "Low Demand"
            })
        )

        # PIE CHART
        fig_ai = px.pie(
            demand_counts,
            names="Demand_Class",
            values="Count",
            title="Demand Classification Distribution",
            template="plotly_white"
        )

        st.plotly_chart(
            fig_ai,
            use_container_width=True
        )

        # BUSINESS INSIGHT

        if "High Demand" in demand_counts["Demand_Class"].values:

            high_ratio = (
                demand_counts.loc[
                    demand_counts["Demand_Class"]
                    == "High Demand",
                    "Count"
                ].values[0]
                / demand_counts["Count"].sum()
            )

        else:

            high_ratio = 0

        st.info(f"""
**AI Insight**

Approximately **{high_ratio*100:.1f}%** of products fall into the **High Demand** category.

**Business Recommendations:**

• Maintain safety stock for high-demand SKUs  
• Improve demand forecasting accuracy  
• Allocate premium logistics resources  
• Introduce SKU-level demand monitoring  
• Optimize warehouse stocking strategy  

""")
    
    # ==========================================
    # RECOMMENDATIONS
    # ==========================================

    elif section == "Recommendations":

        st.markdown("## Strategic Recommendations")

        avg_delivery = df["delivery_days"].mean()

        stock_ratio = (
            df["delivered_qty"].sum()
            / df["stock_available"].sum()
        )

        # INVENTORY CHECK

        if stock_ratio < 0.75:

            st.markdown("""
<div class="error-box">

**Inventory Risk Detected**

• Increase replenishment frequency  
• Maintain higher safety stock  
• Improve supplier coordination  
• Implement demand forecasting  

</div>
""", unsafe_allow_html=True)

        else:

            st.markdown("""
<div class="success-box">

**Inventory Levels Healthy**

• Maintain replenishment strategy  
• Monitor seasonal spikes  
• Optimize stock distribution  

</div>
""", unsafe_allow_html=True)

        # DELIVERY CHECK

        if avg_delivery > 5:

            st.markdown("""
<div class="warning-box">

**Delivery Performance Risk**

• Optimize logistics routes  
• Review courier efficiency  
• Reduce fulfillment time  

</div>
""", unsafe_allow_html=True)

        else:

            st.markdown("""
<div class="success-box">

 **Delivery Performance Efficient**

• Maintain logistics workflow  
• Monitor delivery KPIs  

</div>
""", unsafe_allow_html=True)

        # STRATEGIC INSIGHTS

        high_demand_season = (
            df.groupby("season")["units_sold"]
            .sum()
            .idxmax()
        )

        slow_region = (
            df.groupby("region")["units_sold"]
            .sum()
            .idxmin()
        )

        st.markdown(f"""
<div class="warning-box">

**Strategic Insights**

**Peak Demand Season:** {high_demand_season}  
→ Increase inventory before this period.

**Lowest Performing Region:** {slow_region}  
→ Review logistics & marketing.

</div>
""", unsafe_allow_html=True)

else:

    st.info("Upload dataset to begin dashboard.")