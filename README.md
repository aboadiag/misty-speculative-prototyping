# SPECULATIVE MISTY CO-DESIGN
This project is used as a template for co-design activities conducted with stakeholders.

Current modules:
## interaction_app.py
Flask server that receives behavior requests from Misty-Brain and Misty-Vision module.

## misty_vision_module.py
Vision module that integrates /serengil/deepface. Currently, Misty's vision system captures image, stored in deepface DB. Later retrieved for detection & recognition.

## misty_brain.py
Misty's decision-making and behavioral module. Integrates Eleven Labs Client API Library. 

## Misty-Garmin
Integrates Garmin activity detection with Misty web API. Uses Eleven Labs Web API.

# Instructions:
## Conda activate virtual environment & activate ngrok tunnel.
```
ngrok http 5000
```
## Copy Ngrok tunnel URL --> Paste it to misty_brain.py
```
python misty_brain.py
```

