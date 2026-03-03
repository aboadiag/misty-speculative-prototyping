# misty_brain.py
# misty behavioral (speech, movement, etc) module
from mistyPy.Robot import Robot
import base64
import requests
import time
from elevenlabs.client import ElevenLabs
import os
from dotenv import load_dotenv

# 1. Try to load the file
load_status = load_dotenv()
print(f"Did .env load successfully? {load_status}")

## IP addresses
MISTY_IP = os.getenv("ROBOT_URL")
TTS_KEY = os.getenv("ELEVEN_LAB_KEY")
NGROK_URL = "https://d9b7-128-237-82-210.ngrok-free.app" #NGROK URL --->vision server url


def check_envs():
    """Validates that secrets are loaded and returns a Misty object."""
    if not MISTY_IP:
        print("CRITICAL: MISTY_IP (ROBOT_URL) missing from .env")
        return None
    if not TTS_KEY:
        print("WARNING: ELEVEN_LAB_KEY missing from .env")
    
    try:
        return Robot(MISTY_IP)
    except Exception as e:
        print(f"Failed to initialize Misty: {e}")
        return None

# Global initializations
misty = check_envs() #define robot --> misty = Robot(MISTY_IP)
client = ElevenLabs(api_key=TTS_KEY) #define 11labs api key
AUDIO_FOLDER = "audio_cache"

print(f"MISTY_IP value: {MISTY_IP}")
print(f"TTS_KEY value: {TTS_KEY}")

# Create the folder if it doesn't exist
if not os.path.exists(AUDIO_FOLDER):
    os.makedirs(AUDIO_FOLDER)


# Search range for the head (Pitch, Roll, Yaw)
# Yaw is left/right. -40 is right, 40 is left.
SEARCH_POSITIONS = [0, -20, -40, 0, 20, 40]
last_seen_name = None #indicates the name last seen
last_seen_time = 0 # and time last seen 

#check how many tts credits I have --> eleven labs
# def check_credits():
#     try:
#         user_info = client.user.get()
#         usage = user_info.subscription.character_count
#         limit = user_info.subscription.character_limit
#         remaining = limit - usage
#         print(f"--- ElevenLabs Usage ---")
#         print(f"Used: {usage} | Limit: {limit} | Remaining: {remaining}")
#         return remaining
#     except Exception as e:
#         print(f"Could not fetch credits: {e}")
#         return 0
    

# use eleven labs api to speak text
def speak_smart(text):
    VOICE_ID = "21m00Tcm4TlvDq8ikWAM" #rachel
    clean_text = "".join([c if c.isalnum() else "_" for c in text])
    filename = f"{clean_text[:30]}_{VOICE_ID[:5]}.mp3" 
    local_path = os.path.join(AUDIO_FOLDER, filename)
    # check_credits()

    if not os.path.exists(local_path):
        print(f"Requesting ElevenLabs (Voice: {VOICE_ID})...")
        try:
            # This is the correct v1.x client path
            response = client.text_to_speech.convert(
                voice_id=VOICE_ID,
                text=text,
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
    misty.SaveAudio(
        fileName=filename, 
        data=encoded_audio, 
        immediatelyApply=True, 
        overwriteExisting=True
    )

# misty scans for person
def scan_for_person():
    best_guess = None
    is_new_guess = False

    for yaw_val in SEARCH_POSITIONS:
        print(f"Scanning at angle: {yaw_val}")
        # Move head (Pitch, Roll, Yaw, Velocity)
        # Using PascalCase 'MoveHead' as per your library's likely style
        misty.MoveHead(0, 0, yaw_val, 40) 
        time.sleep(2.0) # Wait for head to finish moving
        
        # Get identification
        name, is_new = identify_person()

        # 1. Check for a specific name. If found, stop scanning and return it
        if name not in ["Unknown", "Error", "None", None]:
            print(f"Target identified: {name}")
            return name, is_new # Found a specific person, we can stop early!
            
        # 2. If we found an unknown name --> definitely a face but we don't know who
        if name == "Unknown":
            print("Saw a face, but not sure who yet. Continuing scan...")
            return "Unknown", True
        
    # After WHOLE loop is done --> saw an Unknown face but no specific person:
    if best_guess == "Unknown":
        return "Unknown", True

    # Only return None after checking ALL angles
    return None, False # finished the sweep and saw absolutely nothing
        
        # # Take two snapshots to be sure
        # name1, is_new1 = identify_person()
        # time.sleep(0.5)
        # name2, is_new2 = identify_person()
        
        # if name1 == name2 and name1 not in ["Unknown", "Error", "None"]:
        #     return name1, is_new1 # Only return if she saw the same person twice
        # elif name1 == "Unknown":
        #     return "Unknown", True
        # return None, False # Finished the sweep, found nobody

# misty: take a picture --> send thru flask to /identify server, which saves to faces_db
def identify_person(): 
    # 1. Ask Misty for a snapshot
    try:
        # We use base64=True so the image data comes directly to our script
        resp = misty.TakePicture(base64=True, width=640, height=480)
        if resp.status_code != 200:
                return None, False
        

        # else if resp.status_code == 200:
        data = resp.json()
        # Handle different potential JSON structures from mistyPy
        img_b64 = data.get("result", {}).get("base64") or data.get("base64")

        #if not in this format
        if not img_b64:
            return None, False
            
        api_resp = requests.post(f"{NGROK_URL}/identify", json={"base64": img_b64})
        result = api_resp.json()

        # Return both the name and the new status
        # result.get("identified_as") might be "Abena", "Unknown", or None
        name = result.get("identified_as")
        is_new = result.get("is_new", False) # set default is_new: False

        return name, is_new
    
    except Exception as e:
        print(f"Identification Error: {e}")
        return "Error", False

# learn person's name --> send request to 
def learn_person(name):
    # Take a fresh photo for the learning process
    resp = misty.TakePicture(base64=True)
    img_b64 = resp.json().get("result", {}).get("base64")
    
    payload = {"name": name, "base64": img_b64}
    
    # Send to the /learn route --> interaction_app.py
    requests.post(f"{NGROK_URL}/learn", json=payload)
    print(f"Success: Misty now knows {name}!")

def misty_search():
    global last_seen_name, last_seen_time # Use global to track across loops
    print("\n[Misty is searching for a friend...]")
    # Pulse LED Blue while searching
    misty.ChangeLED(0, 0, 255) 
    
    # scan_for_person now needs to return (name, is_new)
    # Update scan_for_person to handle the tuple from identify_person
    name, is_new = scan_for_person()
    
    if name is None:
        # print("No one found in this sweep. Resting for 5 seconds...")
        # print("A friend is found, but we don't know their name.")
        print("Sweep complete: No faces detected.")
        return # Restart the search sweep
    

    # ---  MEMORY CHECK ---
    current_time = time.time()
    should_greet = True

    # If seen same person AND less than 60 seconds have passed, ignore them
    if name == last_seen_name and (current_time - last_seen_time) < 120:
        print(f"Skipping greeting: I just spoke to {name} recently.")
        should_greet = False
        return 
    # ------------------------

    # If we reach here, Misty saw a face!
    misty.ChangeLED(0, 255, 0) # Green for 'Detection'
    
    if name == "Unknown":
        speak_smart("I don't believe we've met. What is your name?")
        new_name = input("Type name: ")
        learn_person(new_name)
        speak_smart(f"Got it. Nice to meet you, {new_name}!")
        
    elif name != "Error":
        if is_new:
            # This handles the edge case where they are in known_faces 
            # but maybe not in the SQL database yet
            speak_smart(f"Hello {name}, I am adding you to my memory now.")
        else:
            # THE RECOGNITION GREETING
            speak_smart(f"Hello {name}! It is great to see you again!")

        last_seen_name = name
        last_seen_time = time.time()
        time.sleep(10)

    # [At the very bottom, after the 10s cooldown]
    print("Resetting head for next search...")
    misty.MoveHead(0, 0, 0, 40) 
    time.sleep(2)
    
def main_loop():
    print(f"Connecting to Misty at {MISTY_IP}...")
    
    # Try multiple ways to ping the robot
    connected = False
    for method_name in ["change_led", "changeLED", "ChangeLED"]:
        if hasattr(misty, method_name):
            try:
                # Try to turn her LED Green
                method = getattr(misty, method_name)
                method(0, 255, 0) 
                print(f"Connected using {method_name}!")
                connected = True
                break
            except:
                continue

    if not connected:
        print("Could not verify connection with LED, but we will try the loop anyway...")

    print("Misty is active. Press Ctrl+C to stop.")
    
    while True:
        misty_search()


if __name__ == "__main__":
    main_loop()