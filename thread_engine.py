import threading
import time
import random
import datetime

def simulate_device_stream(appliance_name, db_collection, user_email, interval=10):
    """
    Simulates a background thread sending energy data for one appliance.
    """
    while True:
        consumption = random.uniform(0.5, 5.0)
        db_collection.insert_one({
            "appliance": appliance_name,
            "consumption": consumption,
            "added_by": user_email,
            "timestamp": datetime.datetime.now()
        })
        time.sleep(interval)

def start_device_threads(appliances, db_collection, user_email):
    """
    Starts a thread for each appliance to simulate continuous data flow.
    """
    for appliance in appliances:
        thread = threading.Thread(
            target=simulate_device_stream, 
            args=(appliance, db_collection, user_email), 
            daemon=True
        )
        thread.start()
