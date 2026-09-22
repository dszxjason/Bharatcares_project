# Olist E-Commerce Business Intelligence Dashboard

This is my project for the BharatCares data analytics internship. The idea
was to take a raw e-commerce dataset and turn it into something a business
owner could actually use to make a decision, not just a bunch of charts.

## What it does

It's a Streamlit app with three pages:

1. **Executive Overview** – total revenue, orders, customers, average order
   value, and month-over-month growth, plus a revenue trend line.
2. **Sales & Product Analysis** – which product categories and states bring
   in the most revenue, and how customers are paying.
3. **Customer & Risk Analysis** – which states have the worst late-delivery
   rates and review scores, the repeat customer rate, and a short list of
   risks/opportunities/recommended actions based on what the data shows.

I deliberately kept it to three pages instead of piling on filters and
extra charts. The point is that someone should be able to open this and
know within a minute what's going well, what isn't, and what to do about it.

## Dataset

Brazilian E-Commerce Public Dataset by Olist:
https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

It's real (anonymized) order data from ~100k orders on a Brazilian
marketplace between 2016-2018, which is why the currency is R$ (Brazilian
Real) and the states are Brazilian state codes (SP, RJ, MG, etc.).

## How to run it

1. Download the dataset from the Kaggle link above and unzip it.
2. Create a folder called `data` next to `app.py` and put these 7 files
   inside it:
   - `olist_orders_dataset.csv`
   - `olist_order_items_dataset.csv`
   - `olist_customers_dataset.csv`
   - `olist_order_payments_dataset.csv`
   - `olist_order_reviews_dataset.csv`
   - `olist_products_dataset.csv`
   - `product_category_name_translation.csv`
3. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run it:
   ```
   streamlit run app.py
   ```

It'll open in your browser automatically. If the `data` folder isn't set
up right, the app will tell you exactly what it's missing instead of just
crashing.

## KPIs I picked and why

Out of everything in the dataset, I went with revenue, order volume,
average order value, growth rate, late-delivery rate, review score, and
repeat customer rate. These map onto the actual questions a business
owner cares about: is revenue moving in the right direction, what's
driving it, where's the delivery/quality risk, and are customers coming
back. I skipped things like exact shipping cost breakdowns and seller-level
stats since they didn't change the story being told here.

## Notes

- "Revenue" per order = item price + freight value (what the customer
  actually paid to get the product delivered), not just the sticker price.
- Orders marked "canceled" or "unavailable" are excluded from the revenue
  numbers since they were never actually fulfilled.
- Late delivery = delivered after the estimated delivery date Olist gave
  the customer at checkout.
