import time

def get_stable_value(get_value_func, num_readings=5, delay=0.1):
    """Get a stable value by taking multiple readings and averaging."""
    readings = []
    for _ in range(num_readings):
        readings.append(get_value_func())
        time.sleep(delay)
    
    return sum(readings) / len(readings)

def weight_to_text(weight):
    """Format weight value for display."""
    return f"{weight:.1f}g"