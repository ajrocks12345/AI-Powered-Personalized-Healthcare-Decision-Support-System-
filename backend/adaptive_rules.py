# Adaptive Questioning Rules for Personalization

ADAPTIVE_RULES = {
    # (Profile Condition, Current Symptom) -> [Follow-up Symptoms to Check]
    
    ("Heart problems", "chest_pain"): ["shortness_of_breath", "dizziness", "sweating", "rapid_heartbeat"],
    ("Heart problems", "breathlessness"): ["chest_pain", "swelling", "fatigue"],
    
    ("Asthma", "cough"): ["wheezing", "breathlessness", "chest_tightness"],
    ("Asthma", "breathlessness"): ["wheezing", "cough", "phlegm"],
    
    ("Diabetes", "fatigue"): ["excessive_thirst", "frequent_urination", "blurred_and_distorted_vision"],
    ("Diabetes", "numbness"): ["muscle_weakness", "visual_disturbances"],
    
    ("High Blood Pressure", "headache"): ["nosebleeds", "visual_disturbances", "chest_pain"],
    
    # Generic Symptom Expansions (if not in profile but triggered)
    (None, "fever"): ["cough", "muscle_pain", "chills", "fatigue", "headache"],
    (None, "stomach_pain"): ["vomiting", "diarrhoea", "nausea", "bloating"],
    (None, "cough"): ["throat_irritation", "phlegm", "runny_nose", "congestion"]
}

# Allergy-based Recommendation Adjustments
ALLERGY_ADVICE = {
    "Aspirin": "Avoid aspirin-based pain relief; consult a doctor for alternatives like acetaminophen.",
    "Antibiotics": "Please ensure your doctor is aware of your antibiotic allergy before any prescription.",
    "NSAIDs": "Avoid non-steroidal anti-inflammatory drugs; consult for safe alternatives."
}

# Lifestyle-based Advice
LIFESTYLE_ADVICE = {
    "Smoking": "Given your smoking history, persistent respiratory symptoms require immediate professional evaluation.",
    "Alcohol": "Chronic alcohol use can exacerbate digestive issues; consider limiting intake during recovery.",
    "Poor Sleep": "Improving your sleep hygiene may help reduce the frequency of your fatigue and headaches."
}
