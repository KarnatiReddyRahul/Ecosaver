import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import datetime

def predict_peak_hours(df):
    """
    Predicts peak usage hours based on past energy consumption.
    Returns predicted high-usage hour window.
    """
    if df.empty or "timestamp" not in df or "consumption" not in df:
        return "No data available"

    # Extract hour of day
    df["hour"] = df["timestamp"].dt.hour

    hourly_usage = df.groupby("hour")["consumption"].mean().reset_index()

    # Predict using regression model
    X = hourly_usage[["hour"]]
    y = hourly_usage["consumption"]

    model = LinearRegression()
    model.fit(X, y)

    # Predict for all 24 hours
    preds = model.predict(np.arange(24).reshape(-1, 1))

    # Find top 3 peak hours
    top_hours = np.argsort(preds)[-3:][::-1]

    return f"Predicted peak hours: {', '.join(str(int(h)) + ':00' for h in top_hours)}"
