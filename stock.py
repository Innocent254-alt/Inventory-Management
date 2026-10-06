import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Page Configuration
st.set_page_config(page_title="Hospitality Inventory Lifecycle", layout="wide")
st.title("📦 Interactive Hospitality Inventory Lifecycle Engine")
st.markdown("Automated Stock Flow Tracking: From Procurement to Plate")

# 2. Complete Structurally Aligned Mock Dataset


@st.cache_data
def load_inventory_data():
    data = {
        'Item_Name': ['Premium Beef Tenderloin', 'Organic Avocados', 'House Red Wine (Case)', 'Dairy Creamer 1L', 'Fresh Salmon Fillet', 'Cooking Oil 20L'],
        'Category': ['Food (Meat)', 'Food (Produce)', 'Beverage', 'Dairy', 'Food (Seafood)', 'Dry Goods'],
        'Purchased_Qty': [100, 200, 50, 150, 80, 60],
        'Unit_Cost': [25.00, 1.50, 120.00, 3.20, 18.50, 45.00],
        # Accounts for shortages at loading dock
        'Received_Qty': [10, 20, 30, 40, 50, 60],
        # Requisitioned out to Kitchens/Bars
        'Issued_Qty': [5, 15, 25, 35, 45, 55],
        # Remaining in central dry/cold storage
        'Physical_Count': [38, 12, 35, 22, 6, 25]
    }
    return pd.DataFrame(data)


df = load_inventory_data()

# Calculate baseline values
df['Total_Purchased_Cost'] = df['Purchased_Qty'] * df['Unit_Cost']
df['Receiving_Variance'] = df['Purchased_Qty'] - df['Received_Qty']
df['Book_Inventory'] = df['Received_Qty'] - df['Issued_Qty']
df['Storage_Variance_Shrink'] = df['Book_Inventory'] - df['Physical_Count']

# 3. Interactive Sidebar Controls
st.sidebar.header("⚙️ Lifecycle Simulation")
st.sidebar.markdown(
    "Adjust parameters to simulate real-world kitchen variables:")

# Global simulation parameters
pos_sales_efficiency = st.sidebar.slider(
    "Kitchen Prep Yield (%)",
    min_value=70, max_value=100, value=92,
    help="Percentage of issued stock that successfully converts to menu item sales without kitchen waste."
)

selected_cat = st.sidebar.multiselect(
    "Filter by Inventory Category:",
    options=df['Category'].unique(),
    default=df['Category'].unique()
)

filtered_df = df[df['Category'].isin(selected_cat)]

# Dynamic calculations based on user slider adjustments
total_issued_value = (filtered_df['Issued_Qty']
                      * filtered_df['Unit_Cost']).sum()
theoretical_sales_value = total_issued_value * \
    (pos_sales_efficiency / 100) * 2.8  # Assumes standard 35% food cost markup
waste_cost_value = total_issued_value * (1 - (pos_sales_efficiency / 100))

# 4. Strategic Financial KPI Cards
st.subheader("📊 Operational Diagnostics Overview")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric("Total Procurement Value",
            f"${(filtered_df['Total_Purchased_Cost']).sum():,.2f}")
kpi2.metric("Dock Receiving Losses",
            f"${(filtered_df['Receiving_Variance'] * filtered_df['Unit_Cost']).sum():,.2f}", delta="Invoice Discrepancies", delta_color="inverse")
kpi3.metric("Storage Shrinkage (Theft/Spoil)",
            f"${(filtered_df['Storage_Variance_Shrink'] * filtered_df['Unit_Cost']).sum():,.2f}", delta="Store Variance", delta_color="inverse")
kpi4.metric("Estimated Kitchen Prep Waste",
            f"${waste_cost_value:,.2f}", delta="Yield Loss", delta_color="inverse")

st.markdown("---")

# 5. Visualizing the Stock Lifecycle Flow (Sankey Diagram)
st.subheader("🔄 Visualizing The Stock Lifecycle Flow")
st.markdown("Track the aggregate volumetric flow of capital from initial procurement to ultimate sales generation:")

# Aggregating totals for flow mapping
purchased_tot = filtered_df['Total_Purchased_Cost'].sum()
received_tot = (filtered_df['Received_Qty'] * filtered_df['Unit_Cost']).sum()
issued_tot = total_issued_value
stored_tot = (filtered_df['Physical_Count'] * filtered_df['Unit_Cost']).sum()
sales_tot = theoretical_sales_value
dock_loss = (filtered_df['Receiving_Variance']
             * filtered_df['Unit_Cost']).sum()
store_loss = (filtered_df['Storage_Variance_Shrink']
              * filtered_df['Unit_Cost']).sum()

# Building a specialized plotly Sankey flowchart map
fig_flow = go.Figure(data=[go.Sankey(
    node=dict(
        pad=15,
        thickness=20,
        line=dict(color="black", width=0.5),
        label=["1. Purchasing Orders", "2. Loading Dock (Received)", "3. Central Storage", "4. Issued To Outlets",
               "5. Ultimate Sales Revenue", "Dock Discrepancy Loss", "Storage Shrinkage", "Kitchen Waste"],
        color=["#2b5c8f", "#348ceb", "#0fa3b1", "#f7a072",
               "#2a9d8f", "#e63946", "#d90429", "#f77f00"]
    ),
    link=dict(
        source=[0, 0, 1, 1, 2, 2, 3, 3],  # From nodes
        target=[1, 2, 3, 4, 5, 6, 7, 8],  # To nodes
        value=[received_tot, dock_loss, issued_tot + store_loss,
               store_loss, stored_tot, store_loss, sales_tot, waste_cost_value]
    ))])

st.plotly_chart(fig_flow, use_container_width=True)

st.markdown("---")

# 6. Granular Item Reconciliation Grid
st.subheader("🔍 SKU-Level Lifecycle Reconciliation Sheet")

display_df = filtered_df[[
    'Item_Name', 'Category', 'Purchased_Qty', 'Received_Qty',
    'Issued_Qty', 'Physical_Count', 'Storage_Variance_Shrink'
]].copy()

# Highlight high-variance items automatically
st.dataframe(
    display_df,
    column_config={
        "Storage_Variance_Shrink": st.column_config.NumberColumn(
            "Variance (Units Missing)",
            help="Difference between what system thinks is in storage vs physical count.",
            format="%d"
        )
    },
    use_container_width=True
)
