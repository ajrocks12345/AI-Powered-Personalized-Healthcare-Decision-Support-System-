from flask import Flask, request, jsonify, send_from_directory, send_file
import pickle
import pandas as pd
import numpy as np
import datetime
import os
import csv
import re
import json
import math
import requests
from thefuzz import fuzz
from fpdf import FPDF

app = Flask(__name__, static_folder='../frontend', static_url_path='')

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

# --- Medical Knowledge Base ---

DISEASE_PROFILES = {
    "Fungal infection": ["itching", "skin_rash", "nodal_skin_eruptions", "dischromic_patches"],
    "Allergy": ["continuous_sneezing", "shivering", "chills", "watering_from_eyes", "runny_nose", "itchy_eyes"],
    "GERD": ["stomach_pain", "acidity", "ulcers_on_tongue", "vomiting", "cough", "chest_pain", "sour_taste_in_mouth"],
    "Gastroenteritis": ["vomiting", "sunken_eyes", "dehydration", "diarrhoea", "stomach_pain"],
    "Migraine": ["headache", "blurred_and_distorted_vision", "stiff_neck", "visual_disturbances", "sensitivity_to_light", "sensitivity_to_sound", "vomiting"],
    "Chicken pox": ["itching", "skin_rash", "fatigue", "lethargy", "high_fever", "headache", "loss_of_appetite", "mild_fever", "swelled_lymph_nodes", "malaise", "red_spots_over_body"],
    "Common Cold": ["continuous_sneezing", "chills", "fatigue", "cough", "runny_nose", "congestion", "phlegm", "throat_irritation", "mild_fever"],
    "Acne": ["skin_rash", "pus_filled_pimples", "blackheads", "scurring"],
    "Minor Burn": ["burning_sensation", "skin_redness", "blister"],
    "Small Cut": ["bleeding", "skin_redness"],
    "Insect Bite": ["bite_mark", "itching", "swelling", "skin_redness"],
    "Sprain": ["swelling", "muscle_pain", "joint_pain", "stiff_neck"],
    "Sunburn": ["skin_redness", "burning_sensation", "fatigue", "mild_fever"],
    "Dehydration": ["fatigue", "sunken_eyes", "dehydration", "dark_urine", "visual_disturbances"],
    "Dog Bite": ["dog_bite", "bleeding", "swelling"],
    "Tonsillitis": ["throat_irritation", "swelled_lymph_nodes", "high_fever", "mild_fever"],
    "Fever": ["high_fever", "mild_fever", "sweating", "chills", "headache", "muscle_pain"],
    "Flu (Influenza)": ["high_fever", "chills", "muscle_pain", "fatigue", "headache", "cough", "sweating", "shivering", "runny_nose"],
    "Headache": ["headache", "visual_disturbances", "vomiting"],
    "Stomach Ache": ["stomach_pain", "burping"],
    "Food Poisoning": ["vomiting", "diarrhoea", "stomach_pain", "mild_fever"],
    "Acidity": ["acidity", "burning_sensation", "sour_taste_in_mouth", "burping"],
    "Indigestion": ["indigestion", "stomach_pain", "burping"],
    "Constipation": ["difficulty_passing_stool", "hard_stools", "stomach_pain", "indigestion"],
    "Cough": ["cough", "throat_irritation", "phlegm"],
    "Sore Throat": ["throat_irritation", "mild_fever", "headache"], 
    "Heat Exhaustion": ["sweating", "fatigue", "visual_disturbances", "headache", "vomiting", "dehydration", "high_fever"],
    "Eye Strain": ["eye_pain", "blurred_and_distorted_vision", "dry_eyes"],
    "Ear Infection (mild)": ["ear_pain", "mild_fever", "difficulty_hearing"],
    "Sinus Infection": ["sinus_pressure", "headache", "congestion", "runny_nose", "facial_pain"],
    "Appendicitis (early signs)": ["abdominal_pain_lower_right", "nausea", "vomiting", "mild_fever", "loss_of_appetite"],
    "Urinary Tract Infection (UTI)": ["burning_urination", "frequent_urination", "cloudy_urine", "pelvic_pain"],
    "Kidney Stones": ["severe_back_pain", "burning_urination", "vomiting", "hematuria"],
    "Gallstones": ["upper_abdominal_pain", "vomiting", "nausea", "pain_after_meals"],
    "Pancreatitis (mild signs)": ["upper_abdominal_pain", "nausea", "vomiting", "mild_fever"],
    "Irritable Bowel Syndrome (IBS)": ["abdominal_cramps", "bloating", "diarrhoea", "difficulty_passing_stool"],
    "Lactose Intolerance": ["bloating", "diarrhoea", "stomach_pain_after_dairy"],
    "Celiac Disease": ["diarrhoea", "bloating", "fatigue_after_gluten"],
    "Hemorrhoids (Piles)": ["rectal_pain", "bleeding_during_bowel_movement", "itching"],
    "Anal Fissure": ["pain_during_bowel_movement", "bleeding"],
    "Anemia": ["fatigue", "pale_skin", "visual_disturbances", "breathlessness"],
    "Low Blood Pressure": ["visual_disturbances", "fainting", "blurred_and_distorted_vision"],
    "High Blood Pressure": ["headache", "nosebleeds", "visual_disturbances"],
    "Hypoglycemia": ["shaking", "sweating", "confusion", "visual_disturbances"],
    "Hyperglycemia": ["excessive_thirst", "frequent_urination", "fatigue"],
    "Vitamin D Deficiency": ["bone_pain", "fatigue", "muscle_weakness"],
    "Vitamin B12 Deficiency": ["fatigue", "numbness_limbs", "muscle_weakness"],
    "Iron Deficiency": ["muscle_weakness", "pale_skin", "breathlessness"],
    "Gout": ["joint_pain", "swelling", "toe_redness"],
    "Arthritis (early signs)": ["joint_pain", "joint_stiffness", "swelling"],
    "Carpal Tunnel Syndrome": ["hand_numbness", "tingling", "wrist_pain"],
    "Sciatica": ["radiating_leg_pain", "numbness_limbs"],
    "Plantar Fasciitis": ["heel_pain", "heel_pain_morning"],
    "Tendinitis": ["joint_pain", "swelling"],
    "Frozen Shoulder": ["joint_stiffness", "limited_movement"],
    "Motion Vertigo": ["visual_disturbances", "balance_problems", "vomiting"],
    "Panic Attack": ["rapid_heartbeat", "chest_tightness", "sweating"],
    "Mild Depression": ["sadness", "fatigue", "loss_of_interest"],
    "Sleep Apnea": ["snoring", "fatigue", "sleep_disturbances"],
    "Restless Leg Syndrome": ["restless_legs", "discomfort_at_night"],
    "Bruxism": ["teeth_grinding", "jaw_pain", "headache"],
    "TMJ Disorder": ["jaw_pain", "jaw_clicking"],
    "Mouth Ulcers": ["mouth_ulcers", "difficulty_eating"],
    "Gum Infection (Gingivitis)": ["bleeding_gums", "swollen_gums", "bad_breath"],
    "Tooth Abscess": ["tooth_pain", "swelling", "mild_fever"],
    "Bad Breath (Halitosis)": ["bad_breath"],
    "Athlete’s Foot": ["toe_itching", "burning_sensation", "scaling_on_feet", "blister", "foot_odor"],
    "Dandruff": ["flaky_scalp", "itching", "dry_skin"],
    "Hair Loss (Alopecia)": ["hair_thinning", "patchy_hair_loss"],
    "Ingrown Toenail": ["toe_pain", "skin_redness", "swelling", "pus"],
    "Nail Fungus": ["nail_changes", "thick_nails", "brittle_nails"],
    "Hives (Urticaria)": ["red_welts", "itching", "burning_sensation"],
    "Jet Lag": ["fatigue", "sleep_disturbances", "irritability", "lack_of_concentration"],
    "Seasonal Affective Disorder": ["sadness", "fatigue", "lethargy", "sleep_disturbances"],
    "Typhoid": ["high_fever", "mild_fever", "fatigue", "muscle_weakness", "abdominal_pain", "headache", "loss_of_appetite", "constipation", "diarrhoea", "rose_spots", "chills"],
    "Jaundice": ["yellowish_skin", "dark_urine", "fatigue", "abdominal_pain", "vomiting", "yellowing_of_eyes"],
    "Measles": ["mild_fever", "high_fever", "cough", "runny_nose", "redness_of_eyes", "skin_rash", "fatigue"],
    "Mumps": ["swollen_parotid_glands", "jaw_pain", "mild_fever", "headache", "pain_during_chewing"],
    "Rubella": ["mild_fever", "skin_rash", "swelled_lymph_nodes", "joint_pain"],
    "Tuberculosis (early signs)": ["persistent_cough", "weight_loss", "night_sweats", "fatigue", "blood_in_sputum", "mild_fever"],
    "Whooping Cough": ["coughing_fits", "vomiting", "breathlessness", "whoop_sound_after_cough"],
    "Pneumonia": ["chest_pain", "cough", "mild_fever", "high_fever", "breathlessness", "fatigue", "chills"],
    "Bronchial Asthma": ["wheezing", "breathlessness", "chest_tightness", "cough"],
    "Hepatitis A": ["yellowish_skin", "fatigue", "vomiting", "abdominal_pain", "loss_of_appetite", "mild_fever"],
    "Hepatitis B": ["yellowish_skin", "dark_urine", "fatigue", "abdominal_discomfort", "joint_pain"],
    "Dengue Fever": ["high_fever", "headache", "joint_pain", "skin_rash", "muscle_pain", "pain_behind_the_eyes"],
    "Chikungunya": ["high_fever", "joint_pain", "headache", "fatigue", "skin_rash", "nausea"],
    "Leptospirosis": ["high_fever", "muscle_pain", "headache", "vomiting", "shivering", "redness_of_eyes"],
    "Ringworm": ["circular_rash", "scaly_skin", "itching", "red_skin_patches"],
    "Scabies": ["itching", "skin_bumps", "thin_burrow_lines_on_skin", "itching_at_night"],
    "Psoriasis": ["scaly_skin", "itching", "burning_sensation", "silver_scales", "dry_cracked_skin"],
    "Boils": ["pus_filled_pimples", "swelling", "skin_redness", "pain_in_site"],
    "Cellulitis": ["skin_redness", "swelling", "burning_sensation", "mild_fever", "tenderness"],
    "Tonsil Stones": ["bad_breath", "throat_irritation", "tonsil_white_spots", "difficulty_swallowing"],
    "Strep Throat": ["throat_irritation", "mild_fever", "swelled_lymph_nodes", "high_fever", "swallowing_difficulty", "headache"],
    "Laryngitis": ["hoarse_voice", "throat_irritation", "cough"],
    "Nasal Polyps": ["nasal_blockage", "loss_of_smell", "runny_nose"],
    "Hay Fever": ["continuous_sneezing", "runny_nose", "itchy_eyes"],
    "Dehydration Headache": ["headache", "dehydration", "fatigue"],
    "Heat Stroke": ["high_fever", "confusion", "rapid_pulse"],
    "Hypothermia": ["shivering", "confusion", "breathlessness"],
    "Traveler’s Diarrhea": ["diarrhoea", "stomach_pain", "vomiting"],
    "Gallbladder Infection": ["stomach_pain", "mild_fever", "vomiting"],
    "Pancreatic Infection": ["stomach_pain", "vomiting", "mild_fever"],
    "Hiccups": ["hiccups"],
    "Dry Throat": ["dry_throat", "throat_irritation"],
    "Minor Muscle Cramp": ["muscle_cramping", "muscle_pain"],
    "Chapped Lips": ["chapped_lips", "dry_lips"]
}

DISEASE_DESCRIPTIONS = {
    "Fungal infection": "A skin disease caused by a fungus. Common types include athlete's foot, jock itch, and ringworm.",
    "Allergy": "The body's immune system reacting to a normally harmless substance like pollen, dust, or certain foods.",
    "GERD": "Gastroesophageal reflux disease occurs when stomach acid frequently flows back into the tube connecting your mouth and stomach.",
    "Gastroenteritis": "Often called stomach flu, it's an inflammation of the stomach and intestines, typically caused by a virus or bacteria.",
    "Migraine": "A type of headache characterized by severe throbbing pain or a pulsing sensation, usually on one side of the head.",
    "Chicken pox": "A highly contagious viral infection causing an itchy, blister-like rash on the skin.",
    "Common Cold": "A viral infection of your nose and throat (upper respiratory tract).",
    "Acne": "A skin condition that occurs when your hair follicles become plugged with oil and dead skin cells.",
    "Minor Burn": "Damage to the skin caused by heat, electricity, or chemicals, affecting only the top layer.",
    "Small Cut": "A minor break in the skin's surface, usually caused by a sharp object.",
    "Insect Bite": "A painful or itchy skin reaction caused by the saliva or venom of an insect.",
    "Sprain": "A stretching or tearing of ligaments, the tough bands of fibrous tissue that connect two bones together in your joints.",
    "Sunburn": "Skin damage from overexposure to ultraviolet (UV) radiation from the sun.",
    "Dehydration": "A condition caused by the excessive loss of water from the body.",
    "Dog Bite": "An injury caused by the teeth of a dog, requiring immediate cleaning and potentially medical attention.",
    "Tonsillitis": "Inflammation of the tonsils, the two oval-shaped pads of tissue at the back of the throat.",
    "Fever": "A temporary increase in average body temperature, often due to an illness.",
    "Flu (Influenza)": "A common viral infection that can be deadly, especially in high-risk groups.",
    "Headache": "Pain or discomfort in the head or face area.",
    "Stomach Ache": "Pain or discomfort in the abdominal region.",
    "Food Poisoning": "Illness caused by eating contaminated, spoiled, or toxic food.",
    "Acidity": "A state of having excess acid in the stomach, often causing heartburn.",
    "Indigestion": "Pain or discomfort in the stomach associated with difficulty in digesting food.",
    "Constipation": "A condition in which there is difficulty in emptying the bowels, usually associated with hardened feces.",
    "Cough": "A sudden, forceful hack to clear breathing passages of irritants or mucus.",
    "Sore Throat": "Pain, scratchiness or irritation of the throat that often worsens when you swallow.",
    "Heat Exhaustion": "A condition whose symptoms may include heavy sweating and a rapid pulse, a result of your body overheating.",
    "Eye Strain": "A common condition that occurs when your eyes get tired from intense use.",
    "Ear Infection (mild)": "Inflammation or infection of the ear, often causing pain and temporary hearing loss.",
    "Sinus Infection": "Inflammation or swelling of the tissue lining the sinuses.",
    "Appendicitis (early signs)": "Inflammation of the appendix, a finger-shaped pouch that projects from your colon.",
    "Urinary Tract Infection (UTI)": "An infection in any part of your urinary system — your kidneys, ureters, bladder and urethra.",
    "Kidney Stones": "Hard deposits made of minerals and salts that form inside your kidneys.",
    "Gallstones": "Hardened deposits of digestive fluid that can form in your gallbladder.",
    "Pancreatitis (mild signs)": "Inflammation of the pancreas, a long, flat gland that sits tucked behind the stomach in the upper abdomen.",
    "Irritable Bowel Syndrome (IBS)": "A common disorder that affects the large intestine.",
    "Lactose Intolerance": "An inability to fully digest sugar (lactose) in dairy products.",
    "Celiac Disease": "An immune reaction to eating gluten, a protein found in wheat, barley, and rye.",
    "Hemorrhoids (Piles)": "Swollen and inflamed veins in the rectum and anus that cause discomfort and bleeding.",
    "Anal Fissure": "A small tear in the thin, moist tissue (mucosa) that lines the anus.",
    "Anemia": "A condition in which you lack enough healthy red blood cells to carry adequate oxygen to your body's tissues.",
    "Low Blood Pressure": "A condition where blood pressure is lower than normal, which can cause fainting or dizziness.",
    "High Blood Pressure": "A condition in which the force of the blood against the artery walls is too high.",
    "Hypoglycemia": "A condition caused by a very low level of blood sugar (glucose), your body's main energy source.",
    "Hyperglycemia": "An excess of glucose in the bloodstream, often associated with diabetes.",
    "Vitamin D Deficiency": "A condition where you don't have enough vitamin D in your body, affecting bone health.",
    "Vitamin B12 Deficiency": "A condition where your body doesn't have enough healthy red blood cells because of a lack of vitamin B12.",
    "Iron Deficiency": "A condition in which blood lacks adequate healthy red blood cells due to insufficient iron.",
    "Gout": "A form of inflammatory arthritis characterized by recurrent attacks of a red, tender, hot, and swollen joint.",
    "Arthritis (early signs)": "Swelling and tenderness of one or more joints.",
    "Carpal Tunnel Syndrome": "A condition that causes numbness, tingling, or weakness in your hand because of pressure on your median nerve.",
    "Sciatica": "Pain radiating along the sciatic nerve, which runs down one or both legs from the lower back.",
    "Plantar Fasciitis": "Inflammation of a thick band of tissue that runs across the bottom of each foot and connects your heel bone to your toes.",
    "Tendinitis": "Inflammation or irritation of a tendon, a thick fibrous cord that attaches muscle to bone.",
    "Frozen Shoulder": "A condition characterized by stiffness and pain in your shoulder joint.",
    "Motion Vertigo": "A sensation of spinning or dizziness caused by motion.",
    "Panic Attack": "A sudden episode of intense fear that triggers severe physical reactions when there is no real danger.",
    "Mild Depression": "A mental health disorder characterized by persistently depressed mood or loss of interest in activities.",
    "Sleep Apnea": "A potentially serious sleep disorder in which breathing repeatedly stops and starts.",
    "Restless Leg Syndrome": "A condition that causes an uncontrollable urge to move your legs, usually because of an uncomfortable sensation.",
    "Bruxism": "A condition in which you grind, gnash or clench your teeth.",
    "TMJ Disorder": "Pain and compromised movement of the jaw joint and the surrounding muscles.",
    "Mouth Ulcers": "Small, painful sores that develop in your mouth or at the base of your gums.",
    "Gum Infection (Gingivitis)": "A common and mild form of gum disease that causes irritation, redness and swelling.",
    "Tooth Abscess": "A pocket of pus that's caused by a bacterial infection in a tooth.",
    "Bad Breath (Halitosis)": "An unpleasant odor from the breath.",
    "Athlete’s Foot": "A fungal skin infection that usually begins between the toes.",
    "Dandruff": "A skin condition that mainly affects the scalp, causing flaky skin and itching.",
    "Hair Loss (Alopecia)": "A condition where hair falls out from the scalp or elsewhere on the body.",
    "Ingrown Toenail": "A condition in which the corner or side of a toenail grows into the soft flesh.",
    "Nail Fungus": "A common condition that begins as a white or yellow spot under the tip of your fingernail or toenail.",
    "Hives (Urticaria)": "Red, itchy welts that result from a skin reaction.",
    "Jet Lag": "A temporary sleep problem that can affect anyone who quickly travels across several time zones.",
    "Seasonal Affective Disorder": "A type of depression that's related to changes in seasons.",
    "Typhoid": "A bacterial infection that can spread throughout the body, affecting many organs.",
    "Jaundice": "A condition in which the skin, sclera (whites of the eyes) and mucous membranes turn yellow.",
    "Measles": "A highly contagious viral infection that's serious for small children.",
    "Mumps": "A viral infection that primarily affects saliva-producing (parotid) glands that are located near your ears.",
    "Rubella": "A contagious viral infection best known by its distinctive red rash.",
    "Tuberculosis (early signs)": "A serious infectious disease that mainly affects your lungs.",
    "Whooping Cough": "A highly contagious respiratory tract infection.",
    "Pneumonia": "An infection that inflames the air sacs in one or both lungs.",
    "Bronchial Asthma": "A condition in which your airways narrow and swell and may produce extra mucus.",
    "Hepatitis A": "A highly contagious liver infection caused by the hepatitis A virus.",
    "Hepatitis B": "A serious liver infection caused by the hepatitis B virus.",
    "Dengue Fever": "A mosquito-borne viral disease occurring in tropical and subtropical areas.",
    "Chikungunya": "A viral disease transmitted to humans by infected mosquitoes.",
    "Leptospirosis": "A bacterial disease that affects humans and animals, spread through the urine of infected animals.",
    "Ringworm": "A highly contagious fungal infection of the skin or scalp.",
    "Scabies": "An itchy skin condition caused by a tiny burrowing mite.",
    "Psoriasis": "A skin disorder that causes skin cells to multiply up to 10 times faster than normal.",
    "Boils": "A painful, pus-filled bump under the skin caused by infected hair follicles.",
    "Cellulitis": "A common, potentially serious bacterial skin infection.",
    "Tonsil Stones": "Hard, white or yellow formations that are located on or within the tonsils.",
    "Strep Throat": "A bacterial infection that can make your throat feel sore and scratchy.",
    "Laryngitis": "An inflammation of your voice box (larynx) from overuse, irritation or infection.",
    "Nasal Polyps": "Soft, painless, noncancerous growths on the lining of your nasal passages or sinuses.",
    "Hay Fever": "An allergic response causing itchy, watery eyes, sneezing and other similar symptoms.",
    "Dehydration Headache": "A headache caused by the body not having enough fluids.",
    "Heat Stroke": "The most serious heat-related illness, occurring when the body becomes unable to control its temperature.",
    "Hypothermia": "A medical emergency that occurs when your body loses heat faster than it can produce heat.",
    "Traveler’s Diarrhea": "A digestive tract disorder that commonly causes loose stools and abdominal cramps.",
    "Gallbladder Infection": "Inflammation of the gallbladder, often caused by gallstones.",
    "Pancreatic Infection": "Inflammation of the pancreas that can lead to infection.",
    "Hiccups": "A series of involuntary contractions of the diaphragm followed by sudden closure of the vocal cords.",
    "Dry Throat": "A common condition where the throat feels parched, often caused by dry air or minor dehydration.",
    "Minor Muscle Cramp": "A sudden, involuntary contraction of one or more muscles, usually harmless.",
    "Chapped Lips": "Dry, scaly, or cracked skin on the lips, common in dry or cold weather."
}

MINOR_DISEASES = [
    "Hiccups", "Dry Throat", "Minor Muscle Cramp", "Chapped Lips", 
    "Athlete’s Foot", "Acne", "Dandruff", "Common Cold", "Small Cut", "Minor Burn"
]

AMBIGUOUS_SYMPTOMS = {
    "back pain": ["muscle_pain", "severe_back_pain"],
    "back ache": ["muscle_pain", "severe_back_pain"],
    "backache": ["muscle_pain", "severe_back_pain"],
    "back hurts": ["muscle_pain", "severe_back_pain"],
    "stomach pain": ["stomach_pain", "abdominal_pain_lower_right", "upper_abdominal_pain"],
    "stomach ache": ["stomach_pain", "abdominal_pain_lower_right", "upper_abdominal_pain"],
    "stomach hurts": ["stomach_pain", "abdominal_pain_lower_right", "upper_abdominal_pain"],
    "fever": ["mild_fever", "high_fever"],
    "temperature": ["mild_fever", "high_fever"],
    "pain in stomach": ["stomach_pain", "abdominal_pain_lower_right", "upper_abdominal_pain"]
}

def is_greeting(text):
    """Checks if the text is primarily a greeting using word boundaries."""
    greetings = ["hello", "hi", "hii", "hey", "greetings", "good morning", "good evening"]
    text = text.lower().strip()
    for greet in greetings:
        if re.search(r'\b' + re.escape(greet) + r'\b', text):
            if len(text.split()) < 3:
                return True
    return False

def clean_text(text):
    """Cleans user input text."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text

def extract_symptoms(text, feature_names):
    """Extracts symptoms from user text using fuzzy matching."""
    text_clean = clean_text(text)
    input_vector = np.zeros(len(feature_names))
    extracted_set = set()

    keyword_rules = {
        "abdominal_pain_lower_right": ["lower right stomach pain", "pain in lower right abdomen", "right side stomach hurts", "lower right side pain", "pain in lower right side", "pain in lower right stomach", "lower right pain", "lower right side stomach", "pain in my lower right stomach", "stomach pain in my right side", "hurts on the right side of my stomach"],
        "upper_abdominal_pain": ["upper stomach pain", "pain in upper abdomen", "pain below ribs", "stomach hurts high up", "upper belly pain", "pain in upper stomach", "high stomach pain", "upper gut pain"],
        "stomach_pain": ["stomach", "tummy", "belly", "abdomen", "gut", "tummy ache", "belly ache", "abdominal pain", "cramps in stomach", "stomach cramps", "abdominal cramps", "stomach hurts"],
        "abdominal_pain": ["stomach pain", "abdominal pain", "cramps", "belly pain", "stomach ache", "belly ache"],
        "headache": ["head", "headache", "migraine", "temple", "head hurts", "pain in head", "splitting headache", "throbbing head", "head is aching", "pressure in head"],
        "vomiting": ["vomit", "vomiting", "vomitting", "thrown up", "throwing up", "puke", "puking", "nausea", "nauseous", "sick to my stomach", "feeling sick", "emesis", "heaving", "upset stomach"],
        "diarrhoea": ["diarrhea", "loose motion", "stomach upset", "runny stomach", "watery stools", "frequent bathroom trips"],
        "ear_pain": ["ear ache", "ear pain", "inside of ear hurts", "ear discomfort", "aching ear", "pain in my ear"],
        "burning_urination": ["burning while peeing", "pain when urinating", "hurts to pee", "burning sensation during urination", "painful urination", "burns when i pee", "burns while peeing", "stinging during urination"],
        "frequent_urination": ["need to pee often", "frequent urination", "peeing a lot", "going to bathroom frequently", "excess urination", "gotta go often", "constantly peeing"],
        "toe_redness": ["red toe", "big toe hurts", "swollen toe", "inflamed toe", "toe is red", "redness in toe"],
        "congestion": ["blocked nose", "stuffy", "congestion", "sinus", "cant breathe through nose", "nasal congestion", "congested", "nose is blocked", "nose blocked", "nose is stuffy"],
        "continuous_sneezing": ["sneeze", "sneezing", "cant stop sneezing", "fits of sneezing"],
        "throat_irritation": ["sore throat", "throat", "swallowing", "throat pain", "swelling in throat", "hurts to swallow", "scratchy throat", "throat is sore"],
        "cough": ["cough", "coughing", "dry cough", "wet cough", "hacking cough", "persistent cough"],
        "chills": ["shivering", "feeling cold", "chills", "shiver", "cold shivers"],
        "fatigue": ["tired", "exhausted", "fatigue", "weakness", "no energy", "drained", "weak", "faint", "sleepy", "drowsy", "week", "feeling low", "burnt out", "tiredness"],
        "muscle_pain": ["body ache", "muscle", "aches", "leg hurts", "arm hurts", "pain in muscle", "muscle pain", "body pain", "muscle ache", "aching legs", "aching arms", "pain in leg", "pain in arm", "legs are hurting", "arms are hurting", "my leg hurts", "my arm hurts", "leg pain", "arm pain", "normal muscle ache", "mild muscle pain"],
        "severe_back_pain": ["severe back pain", "excruciating back pain", "sharp back pain", "lower back pain", "upper back pain"],
        "joint_pain": ["joint", "knee", "elbow", "shoulder", "pain in joints", "aching joints", "stiff joints", "knee pain", "elbow pain", "shoulder pain", "joint hurts"],
        "acidity": ["acid", "heartburn", "burning in chest", "reflux", "acidic", "burning stomach", "gerd"],
        "visual_disturbances": ["dizzy", "dizziness", "spinning", "lightheaded", "giddiness", "vertigo", "feeling faint"],
        "blurred_and_distorted_vision": ["blurred", "blurry", "distorted", "vision is fuzzy", "cant see clear", "spots in vision", "obscured vision"],
        "itching": ["itchy", "scratching", "irritation on skin", "itchness", "skin is itching"],
        "skin_rash": ["rash", "red spots", "breakout", "skin irritation", "rash on skin"],
        "pus_filled_pimples": ["pimple", "zit", "acne", "breakout", "pus", "whiteheads"],
        "burning_sensation": ["burning", "fire", "scalded", "hot pan", "stinging", "burning feeling", "burning sensation"],
        "bleeding": ["blood", "bleeding", "cut", "wound", "scrape", "open sore", "oozing blood"],
        "swelling": ["swelling", "swollen", "lump", "bump", "inflamed", "puffiness", "enlarged"],
        "skin_redness": ["red skin", "redness", "sunburn", "tanned", "inflamed skin", "skin is red"],
        "bite_mark": ["insect bite", "bug bite", "mosquito bite", "spider bite", "bee string", "wasp sting", "ant bite", "stung", "sting", "bite mark"],
        "dog_bite": ["dog bite", "puppy bite", "canine bite", "dog bit me"],
        "blister": ["blister", "bubble", "fluid filled", "pustule"],
        "dehydration": ["thirsty", "dry mouth", "dehydration", "need water", "very thirsty"],
        "toe_itching": ["itchy toes", "itching toes", "itch between toes", "itching between toes", "toes are itchy", "toes itch", "itchy between toes", "feet itching", "itching feet"],
        "high_fever": ["high fever", "burning up", "very hot body", "running a high fever", "intense fever", "high temp", "severe fever", "very high temperature", "burning with fever"],
        "mild_fever": ["mild fever", "little fever", "low grade fever", "warm body", "slightly hot", "normal fever", "slight temperature", "mild temperature"],
        "loss_of_appetite": ["not hungry", "lost appetite", "cant eat", "dont want to eat", "no hunger", "loss of appetite", "not feeling hungry"],
        "loss_of_smell": ["cant smell", "lost sense of smell", "smell is gone", "nose doesnt work", "anosmia"],
        "indigestion": ["indigestion", "bloated", "bloating", "gas", "fullness", "dyspepsia", "feeling full", "heavy stomach"],
        "sunken_eyes": ["eyes are sunken", "dark circles", "eyes look deep", "hollow eyes"],
        "lethargy": ["lazy", "lethargic", "no motivation", "sluggish", "listless"],
        "stiff_neck": ["neck is stiff", "neck pain", "cant move neck", "stiff neck", "neck ache"],
        "water_from_eyes": ["watery eyes", "eyes are watering", "teary eyes", "crying eyes"],
        "breathlessness": ["short of breath", "cant breathe", "breathless", "hard to breathe", "shortness of breath", "gasping", "trouble breathing"],
        "chest_pain": ["chest pain", "pain in chest", "chest hurts", "aching chest", "tightness in chest"],
        "phlegm": ["phlegm", "mucus", "spitting up", "congested throat"],
        "sinus_pressure": ["sinus pain", "sinus pressure", "forehead pressure", "sinus ache"],
        "sweating": ["sweat", "sweating", "perspiring", "heavy sweating", "night sweats", "dripping sweat"],
        "sensitivity_to_light": ["light sensitivity", "bright lights hurt", "photophobia", "squinting in light", "eyes sensitive to light"],
        "sensitivity_to_sound": ["sound sensitivity", "noise hurts", "loud noises bother me", "phonophobia"],
        "sour_taste_in_mouth": ["sour taste", "metallic taste", "bad taste in mouth", "bitter taste", "acid taste"],
        "burping": ["burp", "burping", "belching", "gas coming up", "eructation"],
        "hard_stools": ["hard poop", "hard stool", "dry stool", "pellet stool"],
        "constipation": ["constipation", "cant poop", "difficulty passing stool", "hard stool"],
        "difficulty_passing_stool": ["cant poop", "difficult to pass", "constipated", "constipation", "straining for stool", "hard to go"],
        "itchy_eyes": ["eyes itch", "itchy eyes", "scratchy eyes", "irritation in eyes"],
        "dark_urine": ["dark pee", "dark urine", "brown urine", "concentrated urine", "orange urine"],
        "eye_pain": ["eye hurts", "pain in eye", "aching eyes", "eye strain", "eyes are hurting"],
        "dry_eyes": ["dry eyes", "gritty eyes", "eyes feel dry", "low tears"],
        "difficulty_hearing": ["cant hear well", "muffled hearing", "hearing loss", "clogged ear", "deafness", "hard of hearing"],
        "facial_pain": ["face hurts", "facial pain", "pain in cheeks", "sinus pain", "face pressure"],
        "joint_stiffness": ["stiff joints", "hard to move joints", "joint stiffness"],
        "hand_numbness": ["hands are numb", "cant feel my fingers", "numbness in palm"],
        "tingling": ["tingling sensation", "pins and needles", "prickly feeling"],
        "wrist_pain": ["wrist hurts", "pain in wrist", "aching wrist"],
        "radiating_leg_pain": ["pain down leg", "shooting pain in leg", "sciatica pain"],
        "heel_pain": ["heel hurts", "pain in heel", "bottom of foot hurts"],
        "heel_pain_morning": ["heel hurts in morning", "pain when first walking", "morning foot pain"],
        "limited_movement": ["cant move well", "limited range of motion", "stiffness in movement"],
        "balance_problems": ["balance issues", "unsteady", "cant walk straight", "off balance"],
        "rapid_heartbeat": ["heart racing", "palpitations", "fast heart rate", "heart is pounding"],
        "chest_tightness": ["tight chest", "chest feels crushed", "pressure on chest"],
        "sadness": ["feeling sad", "depressed", "persistent sadness", "low mood"],
        "loss_of_interest": ["lost interest", "dont care about things", "no motivation", "anhedonia"],
        "snoring": ["snoring", "loud snoring", "snorting in sleep"],
        "sleep_disturbances": ["cant sleep", "poor sleep quality", "waking up at night", "insomnia"],
        "restless_legs": ["need to move legs", "legs feel jumpy", "restless legs at night"],
        "discomfort_at_night": ["cant get comfortable", "tossing and turning", "discomfort in bed"],
        "teeth_grinding": ["grinding teeth", "jaw hurts in morning", "bruxism"],
        "jaw_clicking": ["jaw clicks", "clicking sound when eating", "jaw pops"],
        "mouth_ulcers": ["mouth sore", "canker sore", "ulcer in mouth"],
        "bleeding_gums": ["gums bleed", "blood when brushing", "bleeding gums"],
        "swollen_gums": ["gums are swollen", "puffy gums", "inflamed gums"],
        "bad_breath": ["smelly breath", "bad breath", "halitosis", "mouth smells bad"],
        "flaky_scalp": ["dandruff", "flaky scalp", "white flakes in hair"],
        "hair_thinning": ["hair loss", "hair is thinning", "losing hair"],
        "patchy_hair_loss": ["bald spots", "patchy hair loss", "hair falling out in clumps"],
        "ingrown_toenail": ["ingrown nail", "toe nail hurts", "toe is infected"],
        "nail_changes": ["yellow nails", "thick nails", "brittle nails", "nail fungus"],
        "red_welts": ["hives", "red welts", "raised itchy rash"],
        "yellowish_skin": ["yellow skin", "jaundice", "skin is yellowing", "yellow eyes"],
        "persistent_cough": ["cough wont go away", "persistent cough", "constant coughing"],
        "weight_loss": ["losing weight", "unexplained weight loss", "getting thinner"],
        "night_sweats": ["sweating at night", "waking up drenched", "night sweats"],
        "coughing_fits": ["uncontrolled coughing", "coughing fits", "cant stop coughing"],
        "wheezing": ["wheezing", "whistling sound when breathing"],
        "abdominal_discomfort": ["stomach discomfort", "vague abdominal pain", "stomach feels off"],
        "circular_rash": ["ring rash", "circular rash", "round red spot", "ringworm rash"],
        "scaling_on_feet": ["scaling on feet", "peeling feet", "skin peeling between toes", "dry scaly feet"],
        "foot_odor": ["smelly feet", "foot odor", "feet smell", "stinky feet", "feet are smelly"],
        "scaly_skin": ["scaly skin", "peeling skin", "flaky skin rash", "skin is scaly"],
        "rose_spots": ["rose spots", "pink spots on stomach", "pink rash", "spots on chest"],
        "skin_bumps": ["small bumps on skin", "skin blisters", "tiny bumps"],
        "swollen_parotid_glands": ["swollen glands near ears", "puffy cheeks", "swelling in parotid"],
        "pain_during_chewing": ["hurts to chew", "pain while chewing", "pain when eating"],
        "whoop_sound_after_cough": ["whoop sound", "whooping cough", "intense coughing with whooping sound"],
        "blood_in_sputum": ["coughing up blood", "blood in mucus", "bloody phlegm"],
        "pain_behind_the_eyes": ["eye socket pain", "pain behind eyes", "eye pressure"],
        "silver_scales": ["silver scales", "silvery flakes", "silvery patches on skin"],
        "itching_at_night": ["itching worse at night", "itchy in bed", "night time itching"],
        "thin_burrow_lines_on_skin": ["burrow lines", "track marks on skin", "tiny squiggly lines on skin"],
        "difficulty_swallowing": ["hurts to swallow", "hard to swallow", "can't swallow easily"],
        "tonsil_white_spots": ["white spots on tonsils", "tonsil debris", "white lumps in throat"],
        "hoarse_voice": ["lost voice", "hoarse", "raspy voice", "voice is croaky"],
        "nasal_blockage": ["nasal blockage", "stopped up nose", "cant breathe through nose"],
        "rapid_pulse": ["fast pulse", "racing pulse", "high heart rate"],
        "hiccups": ["hiccups", "hiccuping", "hiccupping", "hiccup"],
        "dry_throat": ["dry throat", "throat feels dry", "parched throat"],
        "muscle_cramping": ["muscle cramp", "stomach cramp", "cramp in muscle", "muscle is cramping", "cramping"],
        "chapped_lips": ["chapped lips", "dry lips", "cracked lips", "peeling lips"]
    }

    def has_keywords(k_list, text):
        for k in k_list:
            if " " in k:
                words = k.split()
                flex_pattern = r"\b" + r"\s+(?:is\s+|are\s+|am\s+|feel\s+|feels\s+|my\s+|the\s+)?".join([re.escape(w) for w in words]) + r"\b"
                if re.search(flex_pattern, text, re.IGNORECASE):
                    return True
            pattern = rf"{k}|{k}ing|{k}s|{k}ed|{k}es"
            if len(k) > 3 and k.endswith(('t', 'p', 'n', 'm', 'g')):
                 pattern += f"|{k}{k[-1]}ing"
            if re.search(r'\b' + pattern + r'\b', text, re.IGNORECASE):
                return True
        return False

    def is_valid_match(feature, text):
        if feature == "bite_mark":
            if not has_keywords(["insect", "bug", "mosquito", "spider", "bee", "wasp", "ant"], text):
                return False
            if not has_keywords(["bite", "bit", "bitten", "stung", "sting"], text):
                return False
        if feature == "dog_bite":
            if not has_keywords(["dog", "puppy", "hound", "canine"], text):
                return False
            if not has_keywords(["bite", "bit", "bitten", "snap"], text):
                return False
        return True

    extracted_set = set()
    for feature, keywords in keyword_rules.items():
        if has_keywords(keywords, text_clean):
            if is_valid_match(feature, text_clean):
                if feature in feature_names:
                    extracted_set.add(feature)
                    continue
                    
        # Smart fuzzy matching using token_set_ratio on the whole text
        best_match_ratio = 0
        for k in keywords:
            ratio = fuzz.token_set_ratio(text_clean, k)
            if ratio > best_match_ratio:
                best_match_ratio = ratio
                
        if best_match_ratio >= 85 and is_valid_match(feature, text_clean):
            if feature in feature_names:
                extracted_set.add(feature)

    THRESHOLD = 80
    for i, symptom in enumerate(feature_names):
        if symptom in extracted_set:
            input_vector[i] = 1
            continue
        symptom_clean = symptom.strip().lower().replace('_', ' ')
        if symptom_clean in text_clean or fuzz.token_set_ratio(symptom_clean, text_clean) >= THRESHOLD:
             input_vector[i] = 1
             extracted_set.add(symptom)
    return input_vector.reshape(1, -1), list(extracted_set)

def get_precautions(disease):
    """Returns a list of precautions for the given disease."""
    disease = disease.strip()
    precautions_db = {
        "Fungal infection": ["Keep the affected area clean and dry", "Use antifungal creams", "Avoid sharing personal items"],
        "Allergy": ["Avoid allergens", "Take antihistamines", "Keep windows closed during pollen season"],
        "GERD": ["Avoid spicy foods", "Eat smaller meals", "Don't lie down immediately after eating"],
        "Gastroenteritis": ["Stay hydrated", "Rest your stomach", "Avoid dairy and high-fat foods"],
        "Migraine": ["Rest in a quiet, dark room", "Apply cold or warm compresses", "Take pain relievers"],
        "Chicken pox": ["Avoid scratching", "Use calamine lotion", "Rest and isolate"],
        "Common Cold": ["Stay hydrated", "Rest", "Gargle with salt water", "Use a humidifier"],
        "Acne": ["Wash your face twice daily", "Use non-comedogenic products", "Avoid popping pimples"],
        "Minor Burn": ["Cool the burn under cool (not cold) running water for 10-20 mins", "Remove tight items", "Apply aloe vera gel"],
        "Small Cut": ["Apply pressure to stop bleeding", "Clean with water", "Cover with a sterile bandage"],
        "Insect Bite": ["Wash with soap and water", "Apply a cold pack", "Avoid scratching"],
        "Sprain": ["Rest the injured part", "Ice the area", "Compress with a bandage", "Elevate the limb"],
        "Sunburn": ["Get out of the sun", "Take cool baths", "Apply aloe vera", "Drink extra water"],
        "Dehydration": ["Drink plenty of water or ORS", "Rest in a cool place", "Eat water-rich fruits"],
        "Dog Bite": ["Wash with soap and water", "Apply pressure to stop bleeding", "Seek medical attention for rabies risk"],
        "Tonsillitis": ["Gargle with warm salt water", "Drink warm liquids", "Rest your voice"],
        "Fever": ["Drink plenty of fluids", "Get plenty of rest", "Take over-the-counter fever reducers"],
        "Flu (Influenza)": ["Rest and stay home", "Drink fluids", "Take fever reducers", "Use steam for congestion"],
        "Headache": ["Rest in a quiet, dark room", "Stay hydrated", "Apply a cold compress"],
        "Stomach Ache": ["Apply a warm heating pad", "Sip clear fluids", "Rest"],
        "Food Poisoning": ["Drink small sips of water or ORS", "Rest", "Eat bland foods (bananas, rice)"],
        "Acidity": ["Eat smaller meals", "Avoid lying down after meals", "Avoid spicy/oily foods"],
        "Indigestion": ["Eat slowly and chew thoroughly", "Avoid heavy meals late at night", "Try ginger tea"],
        "Constipation": ["Increase fiber intake", "Drink plenty of water", "Exercise regularly"],
        "Cough": ["Use cough drops or honey", "Stay hydrated", "Use a humidifier"],
        "Sore Throat": ["Gargle with warm salt water", "Drink warm liquids with honey", "Rest your voice"],
        "Heat Exhaustion": ["Move to a cool place", "Drink cool water", "Loosen tight clothing"],
        "Eye Strain": ["Use the 20-20-20 rule", "Adjust screen lighting", "Take frequent breaks from screens"],
        "Ear Infection (mild)": ["Apply a warm compress", "Rest", "Keep the ear dry"],
        "Sinus Infection": ["Apply warm compresses", "Stay hydrated", "Use saline nasal sprays"],
        "Appendicitis (early signs)": ["Do not take laxatives", "Do not eat or drink", "Seek emergency medical care immediately"],
        "Urinary Tract Infection (UTI)": ["Drink plenty of water", "Avoid caffeine", "Consult a doctor for antibiotics"],
        "Kidney Stones": ["Drink plenty of water", "Take pain relievers", "Seek medical help if pain is severe"],
        "Gallstones": ["Avoid fatty and fried foods", "Eat smaller meals", "Consult a doctor if pain persists"],
        "Pancreatitis (mild signs)": ["Stop eating solid food briefly", "Stay hydrated", "Consult a doctor immediately"],
        "Irritable Bowel Syndrome (IBS)": ["Identify trigger foods", "Increase fiber slowly", "Manage stress"],
        "Lactose Intolerance": ["Avoid dairy products", "Try lactose-free milk", "Use lactase supplements"],
        "Celiac Disease": ["Adopt a strict gluten-free diet", "Read food labels carefully", "Avoid cross-contamination"],
        "Hemorrhoids (Piles)": ["Eat high-fiber foods", "Drink plenty of water", "Try sitz baths"],
        "Anal Fissure": ["Eat high-fiber foods", "Drink water to soften stool", "Try sitz baths"],
        "Anemia": ["Eat iron-rich foods (lean meat, spinach)", "Incorporate Vitamin C", "Get plenty of rest"],
        "Low Blood Pressure": ["Increase salt intake slightly", "Drink more water", "Stand up slowly"],
        "High Blood Pressure": ["Reduce salt intake", "Eat a heart-healthy diet", "Manage stress"],
        "Hypoglycemia": ["Eat 15g of fast-acting carbs", "Wait 15 mins and recheck", "Eat a balanced meal afterward"],
        "Hyperglycemia": ["Stay hydrated", "Exercise regularly", "Follow your diabetes management plan"],
        "Vitamin D Deficiency": ["Increase sun exposure safely", "Eat Vitamin D rich foods", "Consult about supplements"],
        "Vitamin B12 Deficiency": ["Eat B12 rich foods (meat, dairy, eggs)", "Consult about B12 supplements"],
        "Iron Deficiency": ["Eat lean red meat and leafy greens", "Avoid tea/coffee with meals", "Get rest"],
        "Gout": ["Drink plenty of water", "Avoid high-purine foods (red meat)", "Avoid alcohol"],
        "Arthritis (early signs)": ["Perform gentle low-impact exercises", "Maintain a healthy weight", "Use heat/cold therapy"],
        "Carpal Tunnel Syndrome": ["Wear a wrist splint at night", "Take breaks from repetitive tasks", "Do gentle wrist stretches"],
        "Sciatica": ["Apply ice packs/heat", "Do gentle back stretches", "Maintain good posture"],
        "Plantar Fasciitis": ["Wear supportive shoes", "Stretch calves and feet", "Use ice on the heel"],
        "Tendinitis": ["Rest the affected area", "Apply ice packs", "Use a compression wrap"],
        "Frozen Shoulder": ["Do gentle range-of-motion exercises", "Apply heat", "Avoid sudden movements"],
        "Motion Vertigo": ["Focus on the horizon", "Avoid reading during travel", "Try ginger candies"],
        "Panic Attack": ["Practice deep breathing", "Focus on a physical sensation", "Remind yourself it will pass"],
        "Mild Depression": ["Establish a daily routine", "Get regular exercise", "Reach out for support"],
        "Sleep Apnea": ["Sleep on your side", "Maintain a healthy weight", "Consult a doctor for a sleep study"],
        "Restless Leg Syndrome": ["Try leg massages", "Establish a regular sleep schedule", "Avoid caffeine in evening"],
        "Bruxism": ["Wear a mouth guard at night", "Reduce stress", "Massage jaw muscles"],
        "TMJ Disorder": ["Eat soft foods", "Apply heat/cold to the jaw", "Avoid wide jaw movements"],
        "Mouth Ulcers": ["Avoid spicy/acidic foods", "Rinse with salt water", "Use a soft toothbrush"],
        "Gum Infection (Gingivitis)": ["Brush and floss regularly", "Use an antiseptic mouthwash", "Visit a dentist"],
        "Tooth Abscess": ["Rinse with warm salt water", "Take pain relievers", "Consult a dentist immediately"],
        "Bad Breath (Halitosis)": ["Maintain oral hygiene", "Brush your tongue", "Stay hydrated"],
        "Athlete’s Foot": ["Keep feet clean and dry", "Use antifungal powders", "Wear cotton socks"],
        "Dandruff": ["Use anti-dandruff shampoo", "Wash hair regularly", "Manage stress"],
        "Hair Loss (Alopecia)": ["Handle hair gently", "Eat a balanced diet", "Consult a dermatologist"],
        "Ingrown Toenail": ["Soak foot in warm water", "Keep area clean", "Wear comfortable shoes"],
        "Nail Fungus": ["Keep nails clean and trimmed", "Apply antifungal lacquer", "Keep feet dry"],
        "Hives (Urticaria)": ["Avoid known triggers", "Take antihistamines", "Wear loose clothing"],
        "Jet Lag": ["Adjust to new time zone", "Stay hydrated", "Get sunlight"],
        "Seasonal Affective Disorder": ["Maximize natural light", "Stay active", "Establish a sleep routine"],
        "Typhoid": ["STAY HYDRATED with safe water", "Wash hands thoroughly", "Consult a doctor for antibiotics"],
        "Jaundice": ["Drink plenty of fluids", "Avoid alcohol/fatty foods", "Seek medical evaluation"],
        "Measles": ["Isolate to prevent spreading", "Rest and stay hydrated", "Use fever reducers"],
        "Mumps": ["Apply compresses to swelling", "Eat soft foods", "Rest and stay hydrated"],
        "Rubella": ["Rest and stay home", "Drink fluids", "Avoid contact with pregnant women"],
        "Tuberculosis (early signs)": ["Consult a doctor for testing", "Complete full antibiotic course", "Ensure good ventilation"],
        "Whooping Cough": ["Stay hydrated", "Use a humidifier", "Seek medical care for breathing trouble"],
        "Pneumonia": ["Rest and sleep", "Drink lots of fluids", "Follow doctor's treatment plan"],
        "Bronchial Asthma": ["Use rescue inhaler as prescribed", "Avoid triggers", "Stay calm during attacks"],
        "Hepatitis A": ["Rest and avoid strain", "Avoid alcohol", "Wash hands strictly"],
        "Hepatitis B": ["Avoid alcohol/certain meds", "Follow a healthy diet", "Consult a doctor"],
        "Dengue Fever": ["Take acetaminophen (Avoid Ibuprofen/Aspirin)", "Drink plenty of fluids", "Rest"],
        "Chikungunya": ["Get plenty of rest", "Stay hydrated", "Take acetaminophen for pain"],
        "Leptospirosis": ["Consult a doctor for antibiotics", "Avoid contaminated water", "Rest"],
        "Ringworm": ["Apply antifungal cream", "Keep area clean", "Do not share towels"],
        "Scabies": ["Apply prescribed medicated creams", "Wash clothes/bedding in hot water", "Treat close contacts"],
        "Psoriasis": ["Moisturize regularly", "Avoid harsh soaps", "Manage stress"],
        "Boils": ["Apply warm compresses", "Do not squeeze or pop", "Keep the area clean"],
        "Cellulitis": ["Apply a sterile bandage", "Elevate the affected limb", "Seek urgent medical care"],
        "Tonsil Stones": ["Gargle with warm salt water", "Use a water flosser on low", "Stay hydrated"],
        "Strep Throat": ["Finish all antibiotics", "Gargle with warm salt water", "Rest"],
        "Laryngitis": ["Rest your voice", "Use a humidifier", "Drink warm liquids"],
        "Nasal Polyps": ["Use saline nasal rinses", "Avoid irritants", "Maintain moisture"],
        "Hay Fever": ["Check pollen forecasts", "Keep windows closed", "Use antihistamines"],
        "Dehydration Headache": ["Drink fluids immediately", "Rest in a cool place", "Avoid caffeine"],
        "Heat Stroke": ["Seek emergency medical help", "Move to a cool area", "Sip water if conscious"],
        "Hypothermia": ["Warm the core slowly", "Move to a warm place", "Remove wet clothing"],
        "Traveler’s Diarrhea": ["Drink safe bottled water", "Eat hot cooked foods", "Use ORS"],
        "Gallbladder Infection": ["Seek medical attention", "Avoid solid foods", "Stay hydrated"],
        "Pancreatic Infection": ["Consult a doctor immediately", "Switch to clear liquids", "Avoid alcohol"],
        "Hiccups": ["Hold your breath for 10-20 seconds", "Drink a glass of water quickly", "Pull on your tongue gently"],
        "Dry Throat": ["Gargle with warm salt water", "Drink plenty of warm fluids", "Use a humidifier"],
        "Minor Muscle Cramp": ["Gently stretch the affected muscle", "Massage the area", "Apply heat to tight muscles or cold to sore ones"],
        "Chapped Lips": ["Use a lip balm containing petrolatum or beeswax", "Stay hydrated", "Avoid licking your lips"]
    }
    return precautions_db.get(disease, [
        "Please consult a medical professional for accurate advice and treatment.",
        "Monitor your symptoms closely.",
        "Rest and stay hydrated."
    ])

WHEN_TO_SEE_DOCTOR_DB = {
    "Common Cold": ["Fever lasts more than **3 days**", "Symptoms worsen after day 7", "Difficulty breathing or chest pain", "Severe headache or ear pain"],
    "Flu (Influenza)": ["High fever above **103°F / 39.4°C**", "Trouble breathing", "Severe vomiting or diarrhea", "Symptoms improve then suddenly worsen"],
    "Sore Throat": ["Fever above **102°F / 39°C**", "Difficulty swallowing or opening the mouth", "Rash along with sore throat", "Symptoms persist beyond **7 days**"],
    "Strep Throat": ["Very high fever above **102°F / 39°C**", "Severe throat pain or difficulty swallowing", "White patches on the throat or tonsils", "Breathing difficulty or extreme weakness"],
    "Fever": ["Fever above **104°F / 40°C**", "Fever lasts more than **3 days**", "Severe headache or stiff neck with fever", "Confusion or difficulty waking up"],
    "Headache": ["Sudden, severe 'thunderclap' headache", "Headache with fever, stiff neck or rash", "Headache after head injury", "Vision changes or slurred speech with headache"],
    "Migraine": ["Worst headache of your life", "Headache with fever or stiff neck", "Neurological symptoms like weakness or confusion", "Vomiting that prevents taking medication"],
    "Stomach Ache": ["Severe pain that doesn't go away", "Blood in stool or vomit", "Fever along with abdominal pain", "Pain that moves to the lower right abdomen"],
    "Food Poisoning": ["Unable to keep liquids down for more than **8 hours**", "Signs of dehydration (no urine, dry mouth)", "Blood in stool or vomit", "High fever above **101.5°F / 38.6°C**"],
    "Cough": ["Cough persists for **more than 3 weeks**", "Coughing blood", "Shortness of breath", "High fever with cough"],
    "Acidity": ["Chest pain (rule out heart issues)", "Difficulty swallowing", "Symptoms persist despite antacids", "Unexplained weight loss with acidity"],
    "Constipation": ["No bowel movement for more than **3 days** despite home remedies", "Blood in stool", "Severe abdominal pain", "Sudden constipation with no known cause"],
    "Dehydration": ["Signs of severe dehydration: no urine, rapid heartbeat", "Confusion or extreme dizziness", "Cannot keep fluids down", "Dehydration in infants or elderly"],
    "Indigestion": ["Chest pain that could be mistaken for heartburn", "Severe pain, sweating or shortness of breath", "Blood in stool or vomit", "Persistent weight loss"],
    "Allergy": ["Difficulty breathing or throat swelling (anaphylaxis)", "Hives spreading rapidly", "Symptoms don't improve with antihistamines", "Allergic reaction to a bee sting or food"],
    "Urinary Tract Infection (UTI)": ["Fever or chills along with UTI symptoms", "Back or flank pain", "Nausea or vomiting", "Symptoms worsen or don't improve in **2-3 days**"],
    "Tonsillitis": ["Difficulty breathing or swallowing", "Drooling (unable to swallow)", "Fever above **103°F / 39.4°C**", "Muffled voice or stiff neck"],
    "Ear Infection (mild)": ["Fever above **102°F / 39°C**", "Severe pain or loss of hearing", "Dizziness or vomiting", "Symptoms worsen after **48-72 hours**"],
    "Sinus Infection": ["Symptoms persist beyond **10 days**", "Severe headache or facial pain", "Visual changes or swelling around eyes", "High fever with sinus symptoms"],
    "Jaundice": ["Fever or abdominal pain with jaundice", "Confusion or extreme fatigue", "Dark urine and pale stools together", "Jaundice that's worsening over days"],
    "Typhoid": ["High fever for more than **3-4 days**", "Rose-colored spots on the abdomen", "Confusion or extreme weakness", "Severe abdominal pain or bloating"],
    "Dengue Fever": ["Bleeding from nose or gums", "Blood in urine, stool or vomit", "Severe abdominal pain", "Rapid breathing or extreme fatigue"],
    "Appendicitis (early signs)": ["Pain migrates to lower right abdomen", "Fever with abdominal pain", "Vomiting with inability to pass gas", "Seek emergency care immediately if suspected"],
    "Kidney Stones": ["Fever or chills with kidney stone pain", "Unable to keep fluids down", "Pain that's unmanageable", "Blood in urine"],
    "Gout": ["Joint is very hot, red and swollen", "Fever along with joint attack", "First-ever gout attack (confirm diagnosis)"],
    "Sciatica": ["Loss of bladder or bowel control", "Progressive weakness in the leg", "Pain after a trauma or fall"],
}

def get_when_to_see_doctor(disease):
    """Returns red-flag warning signs for when to escalate to a doctor."""
    default = [
        "Symptoms worsen significantly or persist beyond **7 days**",
        "High fever above **103°F / 39.4°C**",
        "Difficulty breathing or severe pain",
        "You feel something is seriously wrong"
    ]
    return WHEN_TO_SEE_DOCTOR_DB.get(disease, default)

# Load Models and Feature Names
try:
    with open('backend/model.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('backend/nb_model.pkl', 'rb') as f:
        nb_model = pickle.load(f)
    print("Models loaded successfully.")
    
    with open('backend/model_data.pkl', 'rb') as f:
        feature_names = pickle.load(f)
    print("Feature names loaded successfully.")
except FileNotFoundError:
    print("Error: Model files not found. Please run train_model.py first.")
    model = None
    nb_model = None
    feature_names = []

SERIOUS_DISEASES = [
    "Hepatitis A", "Hepatitis B", "Hepatitis C", "Hepatitis D", "Hepatitis E",
    "Tuberculosis (early signs)", "Typhoid", "Pneumonia", "Heart attack",
    "Paralysis (brain hemorrhage)", "Kidney Stones", "Dengue Fever",
    "Chikungunya", "Appendicitis (early signs)", "Leptospirosis",
    "Bronchial Asthma", "Pancreatic Infection", "Gallbladder Infection",
    "Heart problems", "Diabetes", "Anemia", "High Blood Pressure"
]

# Logging Setup
if not os.path.exists('logs'):
    os.makedirs('logs')
        
def get_empathy_message(text):
    """Detects distress or concern and returns a comforting validation message."""
    distress_keywords = ["worried", "scared", "help", "please", "bad", "hurts", "pain", "killing me", "worry", "fear", "anxious", "sad", "uncomfortable"]
    text_lower = text.lower()
    
    if any(k in text_lower for k in distress_keywords):
        return "I'm sorry to hear you're feeling this way. I understand it can be worrying when you're not feeling your best. Let's look into this together. "
    return "I've noted your input. "

def get_nearby_medical_facilities(lat, lon, severity='normal'):
    """
    Fetches nearby medical facilities using OpenStreetMap Overpass API.
    Uses a tiered search: 5km -> 10km -> 20km if no results found.
    """
    try:
        # Optimization: One single 15km search instead of tiered (much faster)
        radius = 15000 
        amenities = "hospital|pharmacy" if severity == 'high' else "hospital|clinic|doctors|pharmacy"
        
        # Select 2 most reliable servers
        overpass_urls = [
            "https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter"
        ]
        
        overpass_query = f"""
        [out:json][timeout:10];
        (
          node["amenity"~"{amenities}"](around:{radius}, {lat}, {lon});
          way["amenity"~"{amenities}"](around:{radius}, {lat}, {lon});
        );
        out center;
        """
        
        data = None
        for url in overpass_urls:
            try:
                # Fast timeout: 6 seconds per server
                response = requests.get(url, params={'data': overpass_query}, timeout=6)
                if response.status_code == 200:
                    data = response.json()
                    break
            except:
                continue
        
        if not data:
            return []

        elements = data.get('elements', [])
            
        if elements:
            print(f"DEBUG: Found {len(elements)} facilities")
            facilities = []
            for element in elements:
                tags = element.get('tags', {})
                amenity = tags.get('amenity', 'Medical Facility')
                
                # Better naming
                name = tags.get('name')
                if not name:
                    if amenity == 'pharmacy': name = 'Medical Store'
                    elif amenity == 'hospital': name = 'General Hospital'
                    else: name = 'Medical Center'

                addr = tags.get('addr:full') or \
                       f"{tags.get('addr:street', '')} {tags.get('addr:city', '')}".strip() or \
                       "Nearby Location"
                phone = tags.get('phone') or tags.get('contact:phone', 'Check online')
                
                f_lat = element.get('lat') or element.get('center', {}).get('lat')
                f_lon = element.get('lon') or element.get('center', {}).get('lon')
                
                if f_lat and f_lon:
                    d = calculate_distance(lat, lon, f_lat, f_lon)
                    facilities.append({
                        'name': name,
                        'address': addr,
                        'phone': phone,
                        'distance': round(d, 2),
                        'lat': f_lat,
                        'lon': f_lon,
                        'type': amenity.replace('_', ' ').capitalize()
                    })
            
            facilities.sort(key=lambda x: x['distance'])
            
            # Ensure we have a mix if possible: at least 2 medical stores (pharmacy) if available
            pharmacies = [f for f in facilities if f['type'] == 'Pharmacy'][:2]
            others = [f for f in facilities if f['type'] != 'Pharmacy'][:3]
            
            combined = pharmacies + others
            combined.sort(key=lambda x: x['distance'])
            
            return combined[:5] # Return top 5 combined (hospitals + pharmacies)
            
        return []
        
    except Exception as e:
        print(f"Error fetching medical facilities: {e}")
        return []

def calculate_distance(lat1, lon1, lat2, lon2):
    """Haversine formula to calculate distance in km."""
    R = 6371 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@app.route('/')
def home():
    return send_from_directory('../frontend', 'index.html')

@app.route('/users', methods=['GET'])
def get_users():
    users = []
    if os.path.exists('logs'):
        for filename in os.listdir('logs'):
            if filename.endswith('_history.csv') and filename != 'history.csv':
                # Extract 'raj_25' from 'raj_25_history.csv'
                user_id = filename.replace('_history.csv', '')
                users.append(user_id)
    return jsonify({'users': users})

@app.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    # Sanitize user_id to prevent directory traversal
    safe_user_id = "".join([c for c in user_id if c.isalpha() or c.isdigit() or c=='_'])
    csv_file = f"logs/{safe_user_id}_history.csv"
    json_file = f"logs/{safe_user_id}_profile.json"
    
    deleted = False
    for f in [csv_file, json_file]:
        if os.path.exists(f):
            try:
                os.remove(f)
                deleted = True
            except Exception as e:
                print(f"Error removing {f}: {e}")
    
    if deleted:
        return jsonify({'message': 'User data deleted successfully'}), 200
    else:
        return jsonify({'error': 'User data not found'}), 404

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user_id = data.get('user_id')
    password = data.get('password')
    
    if not user_id or not password:
        return jsonify({'error': 'Missing credentials'}), 400
        
    safe_user_id = "".join([c for c in user_id if c.isalpha() or c.isdigit() or c=='_'])
    profile_file = f"logs/{safe_user_id}_profile.json"
    
    if os.path.exists(profile_file):
        with open(profile_file, 'r') as f:
            profile = json.load(f)
            
        if str(profile.get('password')) == str(password):
            return jsonify({'message': 'Login successful'}), 200
        else:
            return jsonify({'error': 'Invalid password'}), 401
    
    return jsonify({'error': f'Profile for {user_id} not found'}), 404

@app.route('/users/<user_id>/profile', methods=['GET'])
def get_user_profile(user_id):
    safe_user_id = "".join([c for c in user_id if c.isalpha() or c.isdigit() or c=='_'])
    profile_file = f"logs/{safe_user_id}_profile.json"
    if os.path.exists(profile_file):
        with open(profile_file, 'r') as f:
            profile = json.load(f)
        
        # Don't leak password to the browser
        if 'password' in profile:
            del profile['password']
            
        return jsonify({'profile': profile})
    return jsonify({'profile': {}}), 404

@app.route('/predict', methods=['POST'])
def predict():

    if not model:
        return jsonify({'error': 'Model not loaded'}), 500
        
    data = request.json
    none_of_these = data.get('none_of_these', False)
    force_diagnose = data.get('force', False)
    user_text = str(data.get('message', ''))
    history = data.get('history', [])
    
    user_name = data.get('user_name', 'anonymous')
    user_age = data.get('user_age', '0')
    user_profile = data.get('user_profile', {})
    
    # Define personalized files
    user_log_file = f"logs/{user_name}_{user_age}_history.csv"
    user_profile_file = f"logs/{user_name}_{user_age}_profile.json"

    # Save/Update profile if provided
    if user_profile:
        # Load existing profile to preserve password if it's missing in the update
        if os.path.exists(user_profile_file):
            with open(user_profile_file, 'r') as f:
                existing_profile = json.load(f)
            if 'password' in existing_profile and 'password' not in user_profile:
                user_profile['password'] = existing_profile['password']
        
        with open(user_profile_file, 'w') as f:
            json.dump(user_profile, f)

    # Initialize CSV if not exists (with profile header)
    if not os.path.exists(user_log_file):
        with open(user_log_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([f"Name: {user_name.capitalize()}"])
            writer.writerow([f"Age: {user_age}"])
            writer.writerow([f"Gender: {user_profile.get('gender', 'N/A')}"])
            writer.writerow([f"Medical Conditions: {user_profile.get('conditions', 'N/A')}"])
            writer.writerow([f"Allergies: {user_profile.get('allergies', 'N/A')}"])
            writer.writerow([f"Lifestyle: {user_profile.get('lifestyle', 'N/A')}"])
            writer.writerow([f"Medications: {user_profile.get('medications', 'N/A')}"])
            writer.writerow([])
            writer.writerow(['Date', 'Time', 'User_Input', 'Extracted_Symptoms', 'Predicted_Disease', 'Confidence'])

    # Handle 'None of these' explicitly
    if none_of_these:
        return jsonify({
            'response': "I understand. Since none of the common symptoms for these conditions match your experience, I'm not exactly sure what the problem is. **Please consult a healthcare professional for a proper diagnosis.**",
            'extracted_symptoms': [],
            'status': 'collecting'
        })

    # If force diagnose but no input, we use history
    if force_diagnose and not user_text:
        user_text = "Diagnose now."
        
    if not user_text and not force_diagnose:
        return jsonify({'error': 'No message provided'}), 400

    # 0. Handle Greetings
    if is_greeting(user_text):
         return jsonify({
            'response': "Hello! I'm MediBot. Please describe your symptoms in detail (e.g., 'I have a high fever, cough, and body pain'), and I'll analyze them for you.",
            'extracted_symptoms': history,
            'status': 'collecting'
        })


    # Symptom Extraction
    _, extracted_from_text = extract_symptoms(user_text, feature_names)
    newly_extracted_symptoms = [s for s in extracted_from_text if s in feature_names]
    
    # Merge history with new symptoms
    total_symptoms = list(set(history + newly_extracted_symptoms))
    
    # ACCURACY CHECK: Intercept Ambiguous Symptoms
    user_text_lower = user_text.lower()
    for ambig_term, specific_options in AMBIGUOUS_SYMPTOMS.items():
        if re.search(r'\b' + re.escape(ambig_term) + r'\b', user_text_lower):
            # The user said an ambiguous term. Did they ALREADY clarify it?
            # We check total_symptoms (current extraction + history)
            already_clarified = any(opt in total_symptoms for opt in specific_options)
            
            if not already_clarified:
                # We need to ask for clarification
                friendly_options = " or ".join([opt.replace('_', ' ') for opt in specific_options])
                return jsonify({
                    'response': f"You mentioned {ambig_term}. Could you clarify: is it a normal {specific_options[0].replace('_', ' ')}, or is it {specific_options[1].replace('_', ' ')}?",
                    'extracted_symptoms': history,
                    'status': 'clarifying',
                    'ambiguous_term': ambig_term,
                    'options': [opt.replace('_', ' ') for opt in specific_options]
                })
    
    if not total_symptoms:
        # Check for vague sentiments
        vague_phrases = ["not feeling good", "dont feel good", "not feeling well", "sick", "unwell", "not good", "feeling bad", "not ok", "something is wrong", "feel weird", "feeling weird", "not right", "uncomfortable", "strange", "odd", "feeling off", "i dont", "not really", "help", "diagnose", "check me"]
        positive_phrases = ["i am good", "i'm good", "feeling great", "i am great", "doing well", "i'm fine", "feeling fine", "perfect", "good", "great", "excellent", "i feel good", "i feel great"]
        
        user_text_lower = user_text.lower()
        
        if any(phrase in user_text_lower for phrase in vague_phrases):
             return jsonify({
                'response': get_empathy_message(user_text) + "Can you describe the specific symptoms you're facing right now so I can help you better?",
                'extracted_symptoms': [],
                'status': 'collecting'
            })

        if any(phrase in user_text_lower for phrase in positive_phrases):
             return jsonify({
                'response': "I am happy to hear that you are feeling great! I'm here to assist you whenever you're not feeling your best. Is there anything else you'd like to check today?",
                'extracted_symptoms': [],
                'status': 'collecting'
            })

        return jsonify({
            'response': get_empathy_message(user_text) + "I couldn't identify any specific medical symptoms yet. Could you please describe what you're feeling? For example, 'I have a fever and headache'.",
            'extracted_symptoms': [],
            'status': 'collecting'
        })
    
    # Re-calculate input vector based on cumulative symptoms
    input_vector = np.zeros((1, len(feature_names)))
    for s in total_symptoms:
        if s in feature_names:
            input_vector[0, feature_names.index(s)] = 1

    # Ensemble Prediction
    rf_probabilities = model.predict_proba(input_vector)[0]
    nb_probabilities = nb_model.predict_proba(input_vector)[0]
    
    # Average the probabilities for smoother, more intelligent bounds
    probabilities = (rf_probabilities + nb_probabilities) / 2
    
    top_3_indices = probabilities.argsort()[-3:][::-1]
    
    top_predictions = []
    for idx in top_3_indices:
        pred_disease = model.classes_[idx]
        conf = float(probabilities[idx])
        if conf > 0:
            top_predictions.append({
                'disease': pred_disease,
                'confidence': conf,
                'precautions': get_precautions(pred_disease),
                'description': DISEASE_DESCRIPTIONS.get(pred_disease, "No description available."),
                'symptoms': [s.replace('_', ' ') for s in DISEASE_PROFILES.get(pred_disease, [])]
            })

    # --- Advanced Home-Bias Re-ranking ---
    
    # 1. SPECIAL CASE: Liver Conditions (Jaundice vs Hepatitis)
    # If the user has liver symptoms, we ALWAYS prioritize Jaundice over Hepatitis for home users.
    liver_symptoms = {"yellowish_skin", "dark_urine", "yellowing_of_eyes", "abdominal_discomfort", "abdominal_pain"}
    has_liver_symptom = any(s in liver_symptoms for s in total_symptoms)
    
    if has_liver_symptom:
        # If any Hepatitis is in top prediction, ensure Jaundice is #1 instead
        if "Hepatitis" in top_predictions[0]['disease']:
            jaundice_found = False
            for i, p in enumerate(top_predictions):
                if p['disease'] == "Jaundice":
                    j_pred = top_predictions.pop(i)
                    j_pred['confidence'] = max(j_pred['confidence'], 0.82) # Force high confidence for common name
                    top_predictions.insert(0, j_pred)
                    jaundice_found = True
                    break
            
            if not jaundice_found:
                 # Manually inject Jaundice as #1
                 top_predictions.insert(0, {
                    'disease': "Jaundice",
                    'confidence': 0.88,
                    'precautions': get_precautions("Jaundice"),
                    'description': DISEASE_DESCRIPTIONS.get("Jaundice", ""),
                    'symptoms': [s.replace('_', ' ') for s in DISEASE_PROFILES.get("Jaundice", [])]
                 })
            
            # Penalize the serious Hepatitis prediction
            for p in top_predictions[1:]:
                if "Hepatitis" in p['disease']:
                    p['confidence'] = min(p['confidence'], 0.12)

    # 2. GENERAL CASE: Other Serious Conditions
    # If #1 is Serious and any Normal alternative exists (even with 0% score from RF), 
    # we swap them if they share at least one identified symptom.
    if len(top_predictions) >= 2:
        if top_predictions[0]['disease'] in SERIOUS_DISEASES:
            for i in range(1, len(top_predictions)):
                if top_predictions[i]['disease'] not in SERIOUS_DISEASES:
                    # Move common disease to top
                    common_pred = top_predictions.pop(i)
                    # Boost confidence of common one significantly
                    common_pred['confidence'] = max(common_pred['confidence'], 0.7)
                    top_predictions.insert(0, common_pred)
                    break
            
    if not top_predictions:
        return jsonify({
            'response': "I'm having trouble matching your symptoms to any specific condition. It would be best to **see a doctor** for an accurate evaluation.",
            'extracted_symptoms': total_symptoms,
            'status': 'collecting',
            'top_predictions': []
        })

    prediction = top_predictions[0]['disease']
    confidence = top_predictions[0]['confidence']
    precautions = get_precautions(prediction)

    # ACCURACY CHECK: Confidence & Ambiguity Handling
    primary_conf = top_predictions[0]['confidence']
    
    # Personalization: Detect Recurring Symptoms from History
    recurring_mention = ""
    if os.path.exists(user_log_file):
        try:
            df_hist = pd.read_csv(user_log_file, skiprows=8) # Skip header rows (Name, Age, Gender, Conditions, Allergies, Lifestyle, Meds, Empty)
            if not df_hist.empty and 'Extracted_Symptoms' in df_hist.columns:
                # Count occurrences of the newly extracted symptoms in history
                for s in newly_extracted_symptoms:
                    past_count = df_hist['Extracted_Symptoms'].str.contains(s).sum()
                    if past_count >= 2: # Mention if seen at least twice before
                        recurring_mention = f"I notice you've experienced {s.replace('_', ' ')} a few times recently. "
                        break
        except Exception as e:
            print(f"History analysis error: {e}")

    def get_suggestions(preds, current_symptoms, profile):
        suggs = []
        
        # 1. Profile-Based Adaptive Questions (High Priority)
        user_conditions = profile.get('conditions', '').lower()
        for (condition, symptom_trigger), follow_ups in ADAPTIVE_RULES.items():
            if condition and condition.lower() in user_conditions:
                # If the user has the condition and mentions the trigger symptom
                if any(s == symptom_trigger for s in current_symptoms):
                    for f in follow_ups:
                        if f not in current_symptoms and f not in suggs:
                            suggs.append(f)

        # 2. Model-Based Suggestions (Fall-back)
        for pred in preds[:2]:
            profile_symptoms = DISEASE_PROFILES.get(pred['disease'], [])
            for s in profile_symptoms:
                if s not in current_symptoms and s not in suggs:
                    suggs.append(s)
        return [s.replace('_', ' ') for s in suggs[:6]]

    # 1. LOW CONFIDENCE CASE: If top prediction is too weak, ask for more details
    if primary_conf < 0.45 and not force_diagnose:
        symptom_str = ", ".join([str(s).replace('_', ' ') for s in total_symptoms])
        return jsonify({
            'response': recurring_mention + get_empathy_message(user_text) + f"I've noted: {symptom_str}. These symptoms aren't enough for me to be certain yet. Could you tell me more?",
            'extracted_symptoms': total_symptoms,
            'status': 'collecting_low_conf',
            'suggestions': get_suggestions(top_predictions, total_symptoms, user_profile),
            'top_predictions': top_predictions
        })

    # 2. AMBIGUITY CASE: If top 2 are very close, provide both as possibilities
    if len(top_predictions) >= 2:
        secondary_conf = top_predictions[1]['confidence']
        gap = primary_conf - secondary_conf
        
        # If we have many symptoms (3+), we should be MORE decisive. 
        # Reduce gap threshold from 0.15 to 0.05 if we have 3+ symptoms
        threshold = 0.15 if len(total_symptoms) < 3 else 0.05
        
        if gap < threshold and not force_diagnose:
            disease1 = top_predictions[0]['disease']
            disease2 = top_predictions[1]['disease']
            
            # If the user's latest message was one of the differentiator suggestions,
            # we should avoid stuck loops by just picking the top one if they insist.
            return jsonify({
                'response': recurring_mention + f"I'm still weighing between **{disease1}** and **{disease2}**. Do you have any other very specific symptoms like skin rashes or severe pain that I might have missed?",
                'extracted_symptoms': total_symptoms,
                'status': 'ambiguous',
                'suggestions': get_suggestions(top_predictions, total_symptoms, user_profile),
                'top_predictions': top_predictions[:2]
            })

    # 3. INTERACTIVE FLOW: If only 1-2 symptoms or confidence is not extremely high
    # Be slightly more decisive if we have 3+ symptoms
    is_confident = (len(total_symptoms) >= 3 and primary_conf > 0.65) or (primary_conf > 0.98) or force_diagnose
    
    if not is_confident or (len(total_symptoms) < 3 and not force_diagnose):
       # Ask for more symptoms
        symptom_str = ", ".join([str(s).replace('_', ' ') for s in total_symptoms])
        
        return jsonify({
            'response': recurring_mention + get_empathy_message(user_text) + f"I've noted: {symptom_str}. To be more accurate, do you have any of these other related symptoms?",
            'extracted_symptoms': total_symptoms,
            'status': 'collecting',
            'suggestions': get_suggestions(top_predictions, total_symptoms, user_profile),
            'top_predictions': top_predictions
        })

    # Log Interaction
    with open(user_log_file, 'a', newline='') as f:
        writer = csv.writer(f)
        now = datetime.datetime.now()
        writer.writerow([
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M:%S"),
            user_text,
            ", ".join([str(s) for s in total_symptoms]),
            prediction,
            f"{confidence:.2f}"
        ])
        
    # --- Build simplified response for ChatGPT-style integration ---
    symptom_str = ', '.join([str(s).replace('_', ' ') for s in total_symptoms])
    empathy = get_empathy_message(user_text)
    
    # Opening line (Keep it short as the card will handle the rest)
    if prediction in SERIOUS_DISEASES:
        response_text = (f"I'm sorry you're feeling this way. Based on your symptoms ({symptom_str}), "
                        f"this may require **professional medical evaluation**. It could be related to **{prediction}**.")
    else:
        response_text = (f"I'm sorry you're not feeling well. Based on your symptoms ({symptom_str}), "
                        f"this looks like it could be **{prediction}**, which is quite common and usually manageable at home 🏠")
    
    # Prep data for the card (extracted from previous logic)
    doctor_signs = get_when_to_see_doctor(prediction)
    
    all_related = []
    for p in top_predictions[:2]:
        all_related.extend(DISEASE_PROFILES.get(p['disease'], []))
    
    remaining_symptoms = []
    for s in all_related:
        if s not in total_symptoms and s not in remaining_symptoms:
            remaining_symptoms.append(s.replace('_', ' '))
    
    quick_check = remaining_symptoms[:3] if remaining_symptoms else []

    # Personalized Advice Addition
    personalized_notes = []
    
    # Allergy Advice
    user_allergies = user_profile.get('allergies', '').lower()
    for allergy, advice in ALLERGY_ADVICE.items():
        if allergy.lower() in user_allergies:
            personalized_notes.append(f"**Allergy Warning:** {advice}")

    # Lifestyle Advice
    user_lifestyle = user_profile.get('lifestyle', '').lower()
    for factor, advice in LIFESTYLE_ADVICE.items():
        if factor.lower() in user_lifestyle:
            personalized_notes.append(f"**Lifestyle Note:** {advice}")

    if personalized_notes:
        response_text += "\n\n" + "\n".join(personalized_notes)
    
    # Recommendation Logic
    recommendations = get_precautions(prediction)
    
    # Get hospital recommendations based on location
    hospital_data = []
    location = data.get('location') # {lat: ..., lon: ...}
    print(f"DEBUG: Location received in /predict: {location}")
    if location and 'lat' in location and 'lon' in location:
        severity = 'high' if prediction in SERIOUS_DISEASES else 'normal'
        hospital_data = get_nearby_medical_facilities(location['lat'], location['lon'], severity)

    return jsonify({
        'disease': prediction,
        'confidence': float(confidence),
        'description': DISEASE_DESCRIPTIONS.get(prediction, "No description available."),
        'symptoms': [s.replace('_', ' ') for s in DISEASE_PROFILES.get(prediction, [])],
        'top_predictions': top_predictions,
        'extracted_symptoms': total_symptoms,
        'precautions': recommendations,
        'status': 'diagnosed',
        'response': response_text,
        'is_minor': prediction in MINOR_DISEASES, # Added is_minor flag
        'recommendations': recommendations, # New field for general recommendations
        'when_to_see_doctor': doctor_signs,
        'quick_check': quick_check,
        'hospitals': [f for f in hospital_data if f['type'] != 'Pharmacy'],
        'pharmacies': [f for f in hospital_data if f['type'] == 'Pharmacy']
    })

@app.route('/download-history')
def download_history():
    user_name = request.args.get('name')
    user_age = request.args.get('age')
    
    if user_name and user_age:
        target_file = f"logs/{user_name}_{user_age}_history.csv"
        download_name = f"{user_name.capitalize()}_Health_History.csv"
    else:
        # Fallback for old global history if exists, or just send 404
        target_file = "logs/history.csv"
        download_name = "Global_Health_History.csv"

    if os.path.exists(target_file):
        return send_file(os.path.abspath(target_file), as_attachment=True, download_name=download_name, mimetype='text/csv')
    else:
        return "No history found yet. Please chat with the bot first.", 404

@app.route('/download-pdf')
def download_pdf():
    user_name = request.args.get('name')
    user_age = request.args.get('age')
    
    if not user_name or not user_age:
        return "User name and age are required.", 400
        
    csv_file = f"logs/{user_name}_{user_age}_history.csv"
    pdf_name = f"{user_name.capitalize()}_Medical_Report.pdf"
    pdf_path = f"logs/{user_name}_{user_age}_report.pdf"
    
    if not os.path.exists(csv_file):
         return "No history found yet. Please chat with the bot first.", 404
         
    # Generate PDF
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Header
        pdf.set_font("helvetica", 'B', 18)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 15, "MediBot AI - Professional Medical Report", ln=True, align='C')
        
        # Disclaimer
        pdf.set_font("helvetica", 'I', 10)
        pdf.set_text_color(180, 50, 50)
        pdf.cell(0, 8, "Disclaimer: This report is not an original medical report. This is only for the assistance of AI.", ln=True, align='C')
        
        pdf.line(10, 33, 200, 33)
        pdf.ln(10)
        
        # Read profile data from the top of the CSV
        rows = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
        # Extract metadata
        pdf.set_font("helvetica", 'B', 12)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 10, "Patient Profile Summary:", ln=True)
        pdf.set_font("helvetica", '', 11)
        
        data_start_idx = 0
        for i, row in enumerate(rows):
            if not row:
                continue
            if row[0] == 'Date':
                data_start_idx = i
                break
            pdf.cell(0, 6, str(row[0]), ln=True)
            
        pdf.line(10, pdf.get_y()+5, 200, pdf.get_y()+5)
        pdf.ln(10)
        
        # Table Header
        pdf.set_font("helvetica", 'B', 10)
        pdf.set_fill_color(200, 220, 255)
        pdf.cell(25, 8, "Date", 1, 0, 'C', fill=True)
        pdf.cell(20, 8, "Time", 1, 0, 'C', fill=True)
        pdf.cell(70, 8, "Extracted Symptoms", 1, 0, 'C', fill=True)
        pdf.cell(75, 8, "Predicted Disease", 1, 1, 'C', fill=True)
        
        # Table Content
        pdf.set_font("helvetica", '', 9)
        for row in rows[data_start_idx+1:]:
            if len(row) >= 6:
                date_val = str(row[0])
                time_val = str(row[1])
                symptoms = row[3][:40] + "..." if len(row[3]) > 40 else row[3]
                disease = row[4][:40] + "..." if len(row[4]) > 40 else row[4]
                
                # Sanitize text
                symptoms = symptoms.encode('latin-1', 'replace').decode('latin-1')
                disease = disease.encode('latin-1', 'replace').decode('latin-1')

                pdf.cell(25, 8, date_val, 1)
                pdf.cell(20, 8, time_val, 1)
                pdf.cell(70, 8, symptoms, 1)
                pdf.cell(75, 8, disease, 1, 1)
                
        # Footer
        pdf.set_y(-15)
        pdf.set_font("helvetica", "I", 8)
        pdf.cell(0, 10, "Generated automatically by MediBot AI Diagnostics System.", align='C')
        
        pdf.output(pdf_path)
        
        return send_file(os.path.abspath(pdf_path), as_attachment=True, download_name=pdf_name, mimetype='application/pdf')
    except Exception as e:
        print(f"PDF Gen Error: {e}")
        return "Internal error generating PDF.", 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
