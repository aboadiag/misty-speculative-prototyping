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
SERVER_URL = "https://975e-128-237-82-210.ngrok-free.app"
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
            response = requests.get(f"{SERVER_URL}/get_situation", timeout=3)
            
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
                requests.post(f"{SERVER_URL}/send_watch_alert", json={"message": alert_text})
                
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
                    requests.post(f"{SERVER_URL}/send_watch_alert", json={"message": alert_text})
                    
                    # --- ACTION 2: ROBOT VISUAL CUES ---
                    misty.DisplayImage("e_DefaultContent.jpg") 
                    
                    # Let the user read the positive message for 5 seconds
                    time.sleep(5)
                    
                    # --- ACTION 3: RESET WATCH TO NORMAL ---
                    requests.post(f"{SERVER_URL}/send_watch_alert", json={"message": ""})
                    
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

if __name__ == "__main__":

     # 1. Start by finding the person
    print("Misty is looking for P02...")
    identified_name = mb.misty_search() 
    misty.MoveHead(0, 0, 0, 40) # reset her head
    
    if identified_name:
        # Move head back to center for engagement
        mb.set_current_user(identified_name)
        misty.MoveHead(0, 0, 0, 40)
        time.sleep(2)

        try:
            discrete_misty()
        except KeyboardInterrupt:
            misty.MoveHead(0, 0, 0, 40) # reset her head
            print("\n[!] Exiting mistyStateDetection P05.")