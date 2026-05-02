# misty_brain.py
# misty behavioral (speech, movement, etc) module
# this import to the interaction_server extends the bridge (mmp)
from mistyPy.Robot import Robot
import base64
import requests
import time
from elevenlabs.client import ElevenLabs
import os
from dotenv import load_dotenv
import re
import misty_multimodal_processing as mmp
from misty_multimodal_processing import scan_for_person, learn_person, speak_smart, user_calibration, set_current_user
from bandit_features import UserContextEvaluator
import msvcrt 

# 1. Try to load the file
load_status = load_dotenv()
print(f"Did .env load successfully? {load_status}")

# BANDIT ---
evaluator = UserContextEvaluator()

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

# Global state for the touch interaction
is_touched = False
trigger_source = ""

#last times seen
last_seen_name = None #indicates the name last seen
last_seen_time = 0 # and time last seen 

def physical_interaction_callback(data):
    """
    Handles both TouchSensor and BumpSensor data objects.
    Ref: https://docs.mistyrobotics.com/misty-ii/reference/sensor-data/#bumpsensor
    """
    global is_touched, trigger_source
    
    message = data.get("message", {})
    
    # Check if this is a TOUCH (Head/Chin/Scruff)
    # Ref: isContacted is True for TouchSensors
    if message.get("isContacted") == True:
        trigger_source = message.get("sensorPosition") # e.g., "FrontHead"
        is_touched = True

    # Check if this is a BUMP (Feet)
    # Ref: isContacted is ALSO True for BumpSensors
    elif message.get("isPressed") == True:
        trigger_source = message.get("sensorName") # e.g., "Bump_FrontRight"
        is_touched = True


# purpose: using Misty's on-body sensors to trigger the interaction
# return: misty_search
def misty_feels():
    # global is_touched, trigger_source
    # is_touched = False 
    # trigger_source = ""

    print("\n[Misty is waiting for a touch to wake up...]")
    misty.ChangeLED(255, 165, 0) # Orange

    # # 1. Register for Head/Chin Touches
    # misty.RegisterEvent("TouchEvents", "TouchSensor", 50, True, physical_interaction_callback)
    
    # # 2. Register for Foot Bumps
    # # Note: The Sensor Type string is "BumpSensor"
    # misty.RegisterEvent("BumpEvents", "BumpSensor", 50, True, physical_interaction_callback)

    # # Block execution until the callback sets is_touched to True
    # while not is_touched:
    #     time.sleep(0.1)

    # # Immediately stop listening to prevent multiple triggers
    # misty.UnregisterEvent("TouchEvents")
    # misty.UnregisterEvent("BumpEvents")

    # Manual Trigger: The script will pause here until YOU press Enter
    input(">>> ACTION: Press ENTER when participant touches Misty to start...")

    # Feedback: Cyan LED and success sound
    misty.ChangeLED(0, 255, 255) 
    misty.PlayAudio("s_SystemSuccess.wav", 100)
    print(f">>> INTERACTION TRIGGERED BY: {trigger_source}")
    
    # Physical response: Look up at the person
    # misty.MoveHead(-20, 0, 0, 40) 

    # Proceed to the vision-based search
    return misty_search()
    

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
    name, is_new = scan_for_person(misty, evaluator)
    
    if name is None:
        print("Sweep complete: No faces detected.")
        return None # Return None if no one is there 

    # --- THE RESEARCHER OVERRIDE BLOCK ---
    # We catch the name BEFORE Misty speaks it.
    print(f"\n>>> VISION DETECTED: {name}")
    print(">>> [RECOGNITION PAUSE] Press 'c' to CORRECT, or wait 5s to proceed...")
    
    start_wait = time.time()
    while time.time() - start_wait < 5: # 5second window
        if msvcrt.kbhit():
            key = msvcrt.getch().decode('utf-8').lower()
            if key == 'c':
                name = input("Enter corrected name for this participant: ").strip()
                print(f"Name corrected to: {name}")
                break
        
    # -------------------------------------

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
        new_user = user_calibration(misty)
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
            # ---------- THE RECOGNITION GREETING ---------
            speak_smart(f"Hello {clean_name}! It is great to see you again!", misty)
        found_name = clean_name.lower()

    # Update global tracking
    if found_name:
        last_seen_name = found_name.lower()
        last_seen_time = time.time()

        # --- UNIVERSAL COOLDOWN (Now this will actually run!) ---
        print("Interaction complete. Cooling down for 2 seconds...")
        time.sleep(2)

        print("Resetting head for next search...")
        misty.MoveHead(0, 0, 0, 40) 
        time.sleep(2)

    return found_name # Hand off the name 

def mass_delete_chunks():
    print("--- STARTING TARGETED CLEANUP ---")
    
    # List of prefixes you actually have on your robot
    prefixes = ["chunk_abena_", "reflection_abena_", "River_abena_", "hw_test"]
    
    # This is a bit of a "brute force" way since we don't have a 
    # list-and-delete function easily ready, but it targets the right names.
    for i in range(500):
        for prefix in prefixes:
            # Try deleting as a .wav
            misty.DeleteAudio(f"{prefix}{i}.wav")
            # Try deleting as a .mp3 (for the River files)
            misty.DeleteAudio(f"{prefix}{i}.mp3")
            
        if i % 100 == 0:
            print(f"Cleaning... iteration {i}")

    # Special case for those timestamped ones and the hardware test
    misty.DeleteAudio("hw_test.wav")
    
    print("Cleanup complete. REBOOT MISTY NOW to clear the cache.")

def clean_sweep():
    print("--- STARTING TOTAL SYSTEM PURGE ---")
    
    # 1. Get the actual list of files currently on the robot
    response = misty.GetAudioList()
    
    if response.status_code == 200:
        audio_files = response.json().get("result", [])
        print(f"Found {len(audio_files)} total files.")
        
        deleted_count = 0
        for file in audio_files:
            file_name = file.get("name")
            
            # 2. SAFETY CHECK: Do not delete system assets (names starting with 's_')
            # or files required for Misty to function.
            if file.get("systemAsset") == True or file_name.startswith("s_"):
                continue
            
            # 3. Delete the user-generated file
            print(f"Deleting: {file_name}")
            misty.DeleteAudio(file_name)
            deleted_count += 1
            
            # Tiny sleep to prevent overwhelming the REST API
            time.sleep(0.1)
            
        print(f"--- PURGE COMPLETE: {deleted_count} files removed ---")
        print("ACTION REQUIRED: Please reboot Misty now to refresh her memory.")
    else:
        print("Failed to retrieve audio list. Check connection.")

def hardware_mic_test():
    print("[!] TESTING HARDWARE MICS...")
    misty.ChangeLED(255, 0, 0) # Red for "Test Starting"
    
    # Force volume up
    misty.SetDefaultVolume(100)
    
    # Record 5 seconds to a fresh file
    print("Recording... Speak loudly now!")
    misty.ChangeLED(0, 255, 0) # Green
    misty.StartRecordingAudio("hw_test.wav")
    time.sleep(5)
    misty.StopRecordingAudio()
    
    print("Finalizing file...")
    misty.ChangeLED(0, 0, 255) # Blue
    time.sleep(2)
    
    print("Playing back on Misty's speakers...")
    # If the mic works, you WILL hear your own voice now
    misty.PlayAudio("hw_test.wav", 100)
    
    # Keep script alive during playback
    time.sleep(6)
    print("Test complete.")

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
    name = misty_search()
    # name = user_calibration(misty)
    print(f"Robot just met {name}")