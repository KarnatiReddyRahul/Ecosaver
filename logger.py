# logger.py
import random
import datetime

def simulate_iot_data(user_email, appliances, energy_collection):
    """Simulate IoT device sending random energy data for each appliance"""
    for appliance in appliances:
        consumption = random.uniform(0.5, 5.0)  # Random kWh usage
        energy_collection.insert_one({
            "appliance": appliance,
            "consumption": consumption,
            "added_by": user_email,
            "timestamp": datetime.datetime.now()
        })
