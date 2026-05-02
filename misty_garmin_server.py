# misty_garmin_server.py
from flask import Flask, request, jsonify
import misty_brain as mb
import os

# Use the Robot instance from your brain
misty = mb.misty

app = Flask(__name__)

# Global variable to store the last activity
last_recorded_activity = "STILL"

@app.route('/update_activity', methods=['POST'])
def update_activity():
    global last_recorded_activity
    data = request.json
    last_recorded_activity = data.get('activity_type', 'STILL')

    try:
        data = request.json
        # Garmin/Phone Apps usually send activity as a string or ID
        activity = data.get('activity_type', 'UNKNOWN').upper()
        confidence = data.get('confidence', 100) # How sure the sensor is
        
        print(f"P01 Activity Detected: {activity} ({confidence}% confidence)")
        
        # --- REACTION LOGIC ---
        if activity == "STILL":
            # Misty turns Dim Blue and looks slightly down (resting)
            misty.ChangeLED(0, 0, 50)
            print("Misty enters Resting Mode.")
            
        elif activity in ["WALKING", "ON_FOOT"]:
            # Misty turns Green and looks up/excited
            misty.ChangeLED(0, 255, 0)
            misty.MoveHead(-10, 0, 0, 40)
            print("Misty acknowledges movement!")
            
        elif activity in ["RUNNING", "CYCLING"]:
            # Misty pulses Red/Orange for high intensity
            misty.TransitionLED(255, 69, 0, 0, 0, 0, "Blink", 500)
            print("Misty detects high intensity workout!")

        return jsonify({"status": "updated"}), 200

    except Exception as e:
        print(f"Activity Update Error: {e}")
        return jsonify({"error": str(e)}), 500
    

@app.route('/current_state', methods=['GET'])
def current_state():
    return jsonify({"activity_type": last_recorded_activity})

if __name__ == '__main__':
    # Using Port 5001 to avoid conflict with the Vision Server on 5000
    app.run(host='0.0.0.0', port=5000)