# app/utils.py

import pandas as pd

def calculate_engagement_rate(posts_df):
    posts_df["engagement_rate"] = (posts_df["likes"] + posts_df["comments"]) / posts_df["reach"]
    return posts_df

def calculate_roas(tracking_df, payouts_df):
    total_revenue = tracking_df["revenue"].sum()
    total_payout = payouts_df["total_payout"].sum()
    roas = total_revenue / total_payout if total_payout else 0
    return roas

def get_top_influencers_by_revenue(tracking_df, influencers_df, top_n=5):
    top_df = tracking_df.groupby("influencer_id")["revenue"].sum().reset_index()
    merged = top_df.merge(influencers_df, left_on="influencer_id", right_on="id")
    return merged.sort_values("revenue", ascending=False).head(top_n)

def format_currency(value):
    return f"₹{value:,.2f}"

def get_platform_summary(tracking_df, influencers_df):
    df = tracking_df.merge(influencers_df, left_on="influencer_id", right_on="id")
    return df.groupby("platform")["revenue"].sum().reset_index()
