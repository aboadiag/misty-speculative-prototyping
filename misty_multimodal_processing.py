# misty_multimodal_processing.py
# Purpose: to perform vision processing (e.g. cropping, learning faces, etc)
# and speech processing
# NGROK TUNNEL lives here (herein lies the bridge!)
from mistyPy.Robot import Robot
import base64
import requests
import time
from elevenlabs.client import ElevenLabs
import os
from dotenv import load_dotenv
import re
from PIL import Image
import io
import cv2
import numpy as np
import hashlib

# 1. Try to load the file
load_status = load_dotenv()
print(f"Did .env load successfully? {load_status}")

# Load both detectors globally for speed
FRONTAL_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
PROFILE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')

## IP addresses
TTS_KEY = os.getenv("ELEVEN_LAB_KEY")
NGROK_URL = "https://26eb-128-237-82-216.ngrok-free.app" #NGROK URL ---> all the modality (vision, wearbles, etc) server url

# Search range for the head (Pitch, Roll, Yaw)
# Yaw is left/right. -40 is right, 40 is left.
SEARCH_POSITIONS = [0, -20, -40, 0, 20, 40]


# ------ FOR BANDIT PIPELINE
PRESENCE_SCORE = 0.0
MAX_PRESENCE = 10.0
# human engagement: https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=5453163
FILL_RATE = 1.5   # Gain score quickly when seen
DRAIN_RATE = 0.7  # Lose score slowly when not seen


def check_envs():
    """Validates that secrets are loaded and returns a eleven labs key."""
    if not TTS_KEY:
        print("WARNING: ELEVEN_LAB_KEY missing from .env")
        return None
    
    try:
        return ElevenLabs(api_key=TTS_KEY) #define 11labs api key
    except Exception as e:
        print(f"Failed to initialize TTS Key: {e}")
        return None

# Global initializations
client = check_envs()
AUDIO_FOLDER = "audio_cache"

print(f"TTS_KEY value: {TTS_KEY}")

# Create the folder if it doesn't exist
if not os.path.exists(AUDIO_FOLDER):
    os.makedirs(AUDIO_FOLDER)

import requests

# used for speech generation
CURRENT_USER = "guest"

#set current user
def set_current_user(name):
    global CURRENT_USER
    # Clean it once here
    CURRENT_USER = re.sub(r'_\d+', '', str(name)).lower().strip()

#to play saved audio
def play_cached_audio(file_name, misty_object):
    """Ensures a file from audio_cache is on Misty before playing."""
    local_path = os.path.join(AUDIO_FOLDER, file_name)
    
    if not os.path.exists(local_path):
        print(f"Error: {file_name} not found in {AUDIO_FOLDER}!")
        return

    # 1. Upload to Misty (Same logic as your speak_smart)
    with open(local_path, "rb") as f:
        encoded_audio = base64.b64encode(f.read()).decode('utf-8')
    
    print(f"Syncing {file_name} to Misty...")
    misty_object.SaveAudio(
        fileName=file_name, 
        data=encoded_audio, 
        immediatelyApply=True, # This plays it immediately after upload
        overwriteExisting=True
    )

# use eleven labs api to speak text
def speak_smart(text, misty_object, name=None):
    global CURRENT_USER
    if name:
        set_current_user(name) # Update the global to match the provided name

    VOICE_ID = "SAz9YHcvj6GT2YYXdXww" # River, Relaxed, Neutral, Informative
    VOICE_NAME = "River"
    # VOICE_ID = "21m00Tcm4TlvDq8ikWAM" #rachel
    # VOICE_NAME = "Rachel"

    # Clean the name for natural speech ---
    spoken_text = re.sub(r'_\d+', '', text) # Removes _1, _2, etc.
    spoken_text = spoken_text.replace('_', ' ') # Replaces any other underscores with spaces


    # file_safe_text = "".join([c if c.isalnum() else "_" for c in spoken_text])

    # Generate a Unique Hash based on the FULL text
    # This ensures "Hello how are you today" and "Hello how are you tonight" 
    # get different filenames.
    clean_text = spoken_text.strip().lower()
    text_hash = hashlib.md5(spoken_text.encode()).hexdigest()[:12]

    # filename = f"{VOICE_NAME}_{CURRENT_USER}_{file_safe_text[:25]}.mp3"
    # New Filename format: Voice_User_Hash.mp3
    filename = f"{VOICE_NAME}_{CURRENT_USER}_{text_hash}.mp3"
    local_path = os.path.join(AUDIO_FOLDER, filename)
    # check_credits()

    if not os.path.exists(local_path):
        print(f"Requesting ElevenLabs (Voice: {VOICE_NAME})...")
        try:
            # This is the correct v1.x client path
            response = client.text_to_speech.convert(
                voice_id=VOICE_ID,
                text=spoken_text,
                model_id="eleven_turbo_v2_5",
                output_format="mp3_44100_128",
            )
            
            # The response is an iterator of bytes;  write it to a file
            with open(local_path, "wb") as f:
                for chunk in response:
                    if chunk:
                        f.write(chunk)
            print(f"Saved to {local_path}")
            
        except Exception as e:
            print(f"ElevenLabs Error: {e}")
            return

    # Upload to Misty
    with open(local_path, "rb") as f:
        encoded_audio = base64.b64encode(f.read()).decode('utf-8')
    
    # PascalCase for your specific library
    print(f"Sending audio to Misty: {filename}")
    misty_object.SaveAudio(
        fileName=filename, 
        data=encoded_audio, 
        immediatelyApply=True, 
        overwriteExisting=True
    )


# Purpose: (Helper Function) Ensure dimensions of picture taken is 224 x 224 (compatible for VGG-Face)
# Input: Image thats base 64
# Returns: Image thats 224 x 224 (img base 64) and (bool) face_found
def process_image_for_ai(raw_base64):
    """
    Finds the face (front or side), crops it to a square, and resizes.
    Includes a horizontal flip to detect left-facing profiles.
    """
    # 1. Convert base64 to CV2
    img_data = base64.b64decode(raw_base64)
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        print("Error: Could not decode image.")
        return raw_base64, False

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    face_found = False
    faces = []

    # 2. Try Frontal Face
    faces = FRONTAL_CASCADE.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))

    # 3. If no Frontal, try Profile (Right side)
    if len(faces) == 0:
        faces = PROFILE_CASCADE.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))

    # 4. If still no Profile, FLIP the image and try again (Left side)
    # This is the "Mirror Trick" to catch the left profile
    is_flipped = False
    if len(faces) == 0:
        flipped_gray = cv2.flip(gray, 1)
        faces = PROFILE_CASCADE.detectMultiScale(flipped_gray, 1.1, 5, minSize=(80, 80))
        if len(faces) > 0:
            is_flipped = True
            img = cv2.flip(img, 1) # Flip the color image to match detection

    # 5. Crop if a face was found
    if len(faces) > 0:
        face_found = True
        # Get the largest detected box
        x, y, w, h = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)[0]
        
        # Padding
        pad = int(w * 0.15)
        y1, y2 = max(0, y - pad), min(img.shape[0], y + h + pad)
        x1, x2 = max(0, x - pad), min(img.shape[1], x + w + pad)
        
        img = img[y1:y2, x1:x2]
        print(f"Face successfully cropped (Flipped: {is_flipped})")
    else:
        print("Warning: No face detected.")

    # 6. Resize to AI standard 224x224
    img = cv2.resize(img, (224, 224))

    # 7. Back to Base64
    _, buffer = cv2.imencode('.jpg', img)
    return base64.b64encode(buffer).decode('utf-8'), face_found

#Misty vision processing
# Purpose: Searches for face (name) and whether face has been seen before
# Cross check using vision DB (identify_person)
# Input: None
# Returns: face (name), is_new
def scan_for_person(misty_object, my_evaluator_instance):
    found_name = None
    found_is_new = False
    unknown_found = False

    for yaw_val in SEARCH_POSITIONS:
        print(f"Scanning at angle: {yaw_val}")
        # Move head (Pitch, Roll, Yaw, Velocity)
        # Using PascalCase 'MoveHead' as per your library's likely style
        misty_object.MoveHead(0, 0, yaw_val, 40) 
        time.sleep(3.5) # Wait for head to finish moving
        
        # Get identification
        name, is_new = identify_person(misty_object, evaluator=my_evaluator_instance)

        # 1. Check for a specific name. If found, stop scanning and return it
        if name not in ["Unknown", "Error", "None", None]:
            print(f"Target identified: {name}")
            return name, is_new # Found a specific person, we can stop early!
            
        # 2. If we found an face with unknown name (i.e definitely a face but we don't know who)
        if name == "Unknown":
            print("Saw a face, but not sure who yet. Continuing scan...")
            unknown_found = True # we don't know name, lets check face
            # return "Unknown", True
        
    # After WHOLE loop is done --> saw stranger's face but no known person:
    if unknown_found:
        return "Unknown", True

    # Only return None after checking ALL angles
    return None, False # finished the sweep and saw absolutely nothing
    

# Purpose: (Helper function) Detect face and cross check with vision DB 
# How: Uses Misty's vision system to take a picture --> send thru flask to /identify server, which saves to faces_db
# Input: misty object (from brain) and evaluator object (default = None)
# Returns: Name (based on face), whether person is_new
def identify_person(misty_object, evaluator=None): 
    global PRESENCE_SCORE
    # 1. Ask Misty for a snapshot
    try:
        
        # We use base64=True so the image data comes directly to our script
        # Take picture with mistys vision system that is 640 x 480
        resp = misty_object.TakePicture(base64=True, width=640, height=480)
        if resp.status_code != 200: return None, False
        
        data = resp.json()
        # Handle different potential JSON structures from mistyPy
        raw_b64 = data.get("result", {}).get("base64") or data.get("base64")
        #if not in this format
        if not raw_b64: return None, False

        # --- CROP image to 224 x 224 (for OpenCV)
        # Unpack the tuple into two separate variables
        processed_b64, face_found = process_image_for_ai(raw_b64)

        if face_found:
            img_to_send = processed_b64
            PRESENCE_SCORE = min(MAX_PRESENCE, PRESENCE_SCORE + FILL_RATE)
        else:
            print("Warning: Local crop failed. Sending wide-angle frame to Vision Server.")
            img_to_send = raw_b64 # Use the original 640x480 frame
            # We still give a small presence boost because the Vision Server 
            # might find a face the local cascade missed
            PRESENCE_SCORE = min(MAX_PRESENCE, PRESENCE_SCORE + (FILL_RATE * 0.5))
         
        # 3. Forward image to ngrok tunnel
        api_resp = requests.post(f"{NGROK_URL}/identify", json={"base64": img_to_send})
        result = api_resp.json()

        # DEBUG LOG: See what the server is actually saying
        print(f"DEBUG: Vision Server returned: {result}")
       
        # result.get("identified_as") might be "Abena", "Unknown", or None
        name = result.get("name_to_speak")
        is_new = result.get("is_new", False) # set default is_new: False
        
         # If the server found you (even if local crop failed), boost presence!
        if name and name != "None":
            PRESENCE_SCORE = min(MAX_PRESENCE, PRESENCE_SCORE + FILL_RATE)

        # 3. Inform the Clinical Evaluator immediately
        if evaluator:
            evaluator.update_from_vision(PRESENCE_SCORE)

        return name, is_new
    
    except Exception as e:
        print(f"Identification Error: {e}")
        return "Error", False

# learn person's name --> send request to 
def learn_person(name, processed_b64):
    """Sends the already processed image to the vision server."""
    payload = {"name": name, "base64": processed_b64}
    try:
        requests.post(f"{NGROK_URL}/learn", json=payload, timeout=10)
        print(f"Success: Misty now knows {name}!")
    except Exception as e:
        print(f"Error sending to vision server: {e}")


# Purpose: (Helper function) Asks user their name, Takes 5 images of users face
# Parameters: misty object from misty_brain
# return: name of user
def user_calibration(misty_object):
    """
    Guides the user through a multi-angle photo shoot.
    Misty stays still while the human moves.
    """
    
    # 1. Ensure head is centered and locked
    misty_object.MoveHead(0, 0, 0, 40)
    time.sleep(1)

    # 2. Query person for their name and set the name
    speak_smart("Hi there, before we get started, what is your name?", misty_object)
    name = input("Type name: ").strip() 
    set_current_user(name)

    # 3. Define instructions for the human
    instructions = [
        "To start, please look directly at me.",
        "Now, please turn your head slightly to the left.",
        "Now, turn your head slightly to the right.",
        "Look up slightly.",
        "And finally, look down slightly."
    ]

    # 4. Priming person for calibration sequence
    speak_smart(f"Great! Nice to meet you, {name}. Now, to ensure I'm familiar with you, I need to learn your face.", misty_object)
    time.sleep(5)

    # 5. Calibration sequence
    for i, msg in enumerate(instructions):
        success = False
        attempts = 0
        
        # Speak the instruction ONCE outside the retry loop to save TTS credits
        speak_smart(msg, misty_object)

        while not success and attempts < 3:
            print(f"Waiting for human to pose: {msg}")
            time.sleep(4) 

            # Capture the raw image
            resp = misty_object.TakePicture(base64=True, width=640, height=480)
            data = resp.json()
            raw_b64 = data.get("result", {}).get("base64") or data.get("base64")
            
            if not raw_b64:
                attempts += 1
                continue

            processed_b64, found = process_image_for_ai(raw_b64)
            
            if found:
                print(f"Capturing calibration photo {i+1}/{len(instructions)}...")
                # Use the new version of learn_person that doesn't take a new photo
                learn_person(f"{name}_{i}", processed_b64)
                
                # Visual Feedback
                misty_object.ChangeLED(0, 255, 0) # Green for Success
                time.sleep(0.5)
                success = True
            else:
                attempts += 1
                misty_object.ChangeLED(255, 0, 0) # Red for Error
                if attempts < 3:
                    speak_smart("I didn't quite catch that. Could you adjust slightly?", misty_object)
                    # Small delay to let them move before the loop restarts
                    time.sleep(2)

    speak_smart("Perfect. I have saved those angles to my memory. Calibration complete.", misty_object)
    return name # Return name so the brain knows who it just met


if __name__ == "__main__":
  # Check if key actually exists
    if not TTS_KEY:
        print("CRITICAL: TTS_KEY is empty. Check your .env file!")
    else:
        url = "https://api.elevenlabs.io/v1/voices"
        headers = {
            "xi-api-key": TTS_KEY,
            "Content-Type": "application/json"
        }
        
        print(f"Attempting to fetch voices with key: {TTS_KEY[:5]}***") # Safety check
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            voices = response.json().get('voices', [])
            print(f"{'NAME':<15} | {'VOICE ID':<25} | {'CATEGORY'}")
            print("-" * 60)
            for v in voices:
                # This filter ensures you only see the ones that won't give a 402 error
                    print(f"{v['name']:<15} | {v['voice_id']:<25} | {v['category']}")
        else:
            print(f"Error fetching voices. Status: {response.status_code}")
            print(f"Server says: {response.text}")