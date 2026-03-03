#misty_vision_module.py
from deepface import DeepFace
import os
import pandas as pd

# Setup paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FACES_DB = os.path.join(BASE_DIR, "known_faces")

# Check whether the directory exists
if not os.path.exists(FACES_DB):
    os.makedirs(FACES_DB)


# Function: Identify face using VGG-face
def identify_face(image_path):
    """
    Analyzes an image and compares it to the 'known_faces' directory.
    """
    try:
        # DeepFace.find returns a list of pandas DataFrames
        results = DeepFace.find(
        img_path=image_path,
        db_path=FACES_DB,
        # model_name='ArcFace', #VGG-Face #Reliable and relatively fast
        # detector_backend='retinaface',  # best accuracy
        model_name='VGG-Face',
        detector_backend='opencv',
        distance_metric='cosine',   # 'cosine' is generally better for lighting changes
        enforce_detection=False     # Prevents crashing if a face isn't perfectly clear
    )

        # Check if we found any matches
        if len(results) > 0 and not results[0].empty:
            # results[0] is sorted by 'distance' automatically
            best_match = results[0].iloc[0]
            distance = best_match['distance']

            print(f"Match found with distance: {distance}")

            # --- THE FIX: ENFORCE STRICTNESS ---
            # If the distance is > 0.45, Misty is just guessing.
            if distance > 0.45:
                return "Unknown"
            
            # Extract the name from the filename (e.g., 'kyle.jpg' -> 'kyle')
            best_match_path = best_match['identity']
            filename = os.path.basename(best_match_path)
            name = os.path.splitext(filename)[0]
            
            return name
        
        return "Unknown"

    except Exception as e:
        print(f"Vision Error: {e}")
        return "Error"

if __name__ == "__main__":
    print(f"Vision Module Loaded. Looking for faces in: {FACES_DB}")