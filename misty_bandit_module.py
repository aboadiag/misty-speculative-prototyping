# misty_bandit_module.py
# Purpose: Reusable behvaioral personalization pipeline
import joblib # to build user profile
from bayesianbandits import Arm, NormalInverseGammaRegressor, ContextualAgent, ThompsonSampling
import numpy as np
import os

# Class: used to define resuable arms (decisions) and context
# with thomson sampling policy
class PersonalizationBrain:
    def __init__(self, arm_names, context_map):
        """
        arm_names: List of strings (e.g., ["Charismatic", "Stoic"])
        context_map: Dict mapping labels to NP arrays (e.g., {"low": np.array([0.1])})
        """
        self.arm_names = arm_names
        self.context_map = context_map
        
        # Initialize Arms
        self.arms = [
            Arm(i, learner=NormalInverseGammaRegressor()) 
            for i in range(len(arm_names))
        ]
        
        # Initialize Agent
        self.agent = ContextualAgent(self.arms, ThompsonSampling())

    # Purpose: Given the context, pull an arm
    def get_decision(self, context_vector):
        """Takes the [stress, activity] array directly from the Evaluator."""
        arm_index, = self.agent.pull(context_vector)
        return arm_index, self.arm_names[arm_index]

    #Purpose: Update model with observed rewards given the arm pulled and observed context
    def give_feedback(self, arm_index, context_vector, reward):
        """Updates the model using the actual vector observed during the decision."""
        self.agent.select_for_update(arm_index).update(context_vector, reward)
        print(f"Model Updated: Arm {arm_index} got reward {reward}")
    

    def save_model(self, filename="misty_p01_brain.pkl"):
        """Saves the learned state of the bandit."""
        joblib.dump(self.agent, filename)
        print(f"Brain state saved to {filename}")

    def load_model(self, filename="misty_p01_brain.pkl"):
        """Loads a previously learned state."""
        if os.path.exists(filename):
            self.agent = joblib.load(filename)
            print(f"Brain state loaded from {filename}")
        else:
            print("No saved brain found. Starting from scratch.")