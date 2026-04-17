## interaction_app.py
## purpose: vision and garmin data server
from flask import Flask, request, jsonify
import sqlite3
import os
import misty_vision_module as vision_module
from datetime import datetime
import base64
import misty_brain as mb

# Use the Robot instance from your brain
misty = mb.misty

#define flask app 
app = Flask(__name__)

#define directory
DB_NAME = "speculative_misty_memory.db"

# database stays in speculative misty directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, DB_NAME) #path in this directory
UPLOAD_FOLDER = 'incoming_photos'

# Ensures folder actually exists so the app doesn't crash
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

#Initialize SQLite database & create user table
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    #check if the database exists and if not, then init
    cursor.execute(''' 
                   CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            face_id TEXT UNIQUE,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )
''')
    conn.commit()
    conn.close()
    print(f"Database initialized at: {DB_PATH}")

# --- Global State ---
latest_garmin_data = {
    "heart_rate": 70,       # Default baseline
    "activity_type": "STILL" 
}

# ==========================================
# 1. GARMIN ENDPOINTS (Port 5000)
# ==========================================
@app.route('/update_garmin', methods=['POST']) # Matches the Monkey C call
def update_garmin():
    global latest_garmin_data
    try:
        data = request.json
        # Extract HR and Activity
        latest_garmin_data["heart_rate"] = data.get('heart_rate', 70)
        
        # Logic to convert raw score/speed from watch to strings Misty understands
        raw_activity = data.get('activity_type', 'STILL').upper()
        
        # Map Garmin constants to your study's labels
        if "STILL" in raw_activity:
            latest_garmin_data["activity_type"] = "STILL"
            misty.ChangeLED(0, 0, 50) # Dim Blue
        else:
            latest_garmin_data["activity_type"] = "ACTIVE"
            misty.ChangeLED(0, 255, 0) # Green

        print(f"Watch Update -> HR: {latest_garmin_data['heart_rate']}, Act: {latest_garmin_data['activity_type']}")
        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"Garmin Sync Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/current_state', methods=['GET'])
def current_state():
    # Now returns BOTH pieces of data for misty_p01.py
    global latest_garmin_data
    return jsonify(latest_garmin_data)


# ==========================================
# 2. VISION ENDPOINTS (Port 5000)
# ==========================================
#identify face --> captured by her vision system
@app.route('/identify', methods=['POST'])
# purpose: check database to identify a person (based on face)
# checks vision system DB and matches face with name and status (i.e, is_new, bool)
# Name is either a specific name, "unkown", or "error"
def identify():
    data = request.get_json()
    if data and 'base64' in data:
        img_data = base64.b64decode(data['base64'])
        filepath = os.path.join(UPLOAD_FOLDER, "misty_capture.jpg")
        with open(filepath, "wb") as f:
            f.write(img_data)
            
        name = vision_module.identify_face(filepath)
        is_new = False # if person face is unknown, may not be new, just "unknown"

        if name not in ["Unknown", "Error"]:
            # Strip suffixes before checking database ---
            clean_name = name.split('_')[0].lower()

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # 1. Check if user exists
            cursor.execute("SELECT last_seen FROM users WHERE name = ?", (name.lower(),))
            row = cursor.fetchone()
            
            if row:
                # We HAVE met!
                is_new = False
                cursor.execute("UPDATE users SET last_seen = ? WHERE name = ?", 
                               (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), name.lower()))
            else:
                # We have the PHOTO but no DATABASE entry. Let's fix that now.
                print(f"Syncing {name} to SQL database...")
                cursor.execute("INSERT INTO users (name, face_id) VALUES (?, ?)", 
                               (name.lower(), f"{name}.jpg"))
                is_new = True 
        
            conn.commit()
            conn.close()

        #If name is "Unknown", is_new stays False. 
        # This prevents Misty from starting the "What is your name" talk 
        # unless you specifically want her to.

    return jsonify({"status": "success", "identified_as": name, "is_new": is_new})

# View all remembered friends
@app.route('/history', methods=['GET'])
def get_history():
    try:
        conn = sqlite3.connect(DB_PATH)
        # This helper makes the results look like dictionaries instead of lists
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        
        cursor.execute("SELECT name, last_seen FROM users ORDER BY last_seen DESC")
        rows = cursor.fetchall()
        
        # Convert rows to a list of dicts
        history = [dict(row) for row in rows]
        
        conn.close()
        return jsonify({"status": "success", "count": len(history), "history": history})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# learn face that has been captured by vision system --> save to face db
@app.route('/learn', methods=['POST'])
def learn_new_face():
    data = request.get_json()
    name = data.get('name').lower().strip()
    img_b64 = data.get('base64')

    # 1. Save the Image for DeepFace to use later
    img_data = base64.b64decode(img_b64)
    filename = f"{name}.jpg"
    filepath = os.path.join(vision_module.FACES_DB, filename)
    
    with open(filepath, "wb") as f:
        f.write(img_data)

    # 2. Record the encounter in SQLite
    # strip the suffix (like _0) for the SQL 'name' column 
    # so "abena_0" and "abena_1" both count as "abena" in your history.
    clean_name = name.split('_')[0]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO users (name, face_id, last_seen) VALUES (?, ?, ?)",
        (clean_name, filename, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

    # 3. Wipe the DeepFace cache (.pkl) so the new face is active immediately
    try:
        for f in os.listdir(vision_module.FACES_DB):
            if f.endswith(".pkl"):
                os.remove(os.path.join(vision_module.FACES_DB, f))
                print("Cache cleared: New faces are now live.")
    except Exception as e:
        print(f"Warning: Could not clear cache: {e}")

    return jsonify({"status": "success", "message": f"Learned {clean_name}"})


#base app route
@app.route('/')
def home():
    return "Speculative Misty's Interaction Server is ONLINE."

if __name__ == '__main__':
    init_db()
    #listen to all incoming
    app.run(host="0.0.0.0", port = 5000, debug=True) 
                    
       
