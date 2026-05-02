import sqlite3
import os
import shutil
from datetime import datetime
import re

DB_NAME = "speculative_misty_memory.db"

def merge_database():
    if not os.path.exists(DB_NAME):
        print("Database not found. Nothing to merge.")
        return

    # 1. Create a backup
    # shutil.copy(DB_NAME, f"{DB_NAME}.backup_{int(datetime.now().timestamp())}")
    # print("Backup created.")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 2. Get all entries
    cursor.execute("SELECT name, face_id, last_seen FROM users")
    rows = cursor.fetchall()

    merged_data = {}

    for name, face_id, last_seen in rows:
        # The core logic: strip the suffix to find the "True Name"
        # true_name = name.split('_')[0].lower().strip()
        true_name = re.sub(r'[\d_]+$', '', name.lower().strip())
        
        if true_name not in merged_data:
            merged_data[true_name] = {
                'face_id': f"{true_name}.jpg",
                'last_seen': last_seen
            }
        else:
            # If we find a more recent 'last_seen', update it
            if last_seen > merged_data[true_name]['last_seen']:
                merged_data[true_name]['last_seen'] = last_seen

    # 3. Wipe and Rebuild the table
    print(f"Merging {len(rows)} entries into {len(merged_data)} unique people...")
    
    cursor.execute("DELETE FROM users")
    
    for name, data in merged_data.items():
        cursor.execute(
            "INSERT INTO users (name, face_id, last_seen) VALUES (?, ?, ?)",
            (name, data['face_id'], data['last_seen'])
        )

    conn.commit()
    conn.close()
    print("Database merge complete! Your history is now clean.")

if __name__ == "__main__":
    merge_database()