# misty_p01.py
## Purpose: some ideas came up with P01
import misty_brain as mb
import time
import random
import requests

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

if __name__ == "__main__":
    # 1. Start by finding the person
    print("Misty is looking for P01...")
    identified_name = mb.misty_search() 
    misty.MoveHead(0, 0, 0, 40) # move her head back before joke delivery
    
    if identified_name:
        # 2. Run the new modules
        # misty_jokes()
        # time.sleep(3)
        misty_checksin(identified_name)
        time.sleep(3)
    else:
        print("No one found to joke with.")
