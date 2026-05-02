# misty_p02.py
## Purpose: some ideas came up with P02
import misty_brain as mb
import time
import random
import requests
import json
import os
import re
#imports for misty_gemini
from openai import OpenAI  # NEW: Replace genai with OpenAI
import speech_recognition as sr
from datetime import datetime
from dotenv import load_dotenv


load_dotenv() # Add this - it loads the variables from .env into your system

# Robot instance from misty brain
misty = mb.misty

# configure api key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_user_data(name):
    """Helper to load local JSON data for a specific user."""
    try:
        with open('misty_p02_goals.json', 'r') as f:
            data = json.load(f)
        
        # 1. Clean the name (remove underscores/numbers and make lowercase)
        # "Abena_1" -> "abena"
        clean_name = re.sub(r'_\d+', '', name).lower().strip()
        
        print(f"DEBUG: Looking for JSON key: '{clean_name}'") # Tells you what it's searching for
        
        if clean_name in data:
            print(f"DEBUG: Success! Found data for {clean_name}")
            return data[clean_name]
        else:
            print(f"DEBUG: '{clean_name}' NOT in JSON keys: {list(data.keys())}. Using guest.")
            return data.get("guest", {})
        
    except FileNotFoundError:
        print("Error: misty_goals.json not found.")
        return {}

# Purpose: Provide literary recommendations.
def misty_literary_recommendations(name):
    user_data = load_user_data(name)
    book = user_data.get('recommendation', "The Design of Everyday Things")
    
    text = f"By the way, I remember you're interested in learning more. I highly recommend checking out the book, {book}."
    mb.speak_smart(text, misty, name=name)

# Purpose: Look through calendar (JSON) for schedule and 
# provides gentle reminders to help focus
def misty_motivates_and_reminders(name):
    user_data = load_user_data(name)
    goal = user_data.get('goal', "working on your prototype")
    motivation = user_data.get('motivation', "The best way to predict the future is to create it.")
    
    text = f"I've been tracking your progress on {goal}. Just a reminder: {motivation}"
    mb.speak_smart(text, misty, name=name)

# Misty looks up research on the mental impacts (positive and negative)
# on mental wellbeing from https://www.health.harvard.edu/blog/the-health-effects-of-too-much-gaming-2020122221645
def misty_game_research():
    harvard_insights = [
        "According to Harvard Health, gaming can actually help people connect. It's a useful tool for social interaction, especially for children who find traditional communication challenging.",
        
        "Harvard research notes that video games have medical benefits! They are used to improve balance in people with degenerative diseases and help those with A D H D improve their thinking skills.",
        
        "Did you know surgeons use video games? Dr. Grinspoon notes that gaming can help train surgeons to perform technically complicated operations with better precision.",
        
        "Be careful with your hands! Harvard Health warns about 'Gamer’s Thumb.' It’s a real repetitive stress injury where the tendons in your thumb become inflamed from overuse.",
        
        "There's mixed research on the brain, but some studies show that gaming improves your control over your attention and your spatial reasoning.",
        
        "Harvard researchers suggest that while gaming is a fun community, it can become a problem if it's used as an escape from the real world. Moderation is the key to keeping it healthy."
    ]
    # Select a random insight to keep the demo fresh
    research_bit = random.choice(harvard_insights)

    # Use your brain module to speak it
    print(f"Misty Research: {research_bit}")
    mb.speak_smart(research_bit, misty)


# misty uses dialogue tree to psuh engagement
# e.g. how are you, how has your day beeen
def misty_engagement_dialogue(name):
    mb.speak_smart(f"I'm curious, {name}. On a scale of 1 to 10, how is your energy level right now?", misty)
    
    # For the demo, use terminal input as a 'Wizard of Oz' microphone
    try:
        energy = int(input(f"(Terminal) Enter {name}'s energy level (1-10): "))
        if energy > 7:
            mb.speak_smart("That's fantastic! Let's channel that energy into your goal.", misty, name=name)
        elif energy > 4:
            mb.speak_smart("Not bad. A quick walk might get you back to a ten.", misty, name=name)
        else:
            mb.speak_smart("I'm sorry to hear that. Maybe it's time for a 15 minute power nap.", misty, name=name)
    except ValueError:
        mb.speak_smart("I didn't quite catch that, but I'm here for you anyway.", misty, name=name)


# misty-openai integration
def misty_openai(user_input, user_name):
    """Sends text to OpenAI and returns a short, empathetic response."""
    try:
        response = client.chat.completions.create(
        model="gpt-4o-mini",
        
        # We give it a 'System Instruction' to keep the personality consistent
        messages =[
            {"role": "system", "content": (
                f"Context: You are Misty, a friendly, patient, and empathetic social robot. "
                f"You listen deeply and only give advice when explicitly asked. "
                f"When asked for advice by {user_name}, recommend guided breathing or gamified mindfulness specifically for Black women's mental wellbeing. "
                f"ALWAYS validate feelings first. "
                f"If {user_name} hasn't asked for advice, end with a brief follow-up like 'Would you like to tell me more?' "
                f"If {user_name} mentions 'depressed' or 'anxious', begin by asking if they have consulted a licensed professional."
                f"If {user_name} mentions themes of 'suicide' or 'death', connect them to 'resolve Crisis Services at 1-888-7-YOU-CAN (796-8226)'."
                f"Strict Limit: 25 words per response. "
                )},
                {"role": "user", "content": user_input}
            ], 
            max_tokens=60
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI Error: {e}")
        return "I'm sorry, my brain is a little foggy right now."


#Purppse: log gemini's responses
def log_session_transcript(user_name, user_input, misty_response):
    """Saves the conversation to a timestamped file for research analysis."""
    filename = f"transcripts/{user_name}_session_{datetime.now().strftime('%Y%m%d')}.txt"
    
    # Ensure the directory exists
    os.makedirs('transcripts', exist_ok=True)
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {user_name}: {user_input}\n")
        f.write(f"[{timestamp}] Misty: {misty_response}\n")
        f.write("-" * 30 + "\n")


#conduct mindfullness
def misty_mindfulness_exercise(name):
    """Leads the user through a 3-round gamified breathing exercise."""
    mb.speak_smart(f"Okay {name}, let's try some box breathing together. Follow my head movements. When I look up, breathe in. When I look down, breathe out.", misty)
    time.sleep(6)

    for i in range(1, 4):  # 3 Rounds
        print(f"Round {i}: Inhale...")
        misty.ChangeLED(0, 255, 255) # Cyan for calm
        # Tilt head up slowly over 4 seconds
        misty.MoveHead(-20, 0, 0, 10) 
        time.sleep(4)
        
        print(f"Round {i}: Hold...")
        misty.ChangeLED(255, 255, 255) # White for hold
        time.sleep(2)
        
        print(f"Round {i}: Exhale...")
        misty.ChangeLED(0, 100, 255) # Deep blue
        # Tilt head down slowly over 4 seconds
        misty.MoveHead(20, 0, 0, 10) 
        time.sleep(4)

    misty.MoveHead(0, 0, 0, 40) # Reset head
    mb.speak_smart("Great job. I hope that helped center you a little bit.", misty)
    time.sleep(4)


# purpose: make misty nod for listening purposes 
def misty_nods(repetitions=3):
    """Makes Misty perform a polite nod."""
    for _ in range(repetitions):
        # Pitch 15 is a slight 'down' look, Velocity 60 is snappy but smooth
        misty.MoveHead(15, 0, 0, 80) 
        time.sleep(0.3)
        # Pitch 0 is level
        misty.MoveHead(0, 0, 0, 80)
        time.sleep(0.3)

# purpose: tts --> correction --> send to misty-gemini
#returns: session_active flag (Bool)
def chat_with_misty(user_name):
    recognizer = sr.Recognizer()

    # ADJUSTMENTS FOR PATIENCE:
    # 0.8 seconds of silence is usually the sweet spot for a natural pause.
    recognizer.pause_threshold = 1.8
    # Energy threshold: higher means she's less likely to trigger on background noise
    recognizer.energy_threshold = 250 # avoid robot motor
    
    #set up TTS
    with sr.Microphone() as source:
        # This clears out any audio that happened while Misty was talking
        # so she doesn't "remember" her own voice.
        recognizer.adjust_for_ambient_noise(source, duration=0.4)
        
        # Give the participant a visual cue that she's listening
        print(f"\n[Misty is listening to {user_name}...]")
        misty.ChangeLED(255, 255, 0) # Yellow for listening
        
        misty_nods(2) # Just one polite nod to start the turn
        time.sleep(0.8) # Wait for motor whirring to finish before listening


        try:
            # 2. Listen (this will now stay open for 1.0s after the user stops talking)
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=20)
        except sr.WaitTimeoutError:
            return True # Just loop back if they didn't say anything

    try:
        # -----------------------  THINKING -----------------
       # 1. Convert Speech to Text (using Google's free Web API)
        print("Processing audio...")
        misty.ChangeLED(0, 0, 255) # Blue for thinking
        misty_nods(2)
        stt_result = recognizer.recognize_google(audio)

        # 2. THE EDIT STEP: Show you the text and wait for your input
        print(f"\n--- STT RESULT: \"{stt_result}\" ---")
        correction = input(f"Press ENTER to accept, or type the correction: ").strip()
        
        # If you typed something, use that. Otherwise, use the STT result.
        final_user_input = correction if correction else stt_result

        # 1. Get the response from openai
        misty_reply = misty_openai(final_user_input, user_name)

        # 2. Log the interaction for your research notes
        log_session_transcript(user_name, final_user_input, misty_reply)

        #initialize speech text
        speech_text = misty_reply # Set a default value here

        #3. Check for special triggers
        mindfulness_words = ["mindfulness", "breathing", "exercise", "meditate", "gamified"]
        trigger_end = ["goodbye", "bye", "stop", "thank you misty"]
        safety_keywords = ["professional", "doctor", "licensed", "depressed", "suicidal", "anxious", "hopeless", "death", "suicide"]


        # NEW: This actually checks if the user SAID a safety word
        has_safety_word = any(word in final_user_input.lower() for word in safety_keywords)

        
        #  THE GUARDRAIL: Check for safety words FIRST
        if has_safety_word:
            #changes purple for safety
            misty.ChangeLED(255, 0, 255)
            print("DEBUG: Safety/Professional topic detected. Bypassing mindfulness.")
            speech_text = f"{misty_reply} . . ." # Unique fingerprint for cache

        else:
            #changes blue for other topics
            misty.ChangeLED(0, 255, 0)
            if any(word in final_user_input.lower() for word in trigger_end):
                mb.speak_smart("It was wonderful talking with you. I'm here if you need me later.", misty, name=user_name)
                return False # Stop the loop
            
            # Only run mindfulness if it's NOT a safety topic
            elif any(word in final_user_input.lower() for word in mindfulness_words):
                misty_mindfulness_exercise(user_name)
                return True
            
            else: 
                speech_text=misty_reply
        
        # 4. Make Misty speak open ai response
        print(f"Misty says: {speech_text}")
        mb.speak_smart(speech_text, misty, name=user_name)

        # ---  ECHO CANCELLATION WAIT ---
        # Estimate wait time based on word count (approx 150 words per minute)
        # to prevents Misty from hearing  own voice in the next loop
        words = len(speech_text.split())
        wait_time = (words / 2.2) + 2.5 # Adds a 2-second buffer
        print(f"DEBUG: Waiting {wait_time}s for audio to finish...")
        time.sleep(wait_time)    
            
        return True # Keep the loop going
    
   
    except sr.UnknownValueError:
        print("Misty couldn't hear anything. Try typing manually:")
        manual_input = input("User says: ")
        if manual_input.lower() == "exit": return False
        reply = misty_openai(manual_input, user_name)
        mb.speak_smart(reply, misty, name=user_name)
        log_session_transcript(user_name, manual_input, reply)
        return True

    except Exception as e:
        print(f"Logging Error: {e}")
        return True


if __name__ == "__main__":
    # 1. Start by finding the person
    print("Misty is looking for P02...")
    identified_name = mb.misty_search() 
    misty.MoveHead(0, 0, 0, 40) # move her head back before joke delivery
    
    if identified_name:
        # Move head back to center for engagement
        mb.set_current_user(identified_name)
        misty.MoveHead(0, 0, 0, 40)
        time.sleep(2)


        #----- SESSION 3 -----
        mb.speak_smart("During this interaction, feel free to speak to me like you would a friend. If you want any recommendations, let me know. Otherwise, I'm here just to hold space for you.", misty, name=identified_name)
        time.sleep(5)


        session_active = True
        try:
            while session_active:

                session_active = chat_with_misty(identified_name)

                if session_active:
                    print("--- Ready for next user input ---")
                    time.sleep(3) # Short pause so Misty isn't "interrupting"

            # print(f"Session ended gracefully for {identified_name}.")

        except KeyboardInterrupt:
            print("\n[!] Session interrupted by researcher. Saving logs...")
        except Exception as e:
            print(f"\n[!] Unexpected error: {e}")
        finally:
            # This block runs NO MATTER WHAT (even on Ctrl+C)
            print(f"Finalizing transcript for {identified_name}...")
            # You could add a 'Session Ended Abruptly' note here if you want
            print(f"Demo complete.")
            #----- SESSION 3 -----

        # ----- SESSION 2 -----
        # 2. Run the new modules in sequence for the demo
        # misty_engagement_dialogue(identified_name)
        # time.sleep(10)
        
        # misty_motivates_and_reminders(identified_name)
        # time.sleep(10)
        
        # misty_game_research()
        # time.sleep(10)
        
        # misty_literary_recommendations(identified_name)
        # ----- SESSION 2 -----
        
        # print(f"Demo complete for {identified_name}.")
  
    else:
        print("No one found to interact with")
