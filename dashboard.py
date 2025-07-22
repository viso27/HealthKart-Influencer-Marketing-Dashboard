
import streamlit as st
import pandas as pd
import plotly.express as px


from utils import (
    calculate_engagement_rate,
    calculate_roas,
    get_top_influencers_by_revenue,
    get_platform_summary,
    format_currency
)

# style
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)



# Page Setup
st.set_page_config(page_title="HealthKart Influencer Dashboard", layout="wide")
st.title("📊 HealthKart Influencer Marketing Dashboard")

# Upload Section
with st.expander("📤 Upload Your Campaign Data (Optional)"):
    uploaded_influencers = st.file_uploader("Upload influencers.csv", type="csv")
    uploaded_posts = st.file_uploader("Upload posts.csv", type="csv")
    uploaded_tracking = st.file_uploader("Upload tracking_data.csv", type="csv")
    uploaded_payouts = st.file_uploader("Upload payouts.csv", type="csv")

@st.cache_data
def load_data():
    df_influencers = pd.read_csv("influencers.csv")
    df_posts = pd.read_csv("posts.csv")
    df_tracking = pd.read_csv("tracking_data.csv")
    df_payouts = pd.read_csv("payouts.csv")
    return df_influencers, df_posts, df_tracking, df_payouts

# Load uploaded or default data
if uploaded_influencers and uploaded_posts and uploaded_tracking and uploaded_payouts:
    influencers = pd.read_csv(uploaded_influencers)
    posts = pd.read_csv(uploaded_posts)
    tracking = pd.read_csv(uploaded_tracking)
    payouts = pd.read_csv(uploaded_payouts)
else:
    influencers, posts, tracking, payouts = load_data()

# Sidebar Filters
with st.sidebar:
    st.header("🔎 Filters")
    platform_filter = st.multiselect("Platform", influencers["platform"].unique(), default=influencers["platform"].unique())
    category_filter = st.multiselect("Category", influencers["category"].unique(), default=influencers["category"].unique())
    brand_filter = st.multiselect("Brand", tracking["source"].unique(), default=tracking["source"].unique())
    product_filter = st.multiselect("Product", tracking["product"].unique(), default=tracking["product"].unique())

# Apply filters
influencers_filtered = influencers[
    (influencers["platform"].isin(platform_filter)) &
    (influencers["category"].isin(category_filter))
]

posts_filtered = posts[posts["influencer_id"].isin(influencers_filtered["id"])]
tracking_filtered = tracking[
    (tracking["influencer_id"].isin(influencers_filtered["id"])) &
    (tracking["source"].isin(brand_filter)) &
    (tracking["product"].isin(product_filter))
]
payouts_filtered = payouts[payouts["influencer_id"].isin(influencers_filtered["id"])]

# Enrich and Calculate
posts_filtered = calculate_engagement_rate(posts_filtered)
roas = calculate_roas(tracking_filtered, payouts_filtered)
top5 = get_top_influencers_by_revenue(tracking_filtered, influencers_filtered)
platform_data = get_platform_summary(tracking_filtered, influencers_filtered)

# KPIs
total_revenue = tracking_filtered["revenue"].sum()
total_orders = tracking_filtered["orders"].sum()
total_payout = payouts_filtered["total_payout"].sum()

st.markdown("### 📈 Campaign KPIs")
col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Total Revenue", format_currency(total_revenue))
col2.metric("📦 Total Orders", f"{total_orders}")
col3.metric("🧾 Total Payout", format_currency(total_payout))
col4.metric("📊 ROAS", f"{roas:.2f}x")

# Post Performance Summary
st.markdown("### 🧵 Post Performance Summary")
col5, col6 = st.columns(2)
col5.metric("📢 Avg Reach per Post", f"{posts_filtered['reach'].mean():,.0f}")
col6.metric("💬 Avg Engagement Rate", f"{posts_filtered['engagement_rate'].mean():.2%}")

# Top Influencers
st.markdown("### 🏆 Top 5 Influencers by Revenue")
st.dataframe(top5[["name", "platform", "category", "revenue"]])

# Revenue by Platform
st.markdown("### 🔍 Revenue by Platform")
fig = px.pie(platform_data, names="platform", values="revenue", title="Revenue Share by Platform", hole=0.4)
st.plotly_chart(fig, use_container_width=True)

# Best Personas
st.markdown("### 🌟 Best Performing Influencer Personas")
persona_perf = tracking_filtered.merge(influencers_filtered, left_on="influencer_id", right_on="id")
persona_group = persona_perf.groupby(["category", "gender"])["revenue"].mean().reset_index()
st.dataframe(persona_group.sort_values("revenue", ascending=False).head(5))

# Poor ROIs
rev_grouped = tracking_filtered.groupby("influencer_id")["revenue"].sum().reset_index()
merged_rev = payouts_filtered.merge(rev_grouped, on="influencer_id", how="left")
merged_rev["roas"] = merged_rev["revenue"] / merged_rev["total_payout"]
merged_rev = merged_rev.merge(influencers_filtered, left_on="influencer_id", right_on="id")
low_roas = merged_rev.sort_values("roas").head(5)
st.markdown("### 🔻 Lowest Performing Influencers (Poor ROIs)")
st.dataframe(low_roas[["name", "platform", "category", "revenue", "total_payout", "roas"]])

# Incremental ROAS
st.markdown("### ⚡ Incremental ROAS by Brand")
baseline = {"MuscleBlaze": 30000, "HKVitals": 20000, "Gritzo": 10000}
brand_rev = tracking_filtered.groupby("source")["revenue"].sum().reset_index()
brand_rev["baseline"] = brand_rev["source"].map(baseline)
brand_rev["incremental_rev"] = brand_rev["revenue"] - brand_rev["baseline"]
brand_rev["incremental_roas"] = brand_rev["incremental_rev"] / total_payout
st.dataframe(brand_rev)

# Export
st.markdown("### 📤 Export Filtered Tracking Data")
st.download_button("📥 Download CSV", data=tracking_filtered.to_csv(index=False), file_name="filtered_tracking_data.csv")
