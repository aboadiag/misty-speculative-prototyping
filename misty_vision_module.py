# misty_vision_module.py
# used to identify face and save to database
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
        detector_backend='opencv', #fast and accurate
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
            if distance > 0.38:
                print(f"Distance {distance:.4f} too high. Treating as Unknown.")
                return "Unknown"
            
            # Extract the name from the filename (e.g., 'kyle.jpg' -> 'kyle')
            best_match_path = best_match['identity']
            filename = os.path.basename(best_match_path)
            raw_name = os.path.splitext(filename)[0]
            clean_name = raw_name.split('_')[0] 
            
            return clean_name
        
        return "Unknown"

    except Exception as e:
        print(f"Vision Error: {e}")
        return "Error"
    
# --- NEW FUNCTION: EMOTION DETECTION ---
def detect_emotion(image_path):
    """
    Analyzes an image to determine the dominant facial emotion.
    Returns strings like: 'happy', 'sad', 'angry', 'fear', 'surprise', 'disgust', 'neutral'
    """
    try:
        # DeepFace.analyze extracts attributes like emotion, age, gender
        results = DeepFace.analyze(
            img_path=image_path,
            actions=['emotion'],
            detector_backend='opencv',
            enforce_detection=False
        )
        
        # DeepFace returns a list of dicts if multiple faces are found, or a single dict
        if isinstance(results, list) and len(results) > 0:
            dominant_emotion = results[0]['dominant_emotion']
        elif isinstance(results, dict):
            dominant_emotion = results['dominant_emotion']
        else:
            return "neutral"
            
        return dominant_emotion

    except Exception as e:
        print(f"Emotion Detection Error: {e}")
        return "neutral"

if __name__ == "__main__":
    print(f"Vision Module Loaded. Looking for faces in: {FACES_DB}")