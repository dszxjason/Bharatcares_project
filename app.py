"""
Olist E-Commerce Business Intelligence Dashboard

Built for the BharatCares AI/Data Analytics internship project.

Data source: Brazilian E-Commerce Public Dataset by Olist
https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

Expected files (put them in a folder called `data/` next to this script):
    olist_orders_dataset.csv
    olist_order_items_dataset.csv
    olist_customers_dataset.csv
    olist_order_payments_dataset.csv
    olist_order_reviews_dataset.csv
    olist_products_dataset.csv
    product_category_name_translation.csv

Run with:  streamlit run app.py
"""

import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

DATA_DIR = "data"

st.set_page_config(page_title="Olist Business Intelligence", layout="wide")

# 1. LOAD + CLEAN DATA

@st.cache_data
def load_data():
    orders = pd.read_csv(f"{DATA_DIR}/olist_orders_dataset.csv", parse_dates=[
        "order_purchase_timestamp", "order_approved_at",
        "order_delivered_carrier_date", "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ])
    items = pd.read_csv(f"{DATA_DIR}/olist_order_items_dataset.csv")
    customers = pd.read_csv(f"{DATA_DIR}/olist_customers_dataset.csv")
    payments = pd.read_csv(f"{DATA_DIR}/olist_order_payments_dataset.csv")
    reviews = pd.read_csv(f"{DATA_DIR}/olist_order_reviews_dataset.csv")
    products = pd.read_csv(f"{DATA_DIR}/olist_products_dataset.csv")
    categories = pd.read_csv(f"{DATA_DIR}/product_category_name_translation.csv")

    # Only keep orders that were actually delivered or in a normal state.
    # "unavailable" and "canceled" orders would just muddy the revenue numbers.
    valid_status = ["delivered", "shipped", "invoiced", "processing", "approved"]
    orders = orders[orders["order_status"].isin(valid_status)].copy()

    # Give products their English category name so the charts are readable
    products = products.merge(categories, on="product_category_name", how="left")
    products["product_category_name_english"] = products["product_category_name_english"].fillna("other")

    # Build one big order-level table: items -> products -> orders -> customers
    df = items.merge(orders, on="order_id", how="inner")
    df = df.merge(customers, on="customer_id", how="left")
    df = df.merge(products[["product_id", "product_category_name_english"]], on="product_id", how="left")

    # revenue per line item = price + freight (what the customer actually paid to get it)
    df["revenue"] = df["price"] + df["freight_value"]
    df["order_month"] = df["order_purchase_timestamp"].dt.to_period("M").astype(str)

    # was the order delivered later than the estimate we gave the customer?
    df["late_delivery"] = (
        df["order_delivered_customer_date"] > df["order_estimated_delivery_date"]
    )

    # average review score per order, joined back in
    avg_review = reviews.groupby("order_id")["review_score"].mean().rename("review_score")
    df = df.merge(avg_review, on="order_id", how="left")

    return df, payments


def kpi_card(col, label, value, help_text=None):
    col.metric(label, value, help=help_text)

# 2. LOAD (with a friendly error if the CSVs aren't there yet)

try:
    df, payments = load_data()
except FileNotFoundError:
    st.error(
        "Couldn't find the Olist CSV files. Download them from "
        "https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce and drop "
        "all 9 files into a folder called `data/` next to this script."
    )
    st.stop()

# 3. SIDEBAR NAVIGATION

st.sidebar.title("Olist BI Dashboard")
page = st.sidebar.radio(
    "Go to",
    ["Executive Overview", "Sales & Product Analysis", "Customer & Risk Analysis"],
)

min_month, max_month = df["order_month"].min(), df["order_month"].max()
st.sidebar.caption(f"Data covers {min_month} to {max_month}")

# PAGE 1 — EXECUTIVE OVERVIEW

if page == "Executive Overview":
    st.title("Executive Overview")
    st.caption("The five-second version: is the business healthy, and where is it headed?")

    total_revenue = df["revenue"].sum()
    total_orders = df["order_id"].nunique()
    total_customers = df["customer_unique_id"].nunique() if "customer_unique_id" in df.columns else df["customer_id"].nunique()
    aov = total_revenue / total_orders

    monthly = df.groupby("order_month")["revenue"].sum().sort_index()
    growth = 0.0
    if len(monthly) >= 2:
        growth = (monthly.iloc[-1] - monthly.iloc[-2]) / monthly.iloc[-2] * 100

    c1, c2, c3, c4 = st.columns(4)
    kpi_card(c1, "Total Revenue", f"R$ {total_revenue:,.0f}")
    kpi_card(c2, "Total Orders", f"{total_orders:,}")
    kpi_card(c3, "Average Order Value", f"R$ {aov:,.2f}")
    kpi_card(c4, "Month-over-Month Growth", f"{growth:+.1f}%",
              help_text="Comparing the last two full months in the data")

    st.subheader("Revenue trend")
    fig, ax = plt.subplots(figsize=(10, 4))
    monthly.plot(ax=ax, marker="o", color="#2563eb")
    ax.set_ylabel("Revenue (R$)")
    ax.set_xlabel("Month")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1000:.0f}k"))
    plt.xticks(rotation=45)
    st.pyplot(fig)

    st.markdown(
        "**What this tells us:** revenue has generally been "
        f"{'climbing' if growth >= 0 else 'slipping'} month to month, which is the "
        "first thing worth flagging to leadership before digging into *why*."
    )

# PAGE 2 — SALES & PRODUCT ANALYSIS

elif page == "Sales & Product Analysis":
    st.title("Sales & Product Analysis")
    st.caption("Where the money is actually coming from, and what's driving it.")

    top_categories = (
        df.groupby("product_category_name_english")["revenue"]
        .sum().sort_values(ascending=False).head(10)
    )

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top 10 categories by revenue")
        fig, ax = plt.subplots(figsize=(6, 5))
        top_categories.sort_values().plot(kind="barh", ax=ax, color="#16a34a")
        ax.set_xlabel("Revenue (R$)")
        st.pyplot(fig)

    with col2:
        st.subheader("Revenue by state")
        by_state = df.groupby("customer_state")["revenue"].sum().sort_values(ascending=False).head(10)
        fig, ax = plt.subplots(figsize=(6, 5))
        by_state.sort_values().plot(kind="barh", ax=ax, color="#f59e0b")
        ax.set_xlabel("Revenue (R$)")
        st.pyplot(fig)

    st.subheader("How people are paying")
    pay_mix = payments["payment_type"].value_counts(normalize=True) * 100
    fig, ax = plt.subplots(figsize=(8, 3))
    pay_mix.plot(kind="bar", ax=ax, color="#7c3aed")
    ax.set_ylabel("% of payments")
    plt.xticks(rotation=0)
    st.pyplot(fig)

    top_cat_name = top_categories.index[0]
    st.markdown(
        f"**Driver worth calling out:** *{top_cat_name}* is the single biggest revenue "
        "category, so pricing or stock issues there will move the whole business's "
        "numbers more than anywhere else."
    )

# PAGE 3 — CUSTOMER & RISK ANALYSIS

else:
    st.title("Customer & Risk Analysis")
    st.caption("Where things could go wrong, and what to actually do about it.")

    order_level = df.drop_duplicates(subset="order_id")

    late_by_state = (
        order_level.groupby("customer_state")["late_delivery"].mean().sort_values(ascending=False) * 100
    )
    review_by_state = order_level.groupby("customer_state")["review_score"].mean().sort_values()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Late delivery rate by state (top 10 riskiest)")
        fig, ax = plt.subplots(figsize=(6, 5))
        late_by_state.head(10).sort_values().plot(kind="barh", ax=ax, color="#dc2626")
        ax.set_xlabel("% of orders delivered late")
        st.pyplot(fig)

    with col2:
        st.subheader("Average review score by state (lowest 10)")
        fig, ax = plt.subplots(figsize=(6, 5))
        review_by_state.head(10).plot(kind="barh", ax=ax, color="#0891b2")
        ax.set_xlabel("Average review score (1-5)")
        st.pyplot(fig)

    # a customer counts as "repeat" if their unique id shows up on more than one order
    cust_col = "customer_unique_id" if "customer_unique_id" in order_level.columns else "customer_id"
    orders_per_customer = order_level.groupby(cust_col)["order_id"].nunique()
    repeat_rate = (orders_per_customer > 1).mean() * 100

    st.metric("Repeat customer rate", f"{repeat_rate:.1f}%")

    riskiest_state = late_by_state.index[0]
    worst_review_state = review_by_state.index[0]

    st.subheader("Risks, opportunities, and what to do next")
    st.markdown(f"""
- **Risk:** customers in **{riskiest_state}** see the highest rate of late deliveries
  ({late_by_state.iloc[0]:.1f}% of their orders). Late delivery is one of the clearest
  predictors of a bad review, so this region is quietly costing the brand trust.
- **Risk:** **{worst_review_state}** has the lowest average review score
  ({review_by_state.iloc[0]:.2f}/5), which is worth investigating even if delivery
  times there look fine — it could be a product-quality or expectation-mismatch issue.
- **Opportunity:** only **{repeat_rate:.1f}%** of customers come back for a second
  order. Even a small bump here is usually cheaper to win than acquiring new customers,
  so a simple win-back email after a good review could pay off.
- **Recommended action:** prioritize a logistics review for {riskiest_state} before
  the next peak season, and set up an automatic review-score alert so a bad delivery
  region gets caught in weeks, not months.
""")
