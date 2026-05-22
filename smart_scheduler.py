import datetime

def suggest_schedule(peak_hours):
    """
    Suggests optimal appliance run times to avoid peak hours.
    """
    if isinstance(peak_hours, str):
        hours = [int(h.split(":")[0]) for h in peak_hours.split(",") if ":" in h]
    else:
        hours = peak_hours

    safe_hours = [h for h in range(24) if h not in hours]

    if not safe_hours:
        return "No safe hours available — consider reducing load."

    recommended = f"{min(safe_hours)}:00 - {max(safe_hours)}:00"
    return f"Suggested off-peak run time: {recommended}"
