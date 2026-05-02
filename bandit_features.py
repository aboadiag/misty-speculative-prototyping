# bandit_features.py
# Purpose: used to classify context
# features.py
import numpy as np
import misty_multimodal_processing as mmp

# establish the deviation from user baseline
class UserContextEvaluator:
    def __init__(self, calibration_steps=10):
        # Calibration logic
        self.calibration_steps = calibration_steps
        self.readings_count = 0
        self.stress_samples = []
        self.hr_samples = []
        
        self.state = {
            # CONTEXT (Psychological Proxies)
            "stress_baseline": 0,
            "last_valid_stress": 25, # Fallback if first Garmin read is null
            "stress_delta": 0,    
            "activity_score": 0,  
            
            # REWARDS (Engagement Proxies)
            "hr_baseline": 0,
            "current_hr": 75,
            "gaze_persistence": 0, 
            "calibrated": False
        }

    # get activity and stress from garmin
    def update_from_garmin(self, garmin_data):
        # 0. get data 
        curr_stress = garmin_data.get("stress_score")
        curr_hr = garmin_data.get("heart_rate")
        raw_activity = garmin_data.get("activity_type", "STILL")

        
       # 1. Stress Logic (Handling Monkey C Nulls)
        if curr_stress is not None:
            self.state["last_valid_stress"] = curr_stress
        
        # 2. Calibration Phase (Only with valid data)
        if not self.state["calibrated"]:
            # We need both HR and Stress to calibrate properly
            if curr_hr is not None:
                # If stress is null during calibration, use our last valid fallback
                self.stress_samples.append(self.state["last_valid_stress"])
                self.hr_samples.append(curr_hr)
                self.readings_count += 1
                
                if self.readings_count >= self.calibration_steps:
                    self.state["stress_baseline"] = sum(self.stress_samples) / len(self.stress_samples)
                    self.state["hr_baseline"] = sum(self.hr_samples) / len(self.hr_samples)
                    self.state["calibrated"] = True
                    print(f"User Baseline Set: Stress={self.state['stress_baseline']}, HR={self.state['hr_baseline']}")

        # 3. Update Current State & & Activity Override
        # Calculate Delta using the most recent valid stress score we have
        self.state["stress_delta"] = self.state["last_valid_stress"] - self.state["stress_baseline"]
        
        if curr_hr is not None:
            self.state["current_hr"] = curr_hr
            # --- PHYSIOLOGICAL OVERRIDE ---
            # Calculate HR intensity ratio
            hr_ratio = curr_hr / self.state["hr_baseline"] if self.state["hr_baseline"] > 0 else 1.0

            # If Garmin says STILL but HR is 15% above baseline (e.g., 80bpm -> 92bpm)
            if raw_activity == "STILL" and hr_ratio > 1.10:
                # We override the score to "Active" (0.8) because the body is working
                self.state["activity_score"] = 0.8
                print(f"  [Context Logic] HR Spike Detected ({curr_hr}). Overriding 'STILL' to 'Active'.")
            else:
                # Use the standard mapping if HR is normal or Garmin identifies the activity
                self.state["activity_score"] = self._map_activity(raw_activity)
            
        # self.state["activity_score"] = self._map_activity(garmin_data.get("activity_type"))

        

    def update_from_vision(self, vision_buffer_value):
        # Expects the 0.0-10.0 'sticky' value we discussed
        self.state["gaze_persistence"] = vision_buffer_value

    #context vector (between 0 and 1) --> anxiety or depression based on activity
    def get_context_vector(self):
        """
        Returns [Normalized Stress Delta, Activity Score].
        Stress is normalized such that 0.5 is 'Normal', >0.5 is 'Anxious Spike'.
        """
        # Map stress delta (-50 to +50) to a 0.0-1.0 range
        # 0.5 means exactly at baseline.
        stress_feat = np.clip((self.state["stress_delta"] / 100.0) + 0.5, 0, 1)
        
        # Activity score is already 0.0-1.0
        activity_feat = self.state["activity_score"]
        
        return np.array([stress_feat, activity_feat])

    # calculate rewards based on engagement proxies (HR and gaze) --> behavioral versus social
    def calculate_reward(self):
        # Success = (Physical Activation) + (Social Connection)
        # HR effort is relative to their learned baseline
        hr_effort = max(0, (self.state["current_hr"] - self.state["hr_baseline"]) / 20.0)
        social_effort = self.state["gaze_persistence"] / 10.0 
        
        return np.clip((0.6 * hr_effort) + (0.4 * social_effort), 0, 1) #weighting behevioral over social

    # map activity sensing to vector
    def _map_activity(self, activity_type):
        # Clinical Mapping: 0.0 is the 'Depressive' baseline (Stillness)
        mapping = {
            "STILL": 0.0, 
            "WALKING": 0.5, # light activity
            "ON_FOOT": 0.5, # light activity
            "RUNNING": 1.0, # vigorous actvitiy 
            "CYCLING": 1.0 # vigorous activity
        }
        return mapping.get(activity_type.upper() if activity_type else "", 0.2)