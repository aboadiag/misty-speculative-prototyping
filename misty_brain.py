# misty_brain.py
# misty behavioral (speech, movement, etc) module
from mistyPy.Robot import Robot
import base64
import requests
import time
from elevenlabs.client import ElevenLabs
import os
from dotenv import load_dotenv
import re
import misty_vision_processing as misty_vp
from misty_vision_processing import scan_for_person, learn_person, speak_smart, user_calibration, set_current_user

# 1. Try to load the file
load_status = load_dotenv()
print(f"Did .env load successfully? {load_status}")

## IP addresses
MISTY_IP = os.getenv("ROBOT_URL")
def check_envs():
    """Validates that secrets are loaded and returns a Misty object."""
    if not MISTY_IP:
        print("CRITICAL: MISTY_IP (ROBOT_URL) missing from .env")
        return None
    
    try:
        return Robot(MISTY_IP)
    except Exception as e:
        print(f"Failed to initialize Misty: {e}")
        return None


# Global initializations
misty = check_envs() #define robot --> misty = Robot(MISTY_IP)

print(f"MISTY_IP value: {MISTY_IP}")


#last times seen
last_seen_name = None #indicates the name last seen
last_seen_time = 0 # and time last seen 
    

# Purpose: Misty looks for person
# if finds someone, checks if name is in DB. If not, either "unknown" or "error"
#Returns: Name
def misty_search():
    global last_seen_name, last_seen_time # Use global to track across loops
    print("\n[Misty is searching for a friend...]")

    # Pulse LED Blue while searching
    misty.ChangeLED(0, 0, 255) 
    
    # scan_for_person now needs to return (name, is_new)
    # Update scan_for_person to handle the tuple from identify_person
    name, is_new = scan_for_person(misty)
    
    if name is None:
        print("Sweep complete: No faces detected.")
        return None # Return None if no one is there 

    # ---  MEMORY CHECK ---
    current_time = time.time()
    time_since_last = current_time - last_seen_time
    # should_greet = True
    # ------------------------

    # 1. If seen same person AND less than 60 seconds have passed, ignore them
    if name == last_seen_name and (current_time - last_seen_time) < 120:
        print(f"Skipping greeting: I just spoke to {name} recently.")
        should_greet = False
        return None
    
    # 2. If it's "Unknown" but we JUST met someone, assume it's a bad frame of that person
    if name == "Unknown" and time_since_last < 60:
        print("Saw an unknown face, but I just spoke to someone. Skipping to avoid loops.")
        return None
    
     # If we reach here, Misty saw a face!
    misty.ChangeLED(0, 255, 0) # Green for 'Detection'
    
    # We'll store the name here so we can return it AFTER the cleanup
    found_name = None

    if name == "Unknown":
        # speak_smart("I don't believe we've met. What is your name?", misty)
        # learn_person(new_name, misty)
        new_user = misty_vp.user_calibration(misty)
        found_name = new_user.lower()

        # last_seen_name = new_user.lower()
        # last_seen_time = time.time()        
    elif name != "Error":
        # Strip suffix like _1 or _2 immediately
        clean_name = name.split('_')[0]

        # This handles the edge case where they are in known_faces 
        # but maybe not in the SQL database yet
        if is_new:
            speak_smart(f"Hello {clean_name}, I am adding you to my memory now.", misty)
        else:
            # THE RECOGNITION GREETING
            speak_smart(f"Hello {clean_name}! It is great to see you again!", misty)
        found_name = clean_name.lower()

    # Update global tracking
    if found_name:
        last_seen_name = found_name.lower()
        last_seen_time = time.time()

        # --- UNIVERSAL COOLDOWN (Now this will actually run!) ---
        print("Interaction complete. Cooling down for 10 seconds...")
        time.sleep(10)

        print("Resetting head for next search...")
        misty.MoveHead(0, 0, 0, 40) 
        time.sleep(2)

    return found_name # Hand off the name 

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
    # main_loop()
    name = user_calibration(misty)
    print(f"Robot just met {name}")