from flask import Flask, request
import logging
import requests
import json
import time
import base64
import os

# ELEVEN LABS API info
ELEVEN_API_KEY = os.getenv("ELEVEN_LAB_KEY")  
VOICE_ID = "SAz9YHcvj6GT2YYXdXww" # River, Relaxed, Neutral, Informative
# VOICE_ID = "21m00Tcm4TlvDq8ikWAM"    # Rachel Voice ID

#misty config
MISTY_IP = os.getenv("ROBOT_URL")
audio_upload_url = f"http://{MISTY_IP}/api/audio"
led_url = f"http://{MISTY_IP}/api/led"
led_blue = {"red": 0, "green": 255, "blue": 255}
led_red = {"red": 255, "green": 0, "blue": 0}
led_green = {"red": 0, "green": 255, "blue": 0}
# speak_url = f"http://{MISTY_IP}/api/tts/speak"

# Global variable to track when Misty last spoke
last_speech_time = 0 
SPEECH_COOLDOWN = 15  # Seconds to wait before speaking again
# NEW: Tracks if we have already done the startup routine
IS_SESSION_ACTIVE = False # Tracks if startup scan is done

# Cleaned up SSML (removed newlines to be safe)
speech_stress = """<prosody rate="fast" pitch="high">I am detecting high stress levels. <break time="500ms"/> Please slow down.</prosody>"""
speech_calm = """<prosody rate="slow" pitch="low">I am detecting low stress levels. <break time="500ms"/> Continue breathing calmly.</prosody>"""

# Disable annoying server startup logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

print("--- MISTY SERVER LISTENING ---")


def misty_speaks_elevenlabs(text_to_say, stability_setting=0.5):
    """
    1. Fetches audio from ElevenLabs (RAM only).
    2. Converts to Base64.
    3. Uploads to Misty.
    """
    global last_speech_time
    current_time = time.time()
    
    if (current_time - last_speech_time) < SPEECH_COOLDOWN:
        return 

    # 2. Engage Physical Robot (Look at User)

    print(f"🗣️ Fetching ElevenLabs Voice: '{text_to_say}' (Stability: {stability_setting})")

    try:
        # A. Call ElevenLabs API
        eleven_url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVEN_API_KEY
        }
        data = {
            "text": text_to_say,
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {
                "stability": stability_setting,       # 0.8 = Calm, 0.3 = Expressive
                "similarity_boost": 0.5
            }
        }
        
        # This request gets the raw audio bytes
        response = requests.post(eleven_url, json=data, headers=headers)
        
        if response.status_code != 200:
            print(f"⚠️ ElevenLabs Error: {response.text}")
            return

        # B. Convert Raw Audio Bytes to Base64 directly
        # We skip saving to disk and just encode the response content
        encoded_string = base64.b64encode(response.content).decode('utf-8')

        # C. Send to Misty
        payload = {
            "FileName": "eleven_temp.mp3",
            "Data": encoded_string,
            "ImmediatelyApply": True,
            "OverwriteExisting": True
        }
        
        requests.post(audio_upload_url, json=payload, timeout=10)
        
        last_speech_time = current_time
        print("   -> Audio sent to robot.")

    except Exception as e:
        print(f"⚠️ Error: {e}")

# inputs is the chest color
def change_misty_color(led_data):
    """Sends a command to Misty to change her chest LED."""
    try:
        requests.post(led_url, 
                      headers={"Content-Type": "application/json"},
                      data=json.dumps(led_data))
    except Exception as e:
        print(f"⚠️ Could not talk to Misty: {e}")


def misty_startup_scan():
    """
    Runs ONCE at the start.
    1. Resets head.
    2. Starts tracking.
    3. Scans the room (moves head left/right) to catch a face.
    4. Speaks a greeting.
    """
    print("🤖 STARTUP: Scanning for user...")
    base_url = f"http://{MISTY_IP}/api"

    try:
        # 1. Stop & Reset
        requests.post(f"{base_url}/drive/stop")
        requests.post(f"{base_url}/faces/tracking/stop")
        
        # 2. Move Head to Center-Left (Starting position)
        # Search range for the head (Pitch, Roll, Yaw)
        # Yaw is left/right. -40 is right, 40 is left
        requests.post(f"{base_url}/head", json={"Pitch": -5, "Roll": 0, "Yaw": 0, "Velocity": 60})
        time.sleep(1.5) # Wait for her to get to starting position

        # 3. Enable Face Tracking (It runs in background)
        requests.post(f"{base_url}/faces/tracking/start")
        
        # 4. Perform a "Scan" (Slowly move head from Left to Right)
        # If she sees a face during this move, Tracking *should* take over.
        print("   -> Panning head...")
        requests.post(f"{base_url}/head", json={"Pitch": -5, "Roll": 0, "Yaw": -0, "Velocity": 20}) # Slow sweep
        
        # 5. Turn LED Orange (Searching)
        change_misty_color({"red": 255, "green": 140, "blue": 0})
        
        # 6. Wait for the sweep to finish/lock on
        time.sleep(6)

        # 7. Greeting Audio (Visual confirm)
        print("   -> Session Active.")
        change_misty_color({"red": 0, "green": 255, "blue": 100}) # Green
        
        # 8. NOW we speak (Head is stopped)
        print("   -> Session Active.")
        change_misty_color({"red": 0, "green": 255, "blue": 100}) # Green

    except Exception as e:
        print(f"⚠️ Startup Error: {e}")

# define app route
@app.route('/update_breath', methods=['POST'])

# function: input --> breath rate from garmin watch
# output: color change of misty's chest
def update_breath():
    global IS_SESSION_ACTIVE #DEFINE GLOBAL
    data = request.json
    breath_rate = data.get('breath_rate', 0)
    print(f"🫁 Breath Rate: {breath_rate}")

    # --- STARTUP LOGIC ---
    if not IS_SESSION_ACTIVE:
        # This is the FIRST data packet we received.
        # Ignore the breath rate for a second and just find the user.
        misty_startup_scan()

        IS_SESSION_ACTIVE = True
        return {"status": "initialized"}, 200

    # THE LOGIC:
    # If breathing is slow (< 22), be calm (BLUE).
    # If breathing is fast (>= 22), be alert (RED).
    if breath_rate < 25:
        print("   -> CALM (Turning Blue)")
        change_misty_color(led_blue) # RGB for Blue
        misty_speaks_elevenlabs("Your breathing is perfect. Keep it up.", stability_setting=0.85)
        time.sleep(5)
    else:
        print("   -> FAST (Turning Red)")
        change_misty_color(led_red) # RGB for Red
        misty_speaks_elevenlabs("I'm sensing some stress. Let's take a moment.", stability_setting=0.50)# lower stability --> more empathetic sounding

        time.sleep(5)
    # else:
    #     # State: NORMAL (12 - 15 bpm)
    #     # We don't speak here, just show Green/Normal status
        print("   -> NEUTRAL (Green)")
        change_misty_color(led_green)

    return {"status": "success"}, 200


if __name__ == '__main__':
    # host='0.0.0.0' allows external devices (like the watch) to connect
    app.run(host='0.0.0.0', port=5000, debug=True)


# def misty_speaks(speech_data):
#     """Sends a command to Misty to utter speech."""
#     global last_speech_time # Use the global timer

#     # Check if we spoke too recently
#     current_time = time.time()
#     if (current_time - last_speech_time) < SPEECH_COOLDOWN:
#         # It hasn't been 10 seconds yet, so stay silent
#         return 

#     # If we are clear to speak:
#     print(f"🗣️ Speaking now...")
    
#     # SSML requires a root <speak> tag.
#     # .strip() removes accidental newlines at the start
#     clean_data = speech_data.strip()
#     if not clean_data.startswith("<speak>"):
#         final_ssml = f"<speak>{clean_data}</speak>"
#     else:
#         final_ssml = clean_data

#     payload = {
#         "text": final_ssml,
#         "flush": True,       
#         "utteranceId": "bio_feedback_msg" 
#     }
        
#     try:
#         requests.post(speak_url, json=payload, timeout=5)
#         # Reset the timer ONLY if the request worked
#         last_speech_time = current_time 
#     except Exception as e:
#         print(f"⚠️ Speech Error: {e}")
