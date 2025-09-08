import json
import os

DEFAULTS = {
    "vehicle_box_y_ratio": 0.7,
    "crash_zone_x_ratio": 0.5,
    "crash_zone_y_ratio": 0.7,
    "camera_index": 0,
    "camera_name": "Camera 0",
    "alert_cooldown_frames": 15,
    "position_history_frames": 6,
    "movement_threshold": 3.0,
    "debug_draw": False,
    "enable_log": False,
    "enable_fbf": False,
    "alarm_volume": 0.8,
    "alarm_enabled": True,
    "alarm_path": "assets/alert.mp3",
    "history_length": 5,
    "seconds_to_predict": 2,
    "critical_objects": [
        "person", "bicycle", "car", "motorcycle", "bus", "train", "truck",
        "traffic light", "fire hydrant", "stop sign", "parking meter",
        "bench", "cat", "dog", "horse", "sheep", "cow", "elephant",
        "bear", "zebra", "giraffe"
    ]
}

CONFIG_FILE = "user_config.json"

def load_user_settings():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            user = json.load(f)
        return {**DEFAULTS, **user}
    return DEFAULTS

def save_user_settings(settings):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(settings, f, indent=4)
