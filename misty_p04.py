# misty_p04.py
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

# Source: https://theallpurposewoman.com/40-positive-affirmations-for-black-women/
all_affirmations = [
    "I am deserving of love, respect, and success in all areas of my life.",
    "I walk in the path of my ancestors, drawing strength from their legacy.",
    "I attract positive opportunities and relationships aligned with my purpose.",
    "I embrace my inner power and use it to create positive change.",
    "I celebrate my unique identity and embrace the beauty of my heritage."
]


# Create a working copy so we can pop items without destroying the master list forever
available_affirmations = all_affirmations.copy()

# purppose: detect heart rate in morning (when anxiety is peaked) --> box breathing, then
#  and then gives you schedule (make sure dogs and cats fed, walked)
# Purpose: Misty asks how long person it has been since 
# user has gotten up
def misty_morning_checkin(person_name):
    """Checks Garmin heart rate, guides breathing, and gives the morning schedule."""
    
    current_breathrate = "UNKNOWN"
    
    # 1. Fetch current state from your Garmin Flask Server
    print("[!] Fetching Garmin Data...")
    try:
        # Replace the URL with your actual local Flask endpoint. 
        # The timeout=3 is crucial so Misty doesn't freeze if the server is down.
        response = requests.get("http://127.0.0.1:5000/get_breath", timeout=3)
        if response.status_code == 200:
            data = response.json()
            current_breathrate = data.get("breath_rate", "UNKNOWN")
    except Exception as e:
        print(f"[!] Garmin fetch failed (Watch disconnected?): {e}")

    # 2. Contextual Opening based on Garmin heart rate
    # Assuming anxiety spikes push HR over ~85-90 bpm while resting
    if isinstance(current_breathrate, (int, float)) and current_breathrate > 15:
        greeting = f"Good morning, {person_name}. I notice your heart rate is currently {current_breathrate}. Mornings can be overwhelming. Let's take a moment to ground ourselves."
    else:
        greeting = f"Good morning, {person_name}. It is a new day. Let's take a moment to get centered before we start."
        
    mb.speak_smart(greeting, misty)
    time.sleep(len(greeting) * 0.08 + 1)

    # 3. The Core activity --> box breathing followed by schedule OR Affirmations followed by schedule
    mb.speak_smart("What do you need right now before starting your day? Guided box breathing, affirmations, or both?", misty)
        
    wizard_decision = input("\n[WOZ] Select 'B' for box breathing  or 'A' affirmations, or 'C' for both : ").strip().lower()
    
    if wizard_decision == "b":
        guided_box_breathing(cycles=3) # Do 3 rounds for the prototype
    elif wizard_decision == "a":
        misty_affirms()

    elif wizard_decision == "c":
       guided_box_breathing(cycles=3) # Do 3 rounds for the prototype
       misty_affirms()
    else:
        print(f"You made a mistake, wizard. Try again")


    schedule_text = "Here is your schedule for this morning. First, please make sure the dogs and cats are fed, and the dogs get their walk. You've got this."
    mb.speak_smart(schedule_text, misty)
    time.sleep(len(schedule_text) * 0.08 + 1)

    # 4. Log (Crucial for Co-Design Data)
    log_filename = f"transcripts/P04_morning_logs.txt"
    os.makedirs('transcripts', exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_filename, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] Morning Check-in triggered.\n")
        f.write(f"[{timestamp}] Garmin HR Readout: {current_breathrate}\n")
        f.write("-" * 30 + "\n")
   

#box breathing function
def guided_box_breathing(cycles=3):
    # box breathing script:
    # Prepare: Sit upright in a comfortable chair and place your feet flat on the floor, relaxing your shoulders.
    # Exhale: Gently exhale all the air from your lungs.
    # Inhale (4 seconds): Inhale slowly and deeply through your nose for a slow count of four.
    # Hold (4 seconds): Hold your breath for a count of four.
    # Exhale (4 seconds): Exhale through your mouth or nose for a count of four.
    # Hold (4 seconds): Hold your breath again (lungs empty) for a count of four.
    # Repeat: Repeat this cycle for 5 minutes, or until you fee
    """Guides user through a 4-4-4-4 breathing exercise with LED visual anchors."""
    
    prep_text = "Sit upright in a comfortable chair. Place your feet flat on the floor, and relax your shoulders. Gently exhale all the air from your lungs."
    mb.speak_smart(prep_text, misty)
    time.sleep(len(prep_text) * 0.08 + 2)

    for i in range(cycles):
        print(f"Breathing Cycle {i+1}/{cycles}")
        
        # Inhale (Blue)
        misty.ChangeLED(0, 100, 255) 
        mb.speak_smart("Inhale slowly through your nose. Two. Three. Four.", misty)
        misty.MoveArms(-88, -88, 50, 50) #up
        time.sleep(4)
        
        # Hold (Green)
        misty.ChangeLED(0, 255, 0)
        mb.speak_smart("Hold. Two. Three. Four.", misty)
        time.sleep(4)
        
        # Exhale (Orange)
        misty.ChangeLED(255, 100, 0)
        mb.speak_smart("Exhale gently. Two. Three. Four.", misty)
        misty.MoveArms(88, 88, 50, 50) #down
        time.sleep(4)
        
        # Hold Empty (Dim White)
        misty.ChangeLED(50, 50, 50)
        mb.speak_smart("Hold empty. Two. Three. Four.", misty)
        time.sleep(4)

    # Reset LED and finish
    misty.ChangeLED(0, 255, 0)
    mb.speak_smart("Great job.", misty)
    time.sleep(2)

# affirmation function
def misty_affirms():
    #randomly select from list of affirmations, and remind: "you are safe"

    #asks for user input if user wants another affirmation
    #misty asks: do you want another affirmation?
    #wizard: Y/N --> select another one (pop the other one out so never get same one again)
    """Provides a random affirmation, ensures no repeats, and asks WOZ to continue."""
    global available_affirmations
    
    count = 0

    while True:
        # Check if we ran out of affirmations
        if not available_affirmations:
            msg = "We have gone through all of our affirmations for today. Remember, you are powerful and you are safe."
            mb.speak_smart(msg, misty)
            time.sleep(len(msg) * 0.08)
            print("[!] Affirmation list is empty.")
            break

        # Randomly select and pop out of the list so it never repeats
        random_index = random.randint(0, len(available_affirmations) - 1)
        selected_affirmation = available_affirmations.pop(random_index)

        # Speak
        if count == 0:
            affirmation_speech = f"You are safe. Here is an affirmation: {selected_affirmation}"
            print(f"[Affirmation]: {affirmation_speech}")
        else:
            affirmation_speech = f"Here is another affirmation: {selected_affirmation}"
            
        misty.ChangeLED(255, 0, 255) # Purple for affirmations
        mb.speak_smart(affirmation_speech, misty)
        time.sleep(len(affirmation_speech) * 0.08 + 1)
        misty.ChangeLED(0, 255, 0) # Back to Green

        count=count+1

        print(f"count is: {count}")
        # Wizard Prompt
        mb.speak_smart("Would you like to hear another one?", misty)
        
        wizard_decision = input("\n[WOZ] Give another affirmation? (Y/N): ").strip().lower()
        
        if wizard_decision != 'y':
            depart_words = "Okay. I am here if you need me."
            mb.speak_smart(depart_words, misty)
            time.sleep(len(depart_words) * 0.08 + 1)

            break


if __name__ == "__main__":
    print("Misty is looking for P04...")
    identified_name = mb.misty_search() 
    misty.MoveHead(0, 0, 0, 40) # move head 


    try:
        misty_morning_checkin(identified_name)


    except KeyboardInterrupt:
        print("\n[!] Session interrupted by researcher. Saving logs...")
    except Exception as e:
        print(f"\n[!] Unexpected error: {e}")
    finally:
        # This block runs NO MATTER WHAT (even on Ctrl+C)
        print(f"Finalizing transcript for {identified_name}...")
        # You could add a 'Session Ended Abruptly' note here if you want
        print(f"Demo complete.")

