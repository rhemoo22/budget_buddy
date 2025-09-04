import streamlit as st
import pandas as pd
import plotly.express as px
from groq import Groq
import os
from datetime import date


st.set_page_config(page_title="Budget Buddy", layout="wide")

st.title("💰 Budget Buddy")
st.subheader("Upload your transactions to see where your money goes!")
st.write("All your information is confidential and will not be shared for any other purposes.  🔒  ")

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
today = date.today()


# Step 1: Upload the file

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:

    # Step 2: Show the formatted table of transactions along with brief advice
    df = pd.read_csv(uploaded_file)
    category_totals = df.groupby("Category")["Amount"].sum().abs().reset_index()

    st.subheader("📑 Transaction Details")
    st.dataframe(df)

    summary_text = category_totals.to_string(index=False)

    chat_completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a smart financial coach. Analyze transactions and give practical, money-saving advice in a kind way that helps the user feel secure."
            },
            {
                "role": "user",
                "content": f"""
Here is my spending summary by category:
{summary_text}

Please suggest ways I can reduce spending, especially on non-essential categories (like coffee, dining, shopping, subscriptions). 
Focus on practical tips, but don't cut out necessities like rent or utilities. Keep it concise, and stay kind and non-judgemental.
Please make me also feel secure that I'm sharing my income with you.
"""
            }
        ],
    )

    st.subheader("💡 AI Financial Advice")
    st.write(chat_completion.choices[0].message.content)

    # Step 3: Show tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Spending Patterns",
        "📅 Subscriptions",
        "🎯 Savings Goals",
        "💸 Deals and Discounts"
        
    ])

    # Tab 1: Spending Breakdown
    with tab1:

        # Spending Pie Chart
        st.subheader("📊 Spending Breakdown")
        spending_only = category_totals[category_totals["Category"] != "Income"]

        fig = px.pie(
            spending_only,
            names="Category",
            values="Amount",
            title="Spending by Category",
            hole=0.2
        )
        st.plotly_chart(fig, use_container_width=True)

        # Spending Heatmap
        st.subheader("🔥 Spending Heatmap")

        df['Date'] = pd.to_datetime(df['Date'])

        spending_df = df[df["Category"] != "Income"].copy()

        spending_df['Weekday'] = spending_df['Date'].dt.day_name()

        weekday_spending = spending_df.groupby(
            ["Weekday", "Category"]
        )["Amount"].sum().abs().reset_index()

        weekdays_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekday_spending['Weekday'] = pd.Categorical(
            weekday_spending['Weekday'],
            categories=weekdays_order,
            ordered=True
        )

        weekday_spending = weekday_spending.sort_values("Weekday")

        fig = px.density_heatmap(
            weekday_spending,
            x="Weekday",
            y="Category",
            z="Amount",
            color_continuous_scale="Reds",
            title="Spending by Day of Week and Category"
        )

        st.plotly_chart(fig, use_container_width=True)



    # Tab 2: Possible Subscriptions & Gray Charges
    with tab2:

        # Subscriptions Table
        st.subheader("⚠️ Possible Subscriptions & Gray Charges")
        transactions_text = df[["Date", "Description", "Amount"]].to_string(index=False)

        subs_completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a financial assistant. Identify recurring or subscription-like charges."
                },
                {
                    "role": "user",
                    "content": f"""
        Here are my transactions:

        {transactions_text}

        Step 1 → Extract a clear list of recurring subscriptions, free trials that became paid, or gray charges. 
        Format ONLY as a neat markdown table with two columns: Merchant | Est. Monthly Cost. Don't name the table.

        Rent and utility bills don't count as subscriptions.
        If there are no clear subscriptions, do not create a table. Mention that there are no subscriptions provided at the time!
        """
                }
            ],
        )

        # Subscriptions Removal Analysis
        analysis_completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a financial assistant. Summarize savings potential from subscriptions."
                },
                {
                    "role": "user",
                    "content": f"""
                    Here are my transactions:

        {transactions_text}
        Based on the subscriptions found in my transactions, write a short analysis:
        Don't list out all the subscriptions and thier price.
        1. Monthly and yearly savings if cancelled or reduced.
        2. Highlight which subscriptions started out as free trials but are now being charged fully. List the name of the 
        service and when the free trial started. Only follow this step if there are subscriptions that started as free trials.
        Keep it concise, kind, and practical.
        
        """
                }
            ],
        )

        col1, col2 = st.columns([1.5, 2])

        with col1:
            st.markdown("### 📋 Subscriptions")
            st.write(subs_completion.choices[0].message.content)

        with col2:
            st.markdown("### 💡 Savings Analysis")
            st.write(analysis_completion.choices[0].message.content)
        


    # Tab 3: Savings Goal     
    with tab3:
        st.subheader("🎯 Set a Savings Goal")
        with st.form("goal_form", clear_on_submit=False):
            goal_amount = st.number_input("Goal Amount ($)", min_value=0, step=100)
            goal_date = st.date_input("Target Date")
            submitted = st.form_submit_button("Analyze Goal")

            if submitted:
                if goal_amount <= 0:
                    st.warning("Please enter a goal greater than 0.")
                else:
                    summary_text = category_totals.to_string(index=False)
                    chat_completion = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a smart financial coach. Help users adjust their budget to meet savings goals."
                            },
                            {
                                "role": "user",
                                "content": f"""
        Here is my spending summary by category:
        {summary_text}

        I want to save **${goal_amount}** by **{goal_date}** and today is {today}.

        1. Is this savings goal feasible based on my current spending?
        2. Suggest specific adjustments by category (monthly), focusing on reducing non-essentials first.
        3. Show how much I should aim to save each month to reach the goal.

        Keep your response concise and kind. Please make me also feel secure that I'm sharing my income with you.
        """
                                    }
                                ],
                            )
                    st.subheader("📊 AI Goal Analysis")
                    st.write(chat_completion.choices[0].message.content)

    # Tab 4: Deals and Discounts
    with tab4:
        st.subheader("💸 Deals and Discounts")
        with st.form("deals_form", clear_on_submit=False):
            occupation = st.text_input("Occupation")
            age = st.number_input("Age", min_value=0, max_value=120)
            submitted = st.form_submit_button("Find me ways to save!")

            if submitted:
                if age <= 0:
                    st.warning("Please enter an age greater than 0.")
                else:
                    summary_text = category_totals.to_string(index=False)
                    chat_completion = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a smart financial coach. Help users adjust their budget to meet savings goals."
                            },
                            {
                                "role": "user",
                                "content": f"""
            Here are my transactions:
            {transactions_text}
            My occupation is {occupation} and I am {age} years old. Please suggest if there any deals or discounts for my 
            occupation and/or age and provide links or resources if available to where I can find more information on that.
            Then if I'm not using certain deals currently, point out specific deals I can save on based on what I already pay 
            for with the newfound information of my age and occupation. If I am using those deals, don't point it out.
            """
                                    }
                                ],
                            )
                    st.write(chat_completion.choices[0].message.content)

    