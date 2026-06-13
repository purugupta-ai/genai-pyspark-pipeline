import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import subprocess
import sys
from src.config import PROCESSED_DATA_DIR, RAW_DATA_DIR

st.set_page_config(page_title="E-Commerce Analytics Pro", layout="wide", page_icon="📊")

def run_pipeline():
    """Triggers the Spark analytics pipeline script."""
    with st.spinner("Running PySpark Analytics Pipeline..."):
        result = subprocess.run([sys.executable, "run_analytics.py"], capture_output=True, text=True)
        if result.returncode == 0:
            st.success("Pipeline executed successfully!")
        else:
            st.error(f"Pipeline failed: {result.stderr}")

@st.cache_data(show_spinner=False)
def load_processed_data(file_name):
    """Loads Parquet data from the processed directory."""
    path = PROCESSED_DATA_DIR / file_name
    if path.exists():
        # Spark saves as a directory of part-files; pandas/pyarrow handles this
        return pd.read_parquet(path)
    return None

st.title("🛒 E-Commerce GenAI Analytics Dashboard")
st.markdown("### Real-time Insights from 1.11M Records")

# Sidebar Configuration
st.sidebar.header("Pipeline Controls")
if st.sidebar.button("🚀 Run Analysis Pipeline", width='stretch'):
    run_pipeline()

st.sidebar.divider()
st.sidebar.info("This dashboard uses PySpark for heavy lifting and Streamlit for visualization.")

# Load Data
df_customers = load_processed_data("top_customers_by_revenue")
df_category = load_processed_data("sales_by_category")
df_trends = load_processed_data("monthly_revenue_trends")

if df_customers is None or df_category is None or df_trends is None:
    st.warning("📊 No processed data found. Please click 'Run Analysis Pipeline' in the sidebar to generate insights.")
else:
    # --- Top Metrics Row ---
    total_rev = df_category['total_revenue'].sum()
    total_orders = df_category['order_count'].sum()
    avg_order = total_rev / total_orders
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Revenue", f"${total_rev/1e6:.1f}M")
    m2.metric("Total Orders", f"{total_orders/1e3:.1f}K")
    m3.metric("Avg Order Value", f"${avg_order:.2f}")

    st.divider()

    # --- Charts Row 1 ---
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("🏆 Top 10 Customers by Revenue")
        fig_cust = px.bar(
            df_customers, 
            x='customer_id', 
            y='total_revenue',
            labels={'customer_id': 'Customer ID', 'total_revenue': 'Revenue ($)'},
            color='total_revenue',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig_cust, width='stretch')

    with c2:
        st.subheader("📦 Sales Distribution by Category")
        fig_cat = px.pie(
            df_category, 
            values='total_revenue', 
            names='category', 
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        st.plotly_chart(fig_cat, width='stretch')

    # --- Charts Row 2 ---
    st.subheader("📈 Monthly Revenue Trends & Growth")
    
    # Prepare trend chart
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=df_trends['month_date'], 
        y=df_trends['monthly_revenue'],
        name='Revenue',
        line=dict(color='firebrick', width=4)
    ))
    
    fig_trend.update_layout(
        xaxis_title="Date",
        yaxis_title="Revenue ($)",
        hovermode="x unified"
    )
    st.plotly_chart(fig_trend, width='stretch')

    # Growth Percentage Data Table
    with st.expander("View Detailed Monthly Growth Data"):
        st.dataframe(df_trends[['month_date', 'monthly_revenue', 'growth_percent']], width='stretch')