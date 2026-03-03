## interaction_app.py
## purpose: vision and data server
from flask import Flask, request, jsonify
import sqlite3
import os
import misty_vision_module as vision_module
from datetime import datetime
import base64

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

#identify face --> captured by her vision system
@app.route('/identify', methods=['POST'])
def identify():
    data = request.get_json()
    if data and 'base64' in data:
        img_data = base64.b64decode(data['base64'])
        filepath = os.path.join(UPLOAD_FOLDER, "misty_capture.jpg")
        with open(filepath, "wb") as f:
            f.write(img_data)
            
        name = vision_module.identify_face(filepath)
        is_new = True

        if name not in ["Unknown", "Error"]:
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
                is_new = False # Set to false so she greets you properly immediately
            
            conn.commit()
            conn.close()

    return jsonify({"status": "success", "identified_as": name, "is_new": is_new})

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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO users (name, face_id, last_seen) VALUES (?, ?, ?)",
        (name, filename, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

    # 3. Wipe the DeepFace cache (.pkl) so the new face is active immediately
    for f in os.listdir(vision_module.FACES_DB):
        if f.endswith(".pkl"):
            os.remove(os.path.join(vision_module.FACES_DB, f))

    return jsonify({"status": "success", "message": f"Learned {name}"})


#base app route
@app.route('/')
def home():
    return "Speculative Misty's Interaction Server is ONLINE."

if __name__ == '__main__':
    init_db()
    #listen to all incoming
    app.run(host="0.0.0.0", port = 5000, debug=True) 
                    
       
