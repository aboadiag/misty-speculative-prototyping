# misty_p01.py
## Purpose: some ideas came up with P01
import misty_brain as mb
import time
import random
import requests
from misty_multimodal_processing import play_cached_audio

# -------------------------MISTY BANDIT ----------------
# --- ADD TO TOP OF misty_p01.py ---
from misty_bandit_module import PersonalizationBrain
from bandit_features import UserContextEvaluator
import numpy as np


# --- SETTINGS ---
TESTING_MODE = False  # Set to False when P01 actually arrives
CALIBRATION_SAMPLES = 10  # Increased for better baseline accuracy
SESSION_COOLDOWN = 10     # Seconds to wait before looking for the user again
# ----------------


# 1. Define our Arms (Misty's Recommnedations)
ACTIVITIES = ["Breathing", "Stretching"]

# 2. Define Context Map (Used to translate labels to vectors for the Regressor)
# Vector = [Normalized Stress, Activity Score]
CONTEXT_MAP = { # stress and activity as proxies for depression and anxiety
    "high_stress_low_act":  np.array([0.9, 0.1]), # high stress, low activity
    "low_stress_low_act":   np.array([0.2, 0.1]), # low stress, low activity
    "high_stress_high_act": np.array([0.9, 0.8]), # high stress, high activity
    "low_stress_high_act":  np.array([0.2, 0.8]), # low stress, high activity
    "baseline":             np.array([0.5, 0.2]) # user (default) baseline
}

# 3. Initialize the Brain and Evaluator
brain = PersonalizationBrain(arm_names=ACTIVITIES, context_map=CONTEXT_MAP)
evaluator = UserContextEvaluator(calibration_steps=CALIBRATION_SAMPLES) # Reduced for faster testing

# -------------------------MISTY BANDIT ----------------


# 1. Breathing Activity (~2 minutes)
# In misty_p01.py

def activity_breathing():
    # 1. Play the background music from audio_cache
    # We use the filename you saved from Freesound
    music_file = "calm_sound_1_nature.mp3"
    print(f"Starting intervention music: {music_file}")
   
    # Using your existing upload/play logic
    play_cached_audio(music_file, misty)
    time.sleep(10)
    
    # 2. Misty guides the user while the music plays in the background
    mb.speak_smart("Let's take a moment to breathe. Follow the light on my chest.", misty)
    
    # 3. Animation Loop (matches the music tempo)
    for i in range(3):
        misty.ChangeLED(0, 0, 255) # Blue: Inhale
        misty.MoveHead(-15, 0, 0, 20) 
        time.sleep(5)
        
        misty.ChangeLED(0, 255, 255) # Cyan: Exhale
        misty.MoveHead(10, 0, 0, 20)
        time.sleep(5)

    mb.speak_smart("You're doing great. One last deep breath.", misty)
    time.sleep(6) # DELAY: Wait for the final instruction to finish    

    # 4. Cleanup
    misty.StopAudio() # Ensure music doesn't bleed into the next state
    misty.MoveHead(0, 0, 0, 40)

# 2. Stretching Activity (~3 minutes)
def activity_stretching():
    # 1. Play the background music from audio_cache
    # We use the filename you saved from Freesound
    music_file = "calm_sound_2_waterfall.mp3"
    print(f"Starting intervention music: {music_file}")
    
    # Using your existing upload/play logic
    play_cached_audio(music_file, misty)
    time.sleep(10) # DELAY: Buffer for intro speech

    mb.speak_smart("Time to get moving! Let's do a quick stretch together.", misty)
    time.sleep(5) # DELAY: Buffer for intro speech

    misty.MoveHead(-25, 0, 0, 40) 
    time.sleep(5)
    
    # Physical guidance: Right side
    misty.MoveHead(0, 25, 0, 40) 
    mb.speak_smart("Lean your head to the right and hold it.", misty)
    time.sleep(8) # DELAY: Extra time for the speech + the physical stretch
    
    # Physical guidance: Left side
    misty.MoveHead(0, -25, 0, 40) 
    mb.speak_smart("And now, lean slowly to the left.", misty)
    time.sleep(8) # DELAY: Extra time for the speech + the physical stretch
    
    # Return to neutral
    misty.MoveHead(0, 0, 0, 40)
    mb.speak_smart("Great work. Staying active really helps your energy levels!", misty)
    time.sleep(6) # DELAY: Let her finish the closing thought before the session ends
    
    # Cleanup
    misty.StopAudio()

# Use the Robot instance from your brain
misty = mb.misty
all_jokes = [
        ("Why did the robot go to the doctor?", "Because it had a virus!"),
        ("What is a robot's favorite snack?", "Micro-chips!"),
        ("Why was the robot so tired?", "Because it had a hard drive!")
    ]

random.shuffle(all_jokes) # Scramble the order once at the start

#Purpose: misty tells a joke
def misty_jokes():
    global all_jokes

    if not all_jokes:
        print("Out of jokes! Refilling the list...")
        # Refill if empty
        return

    # setup, punchline = random.choice(all_jokes)
    setup, punchline = all_jokes.pop() # after joke is told, remove from list
    
    # 1. Setup Phase: Show "Joy" eyes
    print("Setting face to: Joy")
    misty.DisplayImage("e_Joy.jpg") 
    mb.speak_smart(setup, misty)
    
    time.sleep(4) # Dramatic pause - keep the Joy face during the wait
    
    # 2. Punchline Phase: Show "Goofy" eyes
    print("Setting face to: Goofy")
    misty.DisplayImage("e_Goofy.jpg")
    mb.speak_smart(punchline, misty)
    
    # 3. Physical comedy: Head tilt
    # Pitch -10 (up), Roll 15 (tilt right), Yaw 0
    misty.MoveHead(-10, 15, 0, 40)
    
    # 4. Hold the pose for a second, then return to normal
    time.sleep(4)
    misty.DisplayImage("e_DefaultContent.jpg") # Or "e_Normal.jpg"
    misty.MoveHead(0, 0, 0, 40)


# Purpose: Misty asks how long person it has been since 
# user has gotten up
def misty_checksin(person_name):
    """Checks Garmin activity state before asking the user for manual input."""
    
    current_activity = "UNKNOWN"
    
    # 1. Fetch current state from your Garmin Flask Server
    try:
        # Assuming your Garmin server is running on port 5001
        response = requests.get("http://localhost:5000/current_state", timeout=1)
        if response.status_code == 200:
            current_activity = response.json().get("activity_type", "UNKNOWN").upper()
    except Exception as e:
        print(f"Note: Garmin server not reached ({e}). Proceeding with manual check.")

    # 2. Contextual Opening based on Garmin Activity
    if current_activity == "STILL":
        mb.speak_smart(f"I've noticed you've been quite still for a while, {person_name}.", misty)
        misty.ChangeLED(0, 0, 255) # Blue for "Sedentary"
    elif current_activity in ["WALKING", "RUNNING"]:
        mb.speak_smart(f"I see you're on the move, {person_name}! I love the energy.", misty)
        misty.ChangeLED(0, 255, 0) # Green for "Active"
    else:
        mb.speak_smart(f"I've been keeping track of the time, {person_name}.", misty)

    # 3. The Core Question
    mb.speak_smart("How long has it been since you last stood up to stretch?", misty)
    
    # 4. Manual Log (Crucial for Co-Design Data)
    human_answer = input(f"Waiting for {person_name}'s response (mins): ") 
    print(f"CO-DESIGN LOG: Garmin said {current_activity}, User said {human_answer} mins.")

    # 5. Logic based on user input
    try:
        mins = int(human_answer)
        if mins > 5:
            mb.speak_smart("That is quite a while! Would you like to do a quick stretch with me?", misty)
            # Physical cue: Misty tilts head invitingly
            misty.MoveHead(0, 20, 0, 40) 
        else:
            mb.speak_smart("Great job staying active. Keep it up!", misty)
    except ValueError:
        mb.speak_smart("I didn't quite catch that number, but let's stay active together!", misty)


def run_personalization_session(identified_name):
    """The core logic for a single interaction session."""
    print(f"\n--- Starting Session for {identified_name} ---")
    mb.mmp.set_current_user(identified_name)
    
    # 1. CALIBRATION (If not already calibrated)
    if not evaluator.state["calibrated"]:
        print(f"Calibrating Garmin baseline ({CALIBRATION_SAMPLES} samples)...")
        while not evaluator.state["calibrated"]:
            try:
                # Use Ngrok or Localhost as per your forwarding setup
                resp = requests.get(f"{mb.mmp.NGROK_URL}/current_state", timeout=2)
                if resp.status_code == 200:
                    evaluator.update_from_garmin(resp.json())
                    print(f"Calibration: {evaluator.readings_count}/{CALIBRATION_SAMPLES}")
            except Exception as e:
                print("Waiting for Garmin data stream...")
            time.sleep(2)

    # 2. DECIDE
    current_context_vector = evaluator.get_context_vector()

    # Get the internal scores for all activities before deciding
    scores = {}
    for i, name in enumerate(ACTIVITIES):
        # This calculates the expected reward for each activity based on the current context
        prediction = brain.agent.arms[i].learner.predict(current_context_vector.reshape(1, -1))
        scores[name] = round(float(prediction[0]), 3)
    
    print(f"\n[BANDIT SCOREBOARD] {scores}")

    arm_idx, activity_choice = brain.get_decision(current_context_vector)
    print(f"Bandit Decision: {activity_choice} (Context: {current_context_vector})")

    # 3. ACT
    if activity_choice == "Breathing":
        activity_breathing()
    elif activity_choice == "Stretching":
        activity_stretching()

    # 4. REWARD CAPTURE
    print("\n[DEBUG] Capturing post-activity physiological response...")
    time.sleep(2) # "breather" for the API

    # ---  Look up if the user was just stretching ---
    if activity_choice == "Stretching":
        print("User likely standing. Tilting head UP to find face...")
        misty.MoveHead(-25, 0, 0, 40) # Pitch -25 looks up
        time.sleep(2) # Give her a second to stabilize
    else:
        # If breathing, user is likely sitting, so look straight
        misty.MoveHead(0, 0, 0, 40)
        time.sleep(1)

    # NEW: Perform a quick vision check to see if they stayed for the whole activity
    print("Checking for user presence...")
    # This calls the vision server one last time to update the PRESENCE_SCORE
    mb.mmp.identify_person(misty, evaluator=evaluator)

    time.sleep(15) # Wait for HR/Stress to settle

    try:
        final_data = requests.get(f"{mb.mmp.NGROK_URL}/current_state").json()
        evaluator.update_from_garmin(final_data)
        
        # Pull latest vision data if your system supports it
        # evaluator.update_from_vision(mb.get_latest_gaze()) 
        
        # --- NEW PRINT LINES FOR DEBUGGING ---
        print(f"  > Current HR: {evaluator.state['current_hr']} (Baseline: {evaluator.state['hr_baseline']:.1f})")
        print(f"  > Current Stress: {evaluator.state['last_valid_stress']} (Baseline: {evaluator.state['stress_baseline']:.1f})")
        print(f"  > Gaze Persistence: {evaluator.state['gaze_persistence']}")
        print(f"  > Activity Type: {final_data.get('activity_type')}")
        # --------------------------------------
        
    except Exception as e:
        print(f"  > Error fetching reward data: {e}")

    reward = evaluator.calculate_reward()
    
    # 5. LEARN
    brain.give_feedback(arm_idx, current_context_vector, reward)
    print(f"Session Result: Reward {reward:.2f}")
    
    if not TESTING_MODE:
        brain.save_model()

if __name__ == "__main__":
    if not TESTING_MODE:
        brain.load_model()

    print("Misty Personalization System Active. Press Ctrl+C to stop.")
    
    try:
        while True:
            # Step 1: Search for a friend
            print("\nScanning for users...")
            identified_name = mb.misty_search() 
            
            if identified_name and identified_name not in ["Unknown", "None"]:
                # NEW: Run 4 activities in a row for this user
                turns_per_session = 4
                print(f"User {identified_name} identified. Starting {turns_per_session}-turn block.")
                
                for turn in range(1, turns_per_session + 1):
                    print(f"\n--- TURN {turn} of {turns_per_session} ---")
                    run_personalization_session(identified_name)
                    
                    if turn < turns_per_session:
                        print("Short buffer before next turn...")
                        time.sleep(10) # 10s pause so activities don't feel like a conveyor belt
                
                # Step 3: Larger Cooldown AFTER the 4 turns are complete
                print(f"Block complete. Cooling down for {SESSION_COOLDOWN}s before next user scan...")
                time.sleep(SESSION_COOLDOWN)
            else:
                print("No one found. Sleeping briefly before next scan...")
                time.sleep(5)
                
    except KeyboardInterrupt:
        print("\nShutting down Misty safely.")
        misty.StopAudio()
        misty.MoveHead(0,0,0,40)