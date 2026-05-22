import streamlit as st
from db_connection import get_database
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import smtplib
from email.mime.text import MIMEText
import random
import datetime
from streamlit_autorefresh import st_autorefresh
import altair as alt
import threading
import time

# =====================================================
# LOAD LOCAL CSS
# =====================================================
def local_css(file_name: str):
    """Load a local CSS file into Streamlit."""
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("⚠️ CSS file not found. Please check the path.")

# =====================================================
# EMAIL ALERT FUNCTION
# =====================================================
def send_email_alert(to_email, appliance, actual, predicted):
    sender_email = "karnatireddyrahul2005@gmail.com"
    app_password = "xeca apgc hdxo rfni"

    subject = f"⚠️ Energy Alert: High Usage in {appliance}"
    body = (
        f"Hello,\n\n"
        f"Your **{appliance}** has consumed **{actual:.2f} kWh**, "
        f"which is higher than the predicted **{predicted:.2f} kWh**.\n\n"
        "Consider reducing usage during peak hours.\n\n"
        "Best Regards,\nECOSAVER Monitoring System"
    )

    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        st.error(f"Failed to send email alert: {e}")

# =====================================================
# PEAK TIME PREDICTION
# =====================================================
def predict_peak_hours(df):
    """Predict peak usage hours using linear regression."""
    if df.empty or "timestamp" not in df or "consumption" not in df:
        return []

    df["hour"] = df["timestamp"].dt.hour
    hourly_usage = df.groupby("hour")["consumption"].mean().reset_index()

    X = hourly_usage[["hour"]]
    y = hourly_usage["consumption"]

    model = LinearRegression()
    model.fit(X, y)

    preds = model.predict(np.arange(24).reshape(-1, 1))
    top_hours = np.argsort(preds)[-3:][::-1]
    return [int(h) for h in top_hours]

# =====================================================
# SMART SCHEDULER
# =====================================================
def suggest_schedule(peak_hours):
    """Suggest off-peak hours based on predicted peaks."""
    if not peak_hours:
        return "No data available for schedule suggestion."

    safe_hours = [h for h in range(24) if h not in peak_hours]
    if not safe_hours:
        return "No safe hours available — consider reducing load."

    return f"Suggested off-peak hours: {min(safe_hours)}:00 - {max(safe_hours)}:00"

# =====================================================
# SIMULATION ENGINE
# =====================================================
def simulate_device_stream(appliance_name, db_collection, user_email, interval=45):
    """Continuously simulate IoT data."""
    while True:
        consumption = random.uniform(0.5, 5.0)
        db_collection.insert_one({
            "appliance": appliance_name,
            "consumption": consumption,
            "added_by": user_email,
            "timestamp": datetime.datetime.now(),
        })
        time.sleep(interval)

def start_device_threads(appliances, db_collection, user_email):
    """Start IoT simulation threads."""
    for appliance in appliances:
        thread = threading.Thread(
            target=simulate_device_stream,
            args=(appliance, db_collection, user_email),
            daemon=True
        )
        thread.start()

# =====================================================
# DASHBOARD FUNCTION
# =====================================================
def run_dashboard(user_email):
    """Main ECOSAVER Dashboard"""
    local_css("style/style.css")
    st_autorefresh(interval=30 * 1000, limit=None, key="iot_refresh")

    db = get_database()
    users_collection = db["users"]
    energy_collection = db["energy_data"]

    # Fetch user info
    user = users_collection.find_one({"email": user_email})
    if not user:
        st.error("User not found in database.")
        return

    appliances = user.get("appliances", [])
    if not appliances:
        st.info("No appliances selected. Please update your profile to begin monitoring.")
        return

    # Start IoT data simulation
    start_device_threads(appliances, energy_collection, user_email)

    st.markdown("### 📊 Real-Time Energy Insights")

    # Chart Colors
    line_color = "#16a34a"
    fill_color_top = "#86efac"
    fill_color_bottom = "#f0fdf4"
    avg_line_color = "#ca8a04"

    for appliance in appliances:
        with st.container():
            # Appliance Header
            st.markdown(
                f"<h4 style='margin-top:25px; margin-bottom:5px; color:#22c55e;'>⚙️ {appliance} Consumption Trend</h4>",
                unsafe_allow_html=True
            )
            st.divider()

            # ✅ Fetch only the latest 10 records for this appliance
            records = list(
                energy_collection
                .find({"added_by": user_email, "appliance": appliance})
                .sort("timestamp", -1)
                .limit(10)
            )
            records.reverse()  # show oldest first for graph order

            if len(records) < 2:
                st.info(f"📡 Collecting IoT data for **{appliance}**... Please wait a few seconds ⏳")
                continue

            # Convert to DataFrame
            df = pd.DataFrame(records)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp").reset_index(drop=True)
            df["index"] = np.arange(len(df))

            # Predict consumption
            X = df[["index"]]
            y = df["consumption"]
            model = LinearRegression()
            model.fit(X, y)
            predicted = model.predict([[len(df)]])[0]
            actual = df["consumption"].iloc[-1]

            # Display current and predicted usage
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="🔌 Latest Usage (kWh)", value=f"{actual:.2f}")
            with col2:
                st.metric(label="📈 Predicted Usage (kWh)", value=f"{predicted:.2f}")

            # Send alert if consumption high
            if actual > predicted:
                send_email_alert(user_email, appliance, actual, predicted)

            # Predict peak hours
            peak_hours = predict_peak_hours(df)
            peak_text = ", ".join(f"{h}:00" for h in peak_hours)
            st.write(f"🕒 **Predicted Peak Hours:** {peak_text or 'No data yet'}")
            st.write(f"💡 **{suggest_schedule(peak_hours)}**")

            # -------------------------
            # ALTair Chart
            # -------------------------
            chart_base = alt.Chart(df).encode(
                x=alt.X("timestamp:T", title="Time"),
                y=alt.Y("consumption:Q", title="Energy (kWh)")
            )

            line = chart_base.mark_line(
                color=line_color,
                interpolate="monotone",
                strokeWidth=3
            ).encode(opacity=alt.value(0.9))

            area = chart_base.mark_area(
                color=alt.Gradient(
                    gradient="linear",
                    stops=[
                        alt.GradientStop(color=fill_color_top, offset=0),
                        alt.GradientStop(color=fill_color_bottom, offset=1)
                    ],
                    x1=1, x2=1, y1=1, y2=0
                ),
                opacity=0.25
            )

            avg_line = alt.Chart(pd.DataFrame({"y": [df["consumption"].mean()]})).mark_rule(
                color=avg_line_color, strokeDash=[6, 4]
            ).encode(y="y:Q")

            final_chart = (area + line + avg_line).properties(
                width="container",
                height=320
            ).configure_axis(
                labelFontSize=12,
                titleFontSize=14
            ).configure_title(
                fontSize=14,
                anchor="start",
                color="#22c55e"
            )

            st.altair_chart(final_chart, use_container_width=True)

            # Expandable historical data table (latest 10 records only)
            with st.expander(f"📋 View {appliance} Latest 10 Records", expanded=False):
                st.dataframe(
                    df[["timestamp", "consumption"]]
                    .sort_values("timestamp", ascending=False)
                    .rename(columns={
                        "timestamp": "Timestamp",
                        "consumption": "Consumption (kWh)"
                    }),
                    use_container_width=True
                )

            st.markdown("<hr>", unsafe_allow_html=True)
