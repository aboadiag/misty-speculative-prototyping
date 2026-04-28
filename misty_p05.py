# misty_p05.py
## Purpose: some ideas came up with P04
import misty_brain as mb
import time
import random
import requests
import json
import os
import re
#imports for misty_gemini
from openai import OpenAI  # NEW: Replace genai with OpenAI
from datetime import datetime
from dotenv import load_dotenv


load_dotenv() # Add this - it loads the variables from .env into your system

#start misty robot instance
misty = mb.misty
SERVER_URL = "http://127.0.0.1:5000"

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
    
    while True:
        try:
            # 1. Fetch current situation from the server
            response = requests.get(f"{SERVER_URL}/get_situation", timeout=3)
            data = response.json()
            
            br = data.get("breath_rate", 15)
            emotion = data.get("current_emotion", "neutral")

            # 2. Decision Logic (High breathing rate OR anxious facial expression)
            if br > 22 or emotion in ["sad", "fear", "angry"]:
                print(f"[P05] Anxiety detected (BR: {br}, Emotion: {emotion}). Triggering intervention...")
                
                # --- ACTION 1: DISCRETE TEXT TO WATCH ---
                alert_text = "I notice you're anxious. Slow down and take a breath."
                requests.post(f"{SERVER_URL}/send_watch_alert", json={"message": alert_text})
                
                # --- ACTION 2: ROBOT VISUAL CUES ---
                misty.DisplayImage("e_Apprehensive.jpg") 
                run_silent_breathing_guidance(cycles=5)
                
                # --- ACTION 3: RESET ---
                requests.post(f"{SERVER_URL}/send_watch_alert", json={"message": ""})
                misty.DisplayImage("e_DefaultContent.jpg")
                
                # Cooldown so we don't spam the user immediately after breathing
                print("[P05] Intervention complete. Cooling down for 10 seconds.")
                time.sleep(10)

        except Exception as e:
            print(f"[!] Server Polling Error: {e}")

        # Wait 2 seconds before checking the server again
        time.sleep(2)


if __name__ == "__main__":
    try:
        discrete_misty()
    except KeyboardInterrupt:
        print("\n[!] Exiting mistyStateDetection P05.")