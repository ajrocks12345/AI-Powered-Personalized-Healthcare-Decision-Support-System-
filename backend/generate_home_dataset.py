import pandas as pd
import numpy as np
import random
import os
from utils import DISEASE_PROFILES

def generate_dataset():
    # Dynamically build features list from ALL disease profiles
    all_symptoms = set()
    for profile in DISEASE_PROFILES.values():
        for s in profile:
            all_symptoms.add(s)
    
    features = sorted(list(all_symptoms))
    disease_profiles = DISEASE_PROFILES

    rows = []
    samples_per_disease = 300
    
    # Feature mapping for profiles (if any legacy names exist)
    feature_map = {
        "nausea": "vomiting" # Example mapping
    }

    # Define systemic symptoms that should override localized ones
    systemic_symptoms = ["high_fever", "mild_fever", "fatigue", "lethargy", "chills", "weight_loss", "night_sweats"]
    localized_diseases = ["Athlete’s Foot", "Acne", "Dandruff", "Ingrown Toenail", "Nail Fungus", "Small Cut", "Minor Burn"]

    for disease, profile in disease_profiles.items():
        base_symptoms = [feature_map.get(s, s) for s in profile if feature_map.get(s, s) in features]
        
        for i in range(samples_per_disease):
            row = {f: 0 for f in features}
            row['Disease'] = disease
            
            # 1. CORE SYMPTOMS (from profile)
            if base_symptoms:
                # Vary the number of symptoms present in this sample
                current_count = random.randint(1, len(base_symptoms))
                selected = random.sample(base_symptoms, current_count)
                for s in selected:
                    row[s] = 1
            
            # 2. INTELLIGENT NOISE (Co-occurrence)
            # Systemic diseases can have random localized symptoms (e.g. Typhoid patient has itchy toes)
            # This teaches the model that "Systemic + Localized = Systemic"
            if disease not in localized_diseases and random.random() < 0.3:
                # Add one localized symptom as 'noise'
                localized_pool = ["itching", "toe_itching", "skin_rash", "skin_redness"]
                noise_s = random.choice(localized_pool)
                if noise_s in features:
                    row[noise_s] = 1
            
            # 3. NEGATIVE REINFORCEMENT
            # Localized diseases should NEVER have systemic symptoms in training data
            # (Ensures the model learns they are strictly localized)
            if disease in localized_diseases:
                for s in systemic_symptoms:
                    if s in row:
                        row[s] = 0
                
            rows.append(row)

    df = pd.DataFrame(rows)
    # Reorder columns to have Disease first
    cols = ['Disease'] + [c for c in df.columns if c != 'Disease']
    df = df[cols]
    
    output_path = 'backend/home_dataset_vectorized.csv'
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} samples across {len(disease_profiles)} diseases with {len(features)} features.")

if __name__ == "__main__":
    generate_dataset()
