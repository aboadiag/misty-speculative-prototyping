# misty_p05.py
## Purpose: some ideas came up with P05
import misty_brain as mb
import time
import random
import requests
import json
import os
import re
import threading  # ✅ NEW: Add threading to prevent blocking
#imports for misty_gemini
from openai import OpenAI  # NEW: Replace genai with OpenAI
from datetime import datetime
from dotenv import load_dotenv


load_dotenv() # Add this - it loads the variables from .env into your system

#start misty robot instance
misty = mb.misty
# SERVER_URL = "https://f28c-128-237-82-123.ngrok-free.app"
SERVER_URL = "http://127.0.0.1:5000"


 # --- SET THE USER'S CONTEXT HERE ---
ENVIRONMENT = "public" # Change to "private" when they are at home with the robot

NGROK_HEADERS = {"ngrok-skip-browser-warning": "true"}

# "http://127.0.0.1:5000"

# discrete misty with additional context awareness --> vision and smartwatch to infer emotional state and direct interventions
# if participant is socially anxious, instead of verbally communicating through the robot, just change robots face to look concerned 
# and have the garmin vibrate and then have the text response "I notice you're anxious, slow down and take a breath"
#while participant is breathing, have the robot move its head up and down and pulse its lights
def run_silent_breathing_guidance(cycles):
    """Guides user via head tilt and LED pulses."""
    for _ in range(cycles):
        misty.ChangeLED(0, 0, 255) # Blue Inhale
        misty.MoveHead(-25, 0, 0, 40) 
        time.sleep(4)
        
        misty.ChangeLED(255, 100, 0) # Orange Exhale
        misty.MoveHead(20, 0, 0, 40)
        time.sleep(4)


#box breathing function --> session 3
def guided_box_breathing(cycles=3, environment="public"):
    """Guides user through a 4-4-4-4 breathing exercise on the physical robot."""
    print(f"[Misty] Starting Box Breathing ({environment.upper()} mode)...")
    
    prep_text = "Sit upright. Place your feet flat on the floor, and relax your shoulders. Exhale all air."
    
    requests.post(f"{SERVER_URL}/send_watch_alert", json={"message": prep_text})
    if environment == "private":
        mb.speak_smart(prep_text, misty)
        time.sleep(len(prep_text) * 0.08 + 2)
    else:
        time.sleep(6)

    for i in range(cycles):
        print(f"Breathing Cycle {i+1}/{cycles}")
        
        # --- INHALE ---
        requests.post(f"{SERVER_URL}/send_watch_alert", json={"message": "Inhale slowly through your nose. 2... 3... 4..."})
        if environment == "private":
            misty.ChangeLED(0, 100, 255) # Blue
            misty.MoveArms(-88, -88, 50, 50) # Arms up
            mb.speak_smart("Inhale slowly through your nose. Two. Three. Four.", misty)
        time.sleep(4)
        
        # --- HOLD ---
        requests.post(f"{SERVER_URL}/send_watch_alert", json={"message": "Hold. 2... 3... 4..."})
        if environment == "private":
            misty.ChangeLED(0, 255, 0) # Green
            mb.speak_smart("Hold. Two. Three. Four.", misty)
        time.sleep(4)
        
        # --- EXHALE ---
        requests.post(f"{SERVER_URL}/send_watch_alert", json={"message": "Exhale gently. 2... 3... 4..."})
        if environment == "private":
            misty.ChangeLED(255, 100, 0) # Orange
            misty.MoveArms(88, 88, 50, 50) # Arms down
            mb.speak_smart("Exhale gently. Two. Three. Four.", misty)
        time.sleep(4)
        
        # --- HOLD EMPTY ---
        requests.post(f"{SERVER_URL}/send_watch_alert", json={"message": "Hold empty. 2... 3... 4..."})
        if environment == "private":
            misty.ChangeLED(50, 50, 50) # Dim White
            mb.speak_smart("Hold empty. Two. Three. Four.", misty)
        time.sleep(4)

    # --- FINISH ---
    requests.post(f"{SERVER_URL}/send_watch_alert", json={"message": "Great job. Returning to normal."})
    if environment == "private":
        misty.ChangeLED(0, 255, 0)
        misty.MoveArms(0, 0, 40, 40) # Reset arms
        mb.speak_smart("Great job.", misty)
    
    time.sleep(4)

# purpose: behavioral helper
# decision making for misty to do guided breathing and also observe user for changes in context/state (anxious vs not)
def discrete_misty():
    # # leverages misty_multimodal_processing from mb to leverage vision (emotion recognition) from deepface
    # # and physiological signals from garmin watch
    """Context-aware intervention: Silent Robot + Watch Text."""
    print("[!] mistyStateDetection P05 Loop Active...")
    
    # Ensure Misty starts in a neutral/happy physical state
    misty.DisplayImage("e_DefaultContent.jpg") 
    misty.MoveHead(0, 0, 0, 40)
    
    was_anxious = False 
    baseline_br = None  # <-- NEW: Track the user's baseline
    
    while True:
        try:
            # 1. Fetch current situation from the server
            response = requests.get(f"{SERVER_URL}/get_situation", headers=NGROK_HEADERS, timeout=3)
            
            data = response.json()
            
            br = data.get("breath_rate", 15)
            emotion = data.get("current_emotion", "neutral")

            # --- NEW: Set baseline on the first successful read ---
            if baseline_br is None:
                print(f"[P05] Calibrating... Baseline breath rate locked at: {br}")
                baseline_br = br
                time.sleep(2)
                continue  # Skip the rest of the loop and start monitoring
            
            # Calculate the delta
            delta = br - baseline_br

            # 2. Decision Logic (Delta >= +2 OR anxious facial expression)
            if delta >= 2 or emotion in ["sad", "fear", "angry"]:
                print(f"[P05] Anxiety detected (BR: {br}, Baseline: {baseline_br}, Delta: +{delta}). Triggering intervention...")
                
                was_anxious = True
                
                # --- ACTION 1: DISCRETE TEXT TO WATCH ---
                alert_text = "I notice you're anxious. Slow down and take a breath."
                requests.post(f"{SERVER_URL}/send_watch_alert", json={"message": alert_text}, headers=NGROK_HEADERS)
                
                # --- ACTION 2: ROBOT VISUAL CUES ---
                misty.DisplayImage("e_Apprehensive.jpg") 
                run_silent_breathing_guidance(cycles=5)
                misty.MoveHead(0, 0, 0, 40) # reset her head


            else:
                # Did they just finish an intervention and return to their baseline?
                # (If they gained 2 to trigger anxiety, returning to delta <= 0 means they successfully decreased by 2)
                if was_anxious and delta <= 0:
                    print(f"[P05] State improved! (BR: {br}, Delta: {delta}). Sending positive reinforcement...")
                    
                    # --- ACTION 1: REWARD TEXT TO WATCH ---
                    alert_text = "Good job on taking it slowly! Keep it up!"
                    requests.post(f"{SERVER_URL}/send_watch_alert", json={"message": alert_text}, headers=NGROK_HEADERS)
                    
                    # --- ACTION 2: ROBOT VISUAL CUES ---
                    misty.DisplayImage("e_DefaultContent.jpg") 
                    
                    # Let the user read the positive message for 5 seconds
                    time.sleep(5)
                    
                    # --- ACTION 3: RESET WATCH TO NORMAL ---
                    requests.post(f"{SERVER_URL}/send_watch_alert", json={"message": ""}, headers=NGROK_HEADERS)
                    
                    # Reset our tracker
                    was_anxious = False
                    
                elif not was_anxious:
                    # User is perfectly fine, just silently monitor.
                    print(f"[P05] User is calm (BR: {br}, Delta: {delta}). Monitoring...")
                else:
                    # They are recovering (e.g., Delta is +1), wait for them to fully reach baseline
                    print(f"[P05] User recovering (BR: {br}, Delta: {delta}). Waiting for return to baseline...")

        except Exception as e:
            print(f"[!] Server Polling Error: {e}")

        # Wait 2 seconds before checking the server again
        time.sleep(2)


# ✅ NEW HELPER: Non-blocking wait for animation to finish
def wait_for_animation_complete(duration=48):
    """Wait for animation to complete WITHOUT blocking Flask server"""
    print(f"[P05] Animation running for {duration} seconds (non-blocking)...")
    time.sleep(duration)
    print("[P05] Animation complete. Resetting...")
    
    # Reset the watch and server state
    requests.post(f"{SERVER_URL}/send_watch_alert", 
        json={"message": ""}, 
        headers=NGROK_HEADERS)
    requests.post(f"{SERVER_URL}/user_choice", 
        json={"choice": "none"}, 
        headers=NGROK_HEADERS)


#purpose: function that decides where misty is embodied:
# on the watch or on the robot
def misty_embodiment():
    global ENVIRONMENT
    print(f"[!] Misty Embodiment Active | Mode: {ENVIRONMENT.upper()}")
    
    misty.DisplayImage("e_DefaultContent.jpg") 
    misty.MoveHead(0, 0, 0, 40)
    
    baseline_br = None
    was_anxious = False
    alert_active_until = 0  # Prevents the watch menu from flickering!
    
    while True:
        try:
            # We just check the get situation to see what the user chose locally on their wrist.
            response = requests.get(f"{SERVER_URL}/get_situation", headers=NGROK_HEADERS, timeout=3)
            data = response.json()
            choice = data.get("user_choice", "none") 
            br = data.get("breath_rate", 15)

            # --- NEW: Set baseline on the first successful read ---
            if baseline_br is None:
                print(f"[P05] Calibrating... Baseline breath rate locked at: {br}")
                baseline_br = br
                time.sleep(2)
                continue  # Skip the rest of the loop and start monitoring
            
            # Calculate the delta
            delta = br - baseline_br
            current_time = time.time()

            # =================================================================
            # STEP 1: TRIGGER THE WATCH MENU (Only if no choice has been made)
            # =================================================================
            if delta >= 2 and choice == "none":
                # 🚨 FIX: Only send the POST request ONCE to stop the spam loop
                if not was_anxious: 
                    print(f"[P05] Anxiety Spike! Unlocking watch menu...")
                    requests.post(f"{SERVER_URL}/send_watch_alert", json={"message": "Anxious? Press Start for options."}, headers=NGROK_HEADERS)
                
                was_anxious = True
                alert_active_until = current_time + 15 # Keep pushing the 15-second timer back as long as BR is high
                
            
            elif was_anxious and delta <= 0:
                    print(f"[P05] State improved! (BR: {br}, Delta: {delta}). Sending positive reinforcement...")
                
                    was_anxious = False # Unlock the system
                    
                    # Send the reward text
                    alert_text = "Good job on taking it slowly! Keep it up!"
                    requests.post(f"{SERVER_URL}/send_watch_alert", json={"message": alert_text}, headers=NGROK_HEADERS)
                    
                    # Let them read it for 5 seconds, then clear the watch screen
                    time.sleep(5)
                    requests.post(f"{SERVER_URL}/send_watch_alert", json={"message": ""}, headers=NGROK_HEADERS)
                    
                    # Recalibrate so they have a fresh baseline
                    baseline_br = None

            # Clear the alert ONLY if they calm down on their own AND the 15-second timer passed
            # elif was_anxious and delta < 1 and current_time > alert_active_until and choice == "none":
            #     print("[P05] User naturally returned to baseline. Clearing menu lock.")
            #     was_anxious = False
            #     requests.post(f"{SERVER_URL}/send_watch_alert", json={"message": ""}, headers=NGROK_HEADERS)


            # =================================================================
            # STEP 2: EMBODIMENT LOGIC (Executes once user picks an option)
            # =================================================================
            if choice != "none":
                print(f"[P05] Watch reported user is performing: {choice}")
                was_anxious = False # Reset state since we are handling it

                # --- IF PRIVATE: Misty physically embodies the intervention ---
                if ENVIRONMENT == "private":
                    mb.speak_smart("Follow along with physical Misty!", misty)

                    if choice == "breathe":
                        guided_box_breathing(cycles=3, environment="private")
                    elif choice == "walk":
                        mb.speak_smart("A walk sounds like a great idea. I'll watch the house while you're gone.", misty)
                        misty.DisplayImage("e_Joy.jpg")
                        time.sleep(5)
                    elif choice == "imagery":
                        mb.speak_smart("Close your eyes. I'll play some calm colors for you.", misty)
                        misty.DisplayImage("e_Sleeping.jpg")
                        misty.ChangeLED(0, 0, 50)
                        time.sleep(10)

                # --- IF PUBLIC: Misty stays discrete ---
                else:
                    follow_text = "Follow along with virtual Misty on your watch!"
                    requests.post(f"{SERVER_URL}/send_watch_alert", json={"message": follow_text}, headers=NGROK_HEADERS)
                    misty.DisplayImage("e_Surprised.jpg")
                    print("[P05] Public mode: Staying quiet while watch handles UI.")
                    time.sleep(10) # Wait a bit so the robot holds the supportive expression

                # --- CLEANUP ---
                print("[P05] Intervention complete. Resetting states...")
                requests.post(f"{SERVER_URL}/user_choice", json={"choice": "none"}, headers=NGROK_HEADERS)
                requests.post(f"{SERVER_URL}/send_watch_alert", json={"message": "reset"}, headers=NGROK_HEADERS)
                
                misty.DisplayImage("e_DefaultContent.jpg")
                misty.ChangeLED(0, 255, 0)
                
                # Re-calibrate baseline after an intervention so they start fresh
                baseline_br = None 

        except Exception as e:
            print(f"[!] Monitoring Error: {e}")

        time.sleep(2)

def set_user_mode(mode="private"):
    global ENVIRONMENT # Tells Python to use the top-level variable
    
    if mode == "private":
        ENVIRONMENT = "private" # Single equals sign to assign!
    elif mode == "public":
        ENVIRONMENT = "public"


if __name__ == "__main__":

     # 1. Start by finding the person
    # print("Misty is looking for P05...")
    # identified_name = mb.misty_search() 
    # misty.MoveHead(0, 0, 0, 40) # reset her head
    
    # if identified_name:
    #     # Move head back to center for engagement
    #     mb.set_current_user(identified_name)
    print("Misty is ready to interact with P05...")
    misty.MoveHead(0, 0, 0, 40)
    time.sleep(2)

    #SET USER MODE
    set_user_mode("private")
    print(f"Current user mode is set to {ENVIRONMENT}")

    try:
        #session 3
        misty_embodiment()
        #session 2
        # discrete_misty()
    except KeyboardInterrupt:
        misty.MoveHead(0, 0, 0, 40) # reset her head
        print("\n[!] Exiting mistyStateDetection P05.")