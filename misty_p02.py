# misty_p02.py
## Purpose: some ideas came up with P02
import misty_brain as mb
import time
import random
import requests
import json
import os
import re

# Use the Robot instance from your brain
misty = mb.misty

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
    mb.speak_smart(text, misty)

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
            mb.speak_smart("That's fantastic! Let's channel that energy into your goal.", misty)
        elif energy > 4:
            mb.speak_smart("Not bad. A quick walk might get you back to a ten.", misty)
        else:
            mb.speak_smart("I'm sorry to hear that. Maybe it's time for a 15 minute power nap.", misty)
    except ValueError:
        mb.speak_smart("I didn't quite catch that, but I'm here for you anyway.", misty)

if __name__ == "__main__":
    # 1. Start by finding the person
    print("Misty is looking for P01...")
    identified_name = mb.misty_search() 
    misty.MoveHead(0, 0, 0, 40) # move her head back before joke delivery
    
    if identified_name:
        # 2. Run the new modules
        # Move head back to center for engagement
        mb.set_current_user(identified_name)
        misty.MoveHead(0, 0, 0, 40)
        time.sleep(1)

        # # 2. Run the new modules in sequence for the demo
        # misty_engagement_dialogue(identified_name)
        # time.sleep(10)
        
        # misty_motivates_and_reminders(identified_name)
        # time.sleep(10)
        
        # misty_game_research()
        # time.sleep(10)
        
        misty_literary_recommendations(identified_name)
        
        print(f"Demo complete for {identified_name}.")
  
    else:
        print("No one found to interact with")
