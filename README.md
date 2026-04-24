# SPECULATIVE MISTY CO-DESIGN
This project is used as a template for co-design activities conducted with stakeholders.

Current modules:
## interaction_app.py
Flask server that receives behavior requests from misty_brain and misty_vision_module.

## misty_vision_module.py
Vision module that integrates /serengil/deepface (lightweight wrapper for various models!). Currently, Misty's vision system captures image, stored in deepface DB. Later retrieved for detection & recognition. Current detection model: opencv (fast & accurate).

## misty_multimodal_processing.py
Performs vision processing (e.g. cropping, learning faces, etc) and speech request processing. Integrates Eleven Labs Client API Library. 

## misty_brain.py
Misty's decision-making and behavioral module. Imports helper functions from modules misty_multimodal processing (e.g. user_calibration).

## /misty-garmin
Stores Garmin app, MistyHeartMonitor activity detection, specifically respiration. Most Garmin application projects are in their own folder e.g. "mistyActivityandStress" or "MistyActivityMonitor."

# Instructions:
## Conda activate virtual environment & activate ngrok tunnel.
```
ngrok http 5000
```
## Copy Ngrok tunnel URL --> Paste it to misty_multimodal_processing.py
```
python misty_brain.py
```

