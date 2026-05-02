# misty_p03.py
## Purpose: some ideas came up with P03
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
import base64
import shutil


load_dotenv() # Add this - it loads the variables from .env into your system

# Robot instance from misty brain
misty = mb.misty

listening_duration = 60


# configure api key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize a global list to store the conversation
chat_history = []

# import wave
# with wave.open("audio_cache/current_chunk.wav", 'r') as f:
#     print(f"Channels: {f.getnchannels()}")
#     print(f"Sample rate: {f.getframerate()}")
#     print(f"Sample width: {f.getsampwidth()}")
#     print(f"Frames: {f.getnframes()}")


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

# misty-openai integration
def misty_openai(user_input, user_name, history):
    """Sends text to OpenAI and returns a short, empathetic response."""
    try:
        # We give it a 'System Instruction' to keep the personality consistent
        system_instructions = {
            "role": "system", 
             "content": (
                f"You are Misty, an empathetic social robot. Your goal is to listen to {user_name}'s reflections. "
                "Maintain continuity: if they mention something in the history, reference it naturally. "
                "Keep responses supportive, but don't repeat yourself. "
                "If {user_name} asks for advice, provide one personalized recommendation. "
                "If they mention 'depressed' or 'anxious', ask if they have a professional to talk to. "
                "If they mention 'suicide' or 'death', give the Crisis line: 1-888-7-YOU-CAN. "
                "Strict Limit: 25 words per response. "
                ) # 25 words == 125 to 160 characters
        }

        # Build the message list: System + History + New Input
        messages = [system_instructions]
        messages.extend(history)
        messages.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=80
        )
        
        ai_message = response.choices[0].message.content.strip()
        
        # Update history with the new exchange
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": ai_message})
        
        return ai_message
    except Exception as e:
        print(f"OpenAI Error: {e}")
        return "I'm here for you, even if my brain is a bit foggy."

#Purpose: allow P03 to verbally record their reflections
def verbal_reflection_session(instruction_text, user_name, duration):
    try:
        misty_ip = misty.ip
    except AttributeError:
        misty_ip = mb.MISTY_IP

    # instruction_text =(
    #     f"Okay {user_name}, I'm going to listen for {duration} seconds. "
    #     "Feel free to reflect out loud on how you're feeling right now."
    #     )

    # 1. Create a unique filename using a timestamp
    timestamp = datetime.now().strftime("%H%M%S")
    reflection_file = f"reflection_{user_name}_{timestamp}.wav"
    local_path = os.path.join("audio_cache", reflection_file) # Path for local save
    
    # I'm hear to listen to your reflections
    mb.speak_smart(instruction_text, misty, name=user_name)
    time.sleep(1)
    time.sleep(len(instruction_text) * 0.05) # Wait for Misty to finish speaking

    # 2. Start Recording (filename, overwrite, silenceTimeout, duration)
    print(f"[!] Recording reflection for {duration}s...")
    misty.StartRecordingAudio(reflection_file)

    # 3. Visual Pulse Loop
    # We pulse every 2 seconds (1s bright, 1s dim)
    rounds = duration // 2
    for i in range(rounds):
        print(f"Recording... {duration - (i*2)}s remaining")
        misty.ChangeLED(0, 255, 0) # Pulse Bright green
        time.sleep(1)
        misty.ChangeLED(0, 80, 0)  # Pulse Dim green
        time.sleep(1)

    # STOP Recording
    misty.StopRecordingAudio()
    print("[!] Recording finished. Fetching for playback...")

    # Give Misty a moment to finish the .wav header
    time.sleep(3)

    reflection_file = download_misty_audio(reflection_file)

    return reflection_file

def download_misty_audio(reflection_file):
    local_path = os.path.join("audio_cache", reflection_file) 
    os.makedirs("audio_cache", exist_ok=True) # Ensure folder exists

    #download audio using rest api    
    print(f"[!] Downloading via GetAudioFile: {reflection_file}")
    try:
        # WRAPPER METHOD CALL
        # We pass Base64=True to ensure we get the string in the JSON response
        response = misty.GetAudioFile(reflection_file,True)
        
        # Parse the wrapper's response
        # Most mistyPy versions return the response object from 'requests'
        # raw =response.json()
        # print(f"[DEBUG] GetAudioFile raw response: {raw}")


        data = response.json().get("result", {})
        encoded_string = data.get("base64")
        
        if encoded_string:
            with open(local_path, "wb") as f:
                f.write(base64.b64decode(encoded_string))
            
            # --- NEW CHECK: Is the file empty? ---
            file_size = os.path.getsize(local_path)
            if file_size < 100: # 100 bytes is essentially an empty header
                print(f"[Warning] {reflection_file} is empty ({file_size} bytes). Recording likely failed.")
            else:
                print(f"[Success] Saved {reflection_file} ({file_size} bytes)")
        else:
            print("[Error] No base64 data returned from Misty.")
            
    except Exception as e:
        print(f"[!] GetAudioFile Error: {e}")

    return local_path

#Purpose: Misty plays back recorded reflection
def playback_reflection(reflection_audio, duration, user_name):
    # Note: Misty stores 'user_reflection.wav' internally. 
    # We can trigger it to play immediately from her own memory.
    msg = "Thank you for sharing that. Here is what I heard."
    mb.speak_smart(msg, misty, name=user_name)
    time.sleep(len(msg) * 0.1 + 1)
    
    misty.PlayAudio(reflection_audio, 100)
    
    # Wait for playback to finish before continuing the loop
    print(f"Waiting {duration}s for playback to finish...")
    time.sleep(duration + 2)

# Purpose: Get recommnedations from open ai (integrates misty_openai)
#returns: response
def get_openai_recommendation(transcript_text, user_name, history):
    # local_path = os.path.join("audio_cache", filename)
    
    # print(f"[!] Transcribing local file: {filename}")
    # transcript, scrubbed_time = transcribe_file(local_path)

    if not transcript_text:
        return "I heard you speaking, but I couldn't quite catch the words."

    ai_response = misty_openai(transcript_text, user_name, history)
    log_session_transcript(user_name, transcript_text, ai_response)


    return ai_response


# Purpose:  Helper to turn a wav file into text. 
# Returns a tuple: (transcript_string, scrubbed_time_string)   
def transcribe_file(file_path):
    recognizer = sr.Recognizer()
    # Boost energy threshold so it picks up quieter voices
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = False

    try:
        with sr.AudioFile(file_path) as source:
            # Clean up the audio before sending to Google
            # recognizer.adjust_for_ambient_noise(source, duration=0.2)
            audio = recognizer.record(source)
        
        transcript = recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        transcript = "" # Return empty string if no speech detected
    except Exception as e:
        print(f"[!] Transcription error: {e}")
        transcript = ""

    scrubbed_time = datetime.now().strftime("%H:%M")
    return transcript, scrubbed_time

# Purpose: Natural turntaking: Records in chunks and decides if the user is finished based on speech content.
# input: what user said, name of user, number of interactions
# returns: full transcript, users verbal reflection file
def natural_turn_taking_session(instruction_text, user_name, max_rounds=15):
    recorded_chunks = [] # storing the various things user says before asking for advice
    # mb.speak_smart(instruction_text, misty, name=user_name)
    # time.sleep(max(len(instruction_text) * 0.08, 3.0) + 1.5)   # Larger buffer + 1.5s margin # 6 seconds to speak 125-160 chars
    speak_and_wait(instruction_text, misty, name=user_name)

    # INIT
    full_transcript = ""
    last_valid_chunk = None # Fallback for playback if master is disabled
    
    # Keywords that signal the user is handing the turn back
    stop_keywords = ["done", "finished", "stop", "that is it"] # stop interaction trigger
    question_cues = ["you think", "your thoughts", "advice",
                      "help", "any ideas", "reflection", "playback", "recommendations"]
    safety_keywords = ["kill myself", "want to die", "suicide", "depressed", "anxious", "stressed", "end it"]

    # SET GREEN HERE - Before the loop starts
    # misty.ChangeLED(0, 255, 0)

    for round_num in range(max_rounds):
        print(f"[Turn-Taking] Listening round {round_num + 1}...")

        misty.ChangeLED(0, 255, 0) 
        time.sleep(0.5) # This gap prevents the flicker collision

        # 1. Record a short burst (12 seconds is a good 'thought' length)
        chunk_file = "current_chunk.wav" # 12 second audio file names
        misty.StopRecordingAudio()
        time.sleep(2.0)  # Let the API settle
        misty.StartRecordingAudio(chunk_file)
        time.sleep(10) 
        misty.StopRecordingAudio()

        # back channel --> listening biatch
        print("[Backchannel] Nodding...")
        misty.MoveHead(15, 0, 0, 40) # Nod down
        time.sleep(0.4)
        misty.MoveHead(0, 0, 0, 40)  # Back to level
        
        # Give the hardware 1 second to finalize the .wav header on the SD card
        time.sleep(3.0)
        
        # 2. Fetch and Transcribe -->  Process/Transcribe (BLUE)
        temp_local_path = download_misty_audio(chunk_file)
        
        if temp_local_path and os.path.exists(temp_local_path):
            # 1. DELETE FROM MISTY IMMEDIATELY
            # This keeps the '346 files' problem from ever returning
            misty.DeleteAudio(chunk_file)

            # SAVE A LOCAL COPY so we don't lose this round's audio
            # The robot overwrites its file, but our laptop keeps every round

            # Create a quick timestamp so filenames never overlap
            timestamp = datetime.now().strftime("%H%M%S")
            permanent_local_path = f"saved_{user_name}_{timestamp}_round_{round_num}.wav"

            # permanent_local_path = f"saved_{user_name}_round_{round_num}.wav"
            shutil.copy(temp_local_path, permanent_local_path)

            current_chunk_text, _ = transcribe_file(temp_local_path)
            current_chunk_text = current_chunk_text.lower()

            # --- BACKCHANNELING NOD ---
            # If the user actually said something, give a small "I hear you" nod
            if current_chunk_text.strip():
                # add to transcript, apprent to  recorded_chunks list, and update last_valid chunk!
                full_transcript += " " + current_chunk_text
                recorded_chunks.append(permanent_local_path)
                last_valid_chunk = permanent_local_path # Keep track for playback

            print(f"[User Said]: {current_chunk_text}")
            # full_transcript += " " + current_chunk_text
            
            # --- ROBUST CUE CHECKING ---
            # We check for WHOLE WORDS only using regex \b

            # Create a rolling window of the last ~25 words to catch split sentences
            recent_context = (full_transcript + " " + current_chunk_text).lower()

            has_safety = any(re.search(rf"\b{re.escape(s)}\b", recent_context) for s in safety_keywords)
            has_stop = any(re.search(rf"\b{re.escape(w)}\b", recent_context) for w in stop_keywords)
            has_cue = any(re.search(rf"\b{re.escape(c)}\b", recent_context) for c in question_cues)
            

            if has_safety or has_cue or has_stop:
                print("[!] Valid natural cue detected. Ending session.")
                break

        
        if round_num < max_rounds - 1:
            print("Continuing to listen...")

    # --- END RECORDING AUDIO ----
    misty.StopRecordingAudio() 
    time.sleep(0.5)
    print("[!] User Reflection File recording finalized.")
    

    return full_transcript.strip(), recorded_chunks, last_valid_chunk #, reflection_file

def upload_to_misty(local_file_path):
    """Pushes a local laptop file to Misty's internal storage via REST API."""
    try:
        # Get the IP from your misty object
        ip = misty.ip 
        url = f"http://{ip}/api/audio"
        
        with open(local_file_path, 'rb') as f:
            file_data = f.read()
            # We encode the file to Base64 because that's what Misty's API expects
            encoded_data = base64.b64encode(file_data).decode('utf-8')
            
            payload = {
                "FileName": os.path.basename(local_file_path),
                "Data": encoded_data,
                "ImmediatelyApply": True,
                "OverwriteExisting": True
            }
            
            response = requests.post(url, json=payload)
            return response.status_code == 200
    except Exception as e:
        print(f"[Upload Error]: {e}")
        return False
    
def process_user_intent(user_speech, voice_chunks, user_name):
    """Automated logic to decide between playback, advice, or both."""
    user_speech_lower = user_speech.lower()

    # Reset head before acting
    # misty.ChangeLED(0, 0, 255)# thinking
    misty.MoveHead(0, 0, 0, 40)
    
    # 1. Intent Detection
    wants_playback = any(word in user_speech_lower for word in ["reflection", "playback", "hear myself"])
    wants_advice = any(word in user_speech_lower for word in ["advice", "think", "what do you", "help"])
    is_finished = any(word in user_speech_lower for word in ["done", "finished", "stop", "that is it"])

    # 2. Action: Playback USER REFLECTION
    if wants_playback:
        playback_msg = "I've been listening closely. Here is what I heard you say."
        # Misty is "Searching" her memory (Blue)
        # misty.ChangeLED(0, 0, 255)
        # mb.speak_smart(playback_msg, misty, name=user_name)
        # time.sleep(3)
        speak_and_wait(playback_msg, misty, name=user_name)

        # Misty is "Speaking/Playing" (Green)
        # misty.ChangeLED(0, 255, 0)
        if isinstance(voice_chunks, list):
            for chunk in voice_chunks:
                # --- THE FIX STARTS HERE ---
                print(f"Uploading to Misty: {chunk}")
                success = upload_to_misty(chunk)

                if success:
                    filename_only = os.path.basename(chunk)
                    print(f"Playing back on Misty: {filename_only}")
                    misty.PlayAudio(filename_only, 100)
                    # Wait for actual chunk duration + small buffer
                    import wave
                    try:
                        with wave.open(chunk, 'r') as wf:
                            chunk_duration = wf.getnframes() / wf.getframerate()
                        print(f"[Chunk duration: {chunk_duration:.1f}s]")
                        time.sleep(chunk_duration + 1.5)
                    except Exception:
                        time.sleep(12)  # fallback
                    # # Now that she has the file, we use just the filename (no path)
                    # filename_only = os.path.basename(chunk)
                    # print(f"Playing back on Misty: {filename_only}")
                    # misty.PlayAudio(filename_only, 100)
                    # time.sleep(10.5) 

                else:
                    print(f"Failed to upload {chunk}")
                
                # Wait for her to finish the 10s chunk
                # time.sleep(10.5) 
                # --- THE FIX ENDS HERE ---

    # 3. Action: Advice (This is where the Safety Check lives)
    # Trigger if they ask OR if they mention clinical keywords
    safety_keywords = ["depressed", "anxious", "kill myself", "die", "suicide"]
    has_safety_trigger = any(word in user_speech_lower for word in safety_keywords)

    if wants_advice or is_finished or has_safety_trigger:
        advice = get_openai_recommendation(user_speech, user_name, chat_history)
        
        # Calculate how long it will take to say the advice (avg 0.15s per word)
        estimated_speech_time = len(advice) * 0.05
        speech_duration = len(advice) / 750
        wait_time = speech_duration + 3.0 + 3.0  # duration + upload buffer + DSP cooldown
        
        speak_and_wait(advice, misty, name=user_name)
        # gesture_while_speaking(wait_time)
        # mb.speak_smart(advice, misty, name=user_name)
        # gesture_while_speaking(len(advice) * 0.05)
        
        
        # KEY: Stop the script here until she is done talking
        print(f"Waiting {wait_time:.1f}s for Misty to finish speaking...")
        # time.sleep(wait_time)

    # 4. Action: Polite check if they didn't use a keyword
    # if not (wants_playback or wants_advice or is_finished):
    #     apology = "I hope I didn't cut you off there. I'm still learning how to listen."
    #     mb.speak_smart(apology, misty, name=user_name)
    #     gesture_while_speaking(len(apology) * 0.05)
    #     time.sleep(3)

    # transition from thinking --> listening
    # misty.ChangeLED(0, 255, 0) # Back to Green


def gesture_while_speaking(duration):
    """Moves Misty's arms up and down for the duration of her speech."""
    start_time = time.time()
    while time.time() - start_time < duration:
        # Move arms up
        misty.MoveArms(30, 30, 40, 40) # Left, Right, Velocity
        time.sleep(0.8)
        # Move arms down
        misty.MoveArms(80, 80, 40, 40)
        time.sleep(0.8)
    # Reset arms to neutral
    misty.MoveArms(90, 90, 20, 20)




def speak_and_wait(text, misty_object, name=None):
    """Speaks text and waits based on actual audio file duration."""
    mb.speak_smart(text, misty_object, name=name)
    
    # Find the cached audio file to get real duration
    import hashlib, glob
    from mutagen.mp3 import MP3
    
    clean_text = text.strip()
    text_hash = hashlib.md5(clean_text.encode()).hexdigest()[:12]
    
    # Match how speak_smart names the file
    current_user = mb.mmp.CURRENT_USER
    pattern = f"audio_cache/River_{current_user}_{text_hash}.mp3"
    
    try:
        audio = MP3(pattern)
        actual_duration = audio.info.length
        print(f"[Audio duration: {actual_duration:.1f}s]")
    except Exception:
        # Fallback to character estimate if file not found
        actual_duration = len(text) / 750
        print(f"[Estimated duration: {actual_duration:.1f}s]")
    
    # Wait for actual playback + upload lag + DSP cooldown
    total_wait = actual_duration + 2.0 + 2.0
    print(f"[Waiting {total_wait:.1f}s for speech to complete...]")
    time.sleep(total_wait)

def session_2_statemachine():
    print("Misty is looking for P03...")
    identified_name = mb.misty_feels() 
    misty.MoveHead(0, 0, 0, 40) # move head 
    
    if identified_name:
        # Move head back to center for engagement
        # mb.set_current_user(identified_name)
        misty.MoveHead(0, 0, 0, 40) # reset head 
        turn_count = 0

     # SESSION 2:
    # CONVERSATIONAL INTRO --> session 2
    if turn_count == 0:
        intro = f"Okay {identified_name}, I'm going to listen for {listening_duration} seconds. Feel free to reflect out loud on how you're feeling right now."
    else:
        intro = f"I'm listening. Is there anything else you'd like to share? Again, I'm going to listen for {listening_duration} seconds."


    # ---- USER RECORDING ---- record user verbal reflections --> return audio file
    reflection_audio_file = verbal_reflection_session(intro, identified_name, listening_duration)

    # ----- WOZ ---- user input
    wizard_decision = input("Type 'p' for Playback, 'a' for AI Advice, or 'b' for Both: ").strip().lower()
    
    # check if playback or both
    if wizard_decision in ['p', 'b']:
        playback_reflection(reflection_audio_file, listening_duration, identified_name)


    # else its both playing the reflection  
    if wizard_decision in ['a', 'b']:
        #  Misty is "thinking"
        misty.ChangeLED(0, 0, 255)
        advice = get_openai_recommendation(reflection_audio_file, identified_name, chat_history)

        # misty responding
        misty.ChangeLED(0, 255, 0) # Back to Green
        mb.speak_smart(advice, misty, name=identified_name)
        # log_session_transcript(identified_name, "[Verbal Reflection]", advice) #log transcript

        # time to speak before starting the next loop
        time.sleep(len(advice) * 0.1 + 2)
        

    elif wizard_decision not in ['p', 'a', 'b']:
        print("Skipping feedback for this round.")
    
    # ---- NEXT TURN ----
    turn_count += 1
    print(f"\n--- End of Turn {turn_count} ---")

def session_3_statemachine():
    print("Misty is looking for P03...")
    identified_name = mb.misty_feels() 
    misty.MoveHead(0, 0, 0, 40) # move head 
    
    if identified_name:
        master_chunk_list = [] # 1. ADD THIS HERE
        # Move head back to center for engagement
        # mb.set_current_user(identified_name)
        misty.MoveHead(0, 0, 0, 40) # reset head 
        turn_count = 0

        try:
            while True:
                #SESSION 3
                # --- STAGGERED ONBOARDING LOGIC ---
                if turn_count == 0:

                    print("Intro Stage 1: Listening LED")
                    intro = (f"Okay {identified_name}, I'm here to listen. While you are speaking, I will record you, "
                             "When you're finished, you can say 'playback reflection' to hear yourself, "
                            "or ask for my advice. Just say 'I'm done' when you are ready.")

                    # time.sleep(len(intro) * 0.1 + 2)

                    # # Move to the next turn so she doesn't repeat this
                    # turn_count = 1 
                    # intro = "I'm listening. Is there anything you'd like to share?"
        
                else:
                    # print(f"Misty says nothing.")
                    intro = f"I'm listening. Is there anything else you'd like to share?"
                    print(f"Turn {turn_count}: Standard session loop")
                
                # Start the session
                user_speech, voice_chunks, reflection_file = natural_turn_taking_session(intro, identified_name)

                # ---  Logic ---
                if user_speech:
                    #ADD THE NEW CHUNKS TO THE MASTER LIST
                    master_chunk_list.extend(voice_chunks)
            
                    print(f"\n[USER]: {user_speech}")
                    process_user_intent(user_speech, master_chunk_list, identified_name)

                    # If the user said they are "done", exit the whole program
                    if any(word in user_speech.lower() for word in ["done", "finished", "that is it"]):
                        print("User is finished. Exiting interaction.")
                        msg = "I've saved your reflections. Thank you for sharing."
                        speak_and_wait(msg, misty)
                        # mb.speak_smart(msg, misty)
                        # time.sleep(len(msg) * 0.05)
                        break # This stops Turn 2 from starting automatically

                # # ---- NEXT TURN ----
                turn_count += 1
                print(f"\n--- End of Turn {turn_count} ---")

                
        except KeyboardInterrupt:
            print("\n[!] Session ended by researcher.")
        except Exception as e:
            print(f"\n[!] Unexpected error: {e}")
        finally:
            print(f"Finalizing transcript for {identified_name} and stopping recording. Demo complete.")
            misty.StopRecordingAudio()
    else:
        print("No one found to interact with")


    
if __name__ == "__main__":
    # # ----- DEBUGGING AUDIO HARDWARE---- 
    # clean_sweep()
    # misty.StopRecordingAudio() 
    # time.sleep(1)
    # mb.hardware_mic_test()

    session_3_statemachine()


    
               