# energy_ui.py
import streamlit as st
import pandas as pd
import altair as alt
from db_connection import get_database
from logger import simulate_iot_data
from peak_time_predictor import predict_consumption
from smart_scheduler import send_email_alert
from thread_engine import start_auto_refresh

def run_dashboard(user_email):
    st.title("⚡ ECOSAVER Energy Dashboard (Modular Version)")

    db = get_database()
    users_collection = db["users"]
    energy_collection = db["energy_data"]

    # Auto-refresh every 30 seconds
    start_auto_refresh()

    # Fetch user appliances
    user = users_collection.find_one({"email": user_email})
    if not user:
        st.error("User not found!")
        return

    appliances = user.get("appliances", [])
    if not appliances:
        st.info("No appliances selected. Please update your profile.")
        return

    st.subheader("Live Energy Data & Predictions")

    # Simulate new IoT data automatically
    simulate_iot_data(user_email, appliances, energy_collection)

    for appliance in appliances:
        st.markdown(f"### {appliance}")

        # Fetch all records for this appliance
        records = list(energy_collection.find({"added_by": user_email, "appliance": appliance}))
        if not records:
            st.info(f"No energy data for {appliance} yet.")
            continue

        df = pd.DataFrame(records)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Predict usage
        actual, predicted = predict_consumption(df)

        st.write(f"Latest Usage: {actual:.2f} kWh")
        st.write(f"Predicted Usage: {predicted:.2f} kWh")

        # Email alert if threshold exceeded
        if actual > predicted:
            send_email_alert(user_email, appliance, actual, predicted)

        # Chart visualization
        chart = alt.Chart(df).mark_line(point=True).encode(
            x='timestamp:T',
            y='consumption:Q',
            tooltip=['timestamp:T', 'consumption:Q']
        ).properties(
            width=700,
            height=300,
            title=f"{appliance} Consumption Over Time"
        )
        st.altair_chart(chart, use_container_width=True)

        # Table
        st.subheader(f"{appliance} Consumption Table")
        st.dataframe(df[['timestamp', 'consumption']].sort_values('timestamp', ascending=False))
