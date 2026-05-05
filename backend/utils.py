import re
import numpy as np
from thefuzz import fuzz

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
    "Jaundice": ["yellowish_skin", "dark_urine", "fatigue", "abdominal_pain", "vomiting", "yellowing_of_eyes", "abdominal_discomfort"],
    "Measles": ["mild_fever", "high_fever", "cough", "runny_nose", "redness_of_eyes", "skin_rash", "fatigue"],
    "Mumps": ["swollen_parotid_glands", "jaw_pain", "mild_fever", "headache", "pain_during_chewing"],
    "Rubella": ["mild_fever", "skin_rash", "swelled_lymph_nodes", "joint_pain"],
    "Tuberculosis (early signs)": ["persistent_cough", "weight_loss", "night_sweats", "fatigue", "blood_in_sputum", "mild_fever"],
    "Whooping Cough": ["coughing_fits", "vomiting", "breathlessness", "whoop_sound_after_cough"],
    "Pneumonia": ["chest_pain", "cough", "mild_fever", "high_fever", "breathlessness", "fatigue", "chills"],
    "Bronchial Asthma": ["wheezing", "breathlessness", "chest_tightness", "cough"],
    "Hepatitis A": ["yellowish_skin", "fatigue", "vomiting", "abdominal_pain", "loss_of_appetite", "mild_fever", "dark_urine"],
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
    "Chapped Lips": ["chapped_lips", "dry_lips"],
    # --- New Expanded Diseases (from standard medical knowledge) ---
    "Diabetes": ["excessive_thirst", "frequent_urination", "fatigue", "blurred_and_distorted_vision", "slow_healing_wounds", "tingling", "numbness_limbs", "weight_loss"],
    "Heart Attack (early warning)": ["chest_pain", "chest_tightness", "breathlessness", "sweating", "nausea", "vomiting", "jaw_pain", "left_arm_pain", "rapid_heartbeat"],
    "Stroke (early signs)": ["sudden_headache", "visual_disturbances", "face_drooping", "arm_weakness", "speech_difficulty", "confusion", "balance_problems"],
    "Anxiety Disorder": ["rapid_heartbeat", "sweating", "chest_tightness", "breathlessness", "restlessness", "poor_concentration", "muscle_tension"],
    "Thyroid (Hypothyroidism)": ["fatigue", "weight_gain", "cold_intolerance", "constipation", "dry_skin", "hair_thinning", "muscle_weakness", "slow_heartbeat"],
    "Thyroid (Hyperthyroidism)": ["weight_loss", "rapid_heartbeat", "heat_intolerance", "excessive_sweating", "nervousness", "diarrhoea", "tremors"],
    "Eczema (Atopic Dermatitis)": ["itching", "skin_rash", "dry_skin", "skin_redness", "scaly_skin", "oozing_skin"],
    "Rosacea": ["facial_redness", "skin_redness", "visible_blood_vessels", "pus_filled_pimples", "eye_irritation"],
    "Shingles (Herpes Zoster)": ["burning_sensation", "skin_rash", "blister", "itching", "mild_fever", "fatigue", "pain_in_site"],
    "Meningitis (early signs)": ["high_fever", "stiff_neck", "headache", "sensitivity_to_light", "vomiting", "fatigue", "confusion", "skin_rash"],
    "Conjunctivitis (Pink Eye)": ["redness_of_eyes", "eye_discharge", "watering_from_eyes", "itchy_eyes", "burning_sensation"],
    "Glaucoma (early signs)": ["visual_disturbances", "eye_pain", "headache", "nausea", "blurred_and_distorted_vision"],
    "Peptic Ulcer": ["stomach_pain", "burning_sensation", "vomiting", "weight_loss", "indigestion", "dark_stools"],
    "Gastritis": ["stomach_pain", "nausea", "vomiting", "indigestion", "loss_of_appetite", "bloating"],
    "Fatty Liver": ["fatigue", "abdominal_discomfort", "abdominal_pain", "weight_gain", "loss_of_appetite"],
    "Liver Cirrhosis (early signs)": ["fatigue", "yellowish_skin", "dark_urine", "abdominal_pain", "swelling", "vomiting"],
    "Chronic Kidney Disease (early)": ["fatigue", "frequent_urination", "dark_urine", "swelling", "breathlessness", "nausea"],
    "Prostate Issues": ["frequent_urination", "difficulty_urinating", "weak_urine_stream", "pelvic_pain", "burning_urination"],
    "PCOS (Polycystic Ovary Syndrome)": ["irregular_periods", "weight_gain", "hair_thinning", "acne", "fatigue", "bloating"],
    "Endometriosis": ["pelvic_pain", "painful_periods", "pain_during_intercourse", "fatigue", "diarrhoea", "bloating"],
    "Fibroids": ["pelvic_pain", "heavy_menstrual_bleeding", "frequent_urination", "constipation", "fatigue"],
    "Ovarian Cyst": ["pelvic_pain", "bloating", "frequent_urination", "irregular_periods", "vomiting"],
    "Osteoporosis (early signs)": ["back_ache", "bone_pain", "height_loss", "fracture_from_minor_fall", "brittle_nails"],
    "Bell's Palsy": ["face_drooping", "facial_pain", "drooling", "headache", "sensitivity_to_sound", "dry_eyes"],
    "Trigeminal Neuralgia": ["facial_pain", "sharp_stabbing_pain", "pain_during_chewing", "sensitivity_to_touch"],
    "Epilepsy (post-seizure)": ["confusion", "fatigue", "headache", "muscle_weakness", "loss_of_memory"],
    "Multiple Sclerosis (early)": ["fatigue", "numbness_limbs", "balance_problems", "blurred_and_distorted_vision", "muscle_weakness", "tingling"],
    "Parkinson's (early signs)": ["tremors", "muscle_stiffness", "balance_problems", "slow_movement", "joint_stiffness"],
    "Thalassemia": ["fatigue", "pale_skin", "breathlessness", "slow_growth", "bone_deformities", "swelling"],
    "Sickle Cell Anemia": ["fatigue", "pale_skin", "joint_pain", "swelling", "breathlessness", "vomiting", "high_fever"],
    "Lupus (SLE early signs)": ["fatigue", "joint_pain", "skin_rash", "mild_fever", "hair_thinning", "chest_pain", "sensitivity_to_light"],
    "Rheumatoid Arthritis": ["joint_pain", "joint_stiffness", "swelling", "fatigue", "mild_fever", "weight_loss"],
    "Fibromyalgia": ["muscle_pain", "fatigue", "sleep_disturbances", "headache", "poor_concentration", "joint_pain"],
    "Chronic Fatigue Syndrome": ["fatigue", "sleep_disturbances", "headache", "poor_concentration", "muscle_pain", "sore_throat_after_exertion"],
    "Alopecia Areata": ["patchy_hair_loss", "nail_changes", "itching"],
    "Vitiligo": ["white_patches_on_skin", "loss_of_skin_color", "premature_whitening_hair"],
    "Pityriasis Rosea": ["skin_rash", "itching", "scaly_skin", "mild_fever", "fatigue"],
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
    "Chapped Lips": "Dry, scaly, or cracked skin on the lips, common in dry or cold weather.",
    "Diabetes": "A metabolic disease that affects how your body turns food into energy, causing high blood sugar levels.",
    "Heart Attack (early warning)": "Chest pain or discomfort that may signal blocked blood flow to the heart. Requires immediate medical attention.",
    "Stroke (early signs)": "A brain attack where blood supply is cut off. Use FAST: Face drooping, Arm weakness, Speech difficulty, Time to call.",
    "Anxiety Disorder": "A mental health condition characterized by persistent feelings of worry, fear, and physical symptoms like rapid heartbeat.",
    "Thyroid (Hypothyroidism)": "An underactive thyroid gland that doesn't produce enough thyroid hormone, slowing down metabolism.",
    "Thyroid (Hyperthyroidism)": "An overactive thyroid gland that produces too much thyroid hormone, speeding up metabolism.",
    "Eczema (Atopic Dermatitis)": "A chronic skin condition causing itchy, inflamed patches of skin.",
    "Rosacea": "A common skin condition that causes redness and visible blood vessels in your face.",
    "Shingles (Herpes Zoster)": "A viral infection caused by the varicella-zoster virus causing a painful rash.",
    "Meningitis (early signs)": "Inflammation of the membranes surrounding the brain and spinal cord, potentially life-threatening.",
    "Conjunctivitis (Pink Eye)": "Inflammation or infection of the transparent membrane lining your eyelid.",
    "Glaucoma (early signs)": "A group of eye conditions that damage the optic nerve, often due to high eye pressure.",
    "Peptic Ulcer": "Open sores that develop on the inner lining of your stomach or upper small intestine.",
    "Gastritis": "Inflammation of the stomach lining, often caused by bacteria, certain medications, or stress.",
    "Fatty Liver": "A condition in which fat builds up in the liver, often linked to lifestyle factors.",
    "Liver Cirrhosis (early signs)": "Scarring of the liver tissue, usually resulting from long-term liver damage.",
    "Chronic Kidney Disease (early)": "Gradual loss of kidney function over time, often without early symptoms.",
    "Prostate Issues": "Conditions affecting the prostate gland, including benign prostatic hyperplasia and prostatitis.",
    "PCOS (Polycystic Ovary Syndrome)": "A hormonal disorder common among women of reproductive age, causing many small cysts on ovaries.",
    "Endometriosis": "A disorder in which tissue similar to the lining of the uterus grows outside the uterus.",
    "Fibroids": "Non-cancerous growths of the uterus that often appear during childbearing years.",
    "Ovarian Cyst": "Fluid-filled sacs on the ovary that are usually harmless but can cause pain.",
    "Osteoporosis (early signs)": "A bone disease that develops when bone mineral density decreases, leading to fragile bones.",
    "Bell's Palsy": "Sudden weakness or paralysis in the muscles on one side of the face.",
    "Trigeminal Neuralgia": "Chronic pain condition affecting the trigeminal nerve, causing intense facial pain.",
    "Epilepsy (post-seizure)": "A neurological disorder causing unprovoked, recurrent seizures. Symptoms described are post-seizure effects.",
    "Multiple Sclerosis (early)": "A disease that disrupts the flow of information within the brain, and between the brain and body.",
    "Parkinson's (early signs)": "A nervous system disorder affecting movement, causing shaking, stiffness, and slowing of movement.",
    "Thalassemia": "An inherited blood disorder caused by the body making an abnormal form of hemoglobin.",
    "Sickle Cell Anemia": "An inherited red blood cell disorder where there aren't enough healthy red blood cells.",
    "Lupus (SLE early signs)": "A systemic autoimmune disease that occurs when your body's immune system attacks your own tissues.",
    "Rheumatoid Arthritis": "An inflammatory disorder affecting joints, causing painful swelling that can eventually cause bone erosion.",
    "Fibromyalgia": "A disorder characterized by widespread musculoskeletal pain accompanied by fatigue and sleep issues.",
    "Chronic Fatigue Syndrome": "A complicated disorder with extreme fatigue that doesn't improve with rest.",
    "Alopecia Areata": "An autoimmune condition that attacks hair follicles, causing patchy hair loss.",
    "Vitiligo": "A condition causing loss of skin color in patches due to destruction of pigment-forming cells.",
    "Pityriasis Rosea": "A common, mild skin condition causing a scaly rash that usually goes away within 10 weeks."
}

MINOR_DISEASES = [
    "Hiccups", "Dry Throat", "Minor Muscle Cramp", "Chapped Lips", 
    "Athlete’s Foot", "Acne", "Dandruff", "Common Cold", "Small Cut", "Minor Burn"
]

WHEN_TO_SEE_DOCTOR = {
    "Common Cold": ["Fever lasts more than **3 days**", "Symptoms worsen after day 7", "Difficulty breathing or chest pain", "Severe headache or ear pain"],
    "Flu (Influenza)": ["High fever above **103°F / 39.4°C**", "Trouble breathing", "Severe vomiting or diarrhea", "Symptoms improve then suddenly worsen"],
    "Sore Throat": ["Fever above **102°F / 39°C**", "Difficulty swallowing or opening the mouth", "Rash along with sore throat", "Symptoms persist beyond **7 days**"],
    "Strep Throat": ["Very high fever above **102°F / 39°C**", "Severe throat pain or difficulty swallowing", "White patches on the throat or tonsils", "Breathing difficulty or extreme weakness"],
    "Fever": ["Fever above **104°F / 40°C**", "Fever lasts more than **3 days**", "Severe headache or stiff neck with fever", "Confusion or difficulty waking up"],
    "Headache": ["Sudden, severe 'thunderclap' headache", "Headache with fever, stiff neck, or rash", "Headache after head injury", "Vision changes or slurred speech with headache"],
    "Migraine": ["Worst headache of your life", "Headache with fever or stiff neck", "Neurological symptoms like weakness or confusion", "Vomiting that prevents taking medication"],
    "Stomach Ache": ["Severe pain that doesn't go away", "Blood in stool or vomit", "Fever along with abdominal pain", "Pain that moves to the lower right abdomen"],
    "Food Poisoning": ["Unable to keep liquids down for more than **8 hours**", "Signs of dehydration (no urine, dry mouth)", "Blood in stool or vomit", "High fever above **101.5°F / 38.6°C**"],
    "Diarrhea": ["Diarrhea for more than **2 days**", "Signs of dehydration", "Blood in stool", "Severe abdominal or rectal pain"],
    "Vomiting": ["Vomiting for more than **24 hours**", "Unable to keep any fluids down", "Signs of dehydration", "Blood in vomit"],
    "Cough": ["Cough persists for **more than 3 weeks**", "Coughing blood", "Shortness of breath", "High fever with cough"],
    "Acidity": ["Chest pain (rule out heart issues)", "Difficulty swallowing", "Symptoms persist despite antacids", "Unexplained weight loss with acidity"],
    "Constipation": ["No bowel movement for more than **3 days** despite home remedies", "Blood in stool", "Severe abdominal pain", "Sudden constipation with no known cause"],
    "Dehydration": ["Signs of severe dehydration: no urine, rapid heartbeat", "Confusion or extreme dizziness", "Cannot keep fluids down", "Dehydration in infants or elderly"],
    "Indigestion": ["Chest pain that could be mistaken for heartburn", "Severe pain, sweating, or shortness of breath", "Blood in stool or vomit", "Persistent weight loss"],
    "Allergy": ["Difficulty breathing or throat swelling (anaphylaxis)", "Hives spreading rapidly", "Symptoms don't improve with antihistamines", "Allergic reaction to a bee sting or food"],
    "Urinary Tract Infection (UTI)": ["Fever or chills along with UTI symptoms", "Back or flank pain", "Nausea or vomiting", "Symptoms worsen or don't improve in **2-3 days**"],
    "Tonsillitis": ["Difficulty breathing or swallowing", "Drooling (unable to swallow)", "Fever above **103°F / 39.4°C**", "Muffled voice or stiff neck"],
    "Ear Infection (mild)": ["Fever above **102°F / 39°C**", "Severe pain or loss of hearing", "Dizziness or vomiting", "Symptoms worsen after **48-72 hours**"],
    "Sinus Infection": ["Symptoms persist beyond **10 days**", "Severe headache or facial pain", "Visual changes or swelling around eyes", "High fever with sinus symptoms"],
    "Eye Strain": ["Sudden vision loss", "Eye pain that doesn't go away with rest", "Persistent blurred or double vision", "Eye redness with discharge"],
    "Conjunctivitis (Pink Eye)": ["Vision changes or severe eye pain", "Symptoms don't improve in **5-7 days**", "Sensitivity to light", "High fever with pink eye"],
    "Skin Rash": ["Rash spreads rapidly or covers large area", "Rash with fever, difficulty breathing", "Blisters or open sores", "Rash on face or genitals"],
    "Acne": ["Sudden severe cystic acne", "Acne with other hormonal symptoms", "Severe pain or infection from acne", "No improvement with OTC treatment after **3 months**"],
    "Insect Bite": ["Difficulty breathing or swallowing", "Rash spreading from the bite", "High fever after a bite", "Weakness, confusion, or rapid heartbeat"],
    "Sprain": ["Cannot put any weight on the area", "Extreme swelling or bruising", "Numbness or tingling", "Bone may be visible or deformed (fracture)"],
    "Sunburn": ["Blistering over large area of skin", "High fever or chills with sunburn", "Extreme pain or dizziness", "Signs of heat stroke: confusion, rapid pulse"],
    "Jaundice": ["Fever or abdominal pain with jaundice", "Confusion or extreme fatigue", "Dark urine and pale stools together", "Jaundice that's worsening over days"],
    "Typhoid": ["High fever for more than **3-4 days**", "Rose-colored spots on the abdomen", "Confusion or extreme weakness", "Severe abdominal pain or bloating"],
    "Dengue Fever": ["Bleeding from nose or gums", "Blood in urine, stool, or vomit", "Severe abdominal pain", "Rapid breathing or extreme fatigue"],
    "Chicken pox": ["Chickenpox in adults (more severe)", "Bacterial infection of the blisters", "High fever above **103°F / 39.4°C**", "Neurological symptoms like confusion"],
    "Pneumonia": ["Any difficulty breathing — seek care immediately", "Chest pain when breathing", "High fever with productive cough", "Rapid breathing or bluish lips"],
    "Asthma": ["Not responding to rescue inhaler", "Difficulty speaking due to breathlessness", "Blue lips or fingernails", "Silent chest (no wheezing) — life-threatening"],
    "Appendicitis (early signs)": ["Pain migrates to lower right abdomen", "Fever with abdominal pain", "Vomiting with inability to pass gas", "Seek emergency care immediately if suspected"],
    "Kidney Stones": ["Fever or chills with kidney stone pain", "Unable to keep fluids down", "Pain that's unmanageable", "Blood in urine"],
    "UTI": ["Fever or back pain (signs of kidney infection)", "Symptoms not improving in **2-3 days**", "Blood in urine", "Frequent UTIs (more than twice in 6 months)"],
    "Gout": ["Joint is very hot, red, and swollen", "Fever along with joint attack", "First-ever gout attack (confirm diagnosis)", "Tophi (lumps under skin)"],
    "Sciatica": ["Loss of bladder or bowel control", "Progressive weakness in the leg", "Pain after a trauma or fall", "Bilateral symptoms (both legs)"],
}

def get_when_to_see_doctor(disease):
    """Returns warning signs for when to escalate to a doctor."""
    default = [
        "Symptoms worsen significantly or persist beyond **7 days**",
        "High fever above **103°F / 39.4°C**",
        "Difficulty breathing or severe pain",
        "You feel something is seriously wrong"
    ]
    return WHEN_TO_SEE_DOCTOR.get(disease, default)

def is_greeting(text):
    """Checks if the text is primarily a greeting using word boundaries."""
    greetings = ["hello", "hi", "hii", "hey", "greetings", "good morning", "good evening"]
    text = text.lower().strip()
    # Use regex to find if ANY greeting word is present as a WHOLE word
    for greet in greetings:
        if re.search(r'\b' + re.escape(greet) + r'\b', text):
            # Only count as greeting if it's a short message (likely just a greeting)
            if len(text.split()) < 3:
                return True
    return False

def clean_text(text):
    """
    Cleans the user input text by removing special characters, converting to lowercase.
    """
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text

# 0. Ambiguity Map 
# If a user says these, we must ask for clarification instead of guessing
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

def extract_symptoms(text, feature_names):
    """
    Extracts symptoms from user text using fuzzy string matching and synonym mapping.
    Allows for spelling mistakes and natural language phrasing.
    """
    text_clean = clean_text(text)
    
    input_vector = np.zeros(len(feature_names))
    extracted_symptoms = []

    # 1. Hard-coded Keyword Mapping for better NLU
    # This maps common natural language keywords directly to feature names
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
        "toe_itching": ["itchy toes", "itch between toes", "athlete foot itch"],
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
        "scaling_on_feet": ["scaling on feet", "peeling feet", "skin peeling between toes", "dry scaly feet", "skin is peeling", "feet are peeling", "flaky feet", "peeling skin between toes"],
        "foot_odor": ["smelly feet", "foot odor", "feet smell", "stinky feet", "feet are smelly"],
        "scaly_skin": ["scaly skin", "peeling skin", "flaky skin rash", "skin is scaly"],
        "rose_spots": ["rose spots", "pink spots on stomach", "pink rash", "spots on chest", "rose colored spots", "pink spots on chest", "spots on my chest"],
        "skin_bumps": ["small bumps on skin", "skin blisters", "tiny bumps"],
        "swollen_parotid_glands": ["swollen glands near ears", "puffy cheeks", "swelling in parotid", "swollen parotid"],
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
        "chapped_lips": ["chapped lips", "dry lips", "cracked lips", "peeling lips", "lips are peeling", "lips are dry", "lips are cracked", "lips peeling", "lips dry", "lips cracked"],
        # --- New symptom keywords for expanded diseases ---
        "excessive_thirst": ["very thirsty", "extremely thirsty", "cant quench thirst", "always thirsty", "drinking a lot", "thirst that wont go away"],
        "slow_healing_wounds": ["wound not healing", "cut wont heal", "injury taking long time", "slow healing"],
        "numbness_limbs": ["numbness", "numb hands", "numb feet", "numb fingers", "numb toes", "cant feel legs", "loss of sensation"],
        "weight_gain": ["gaining weight", "weight has increased", "getting heavier", "unexplained weight gain", "putting on weight"],
        "cold_intolerance": ["always cold", "feeling too cold", "sensitive to cold", "cant tolerate cold"],
        "heat_intolerance": ["always hot", "feeling too hot", "very sensitive to heat", "sweating too much"],
        "tremors": ["shaking hands", "hand tremor", "trembling", "shaky hands", "uncontrollable shaking"],
        "dry_skin": ["dry skin", "skin feels dry", "skin is cracking", "tight skin"],
        "nervousness": ["nervous", "feeling nervous", "anxious", "on edge", "restless"],
        "slow_heartbeat": ["slow heartbeat", "bradycardia", "low heart rate", "heart beats slowly"],
        "excessive_sweating": ["excessive sweating", "sweating too much", "profuse sweating", "drenched in sweat"],
        "oozing_skin": ["weeping skin", "skin oozing", "fluid leaking from skin", "wet rash"],
        "facial_redness": ["red face", "facial flush", "redness on face", "face is red"],
        "visible_blood_vessels": ["spider veins on face", "veins visible on face", "capillaries visible"],
        "eye_irritation": ["irritated eyes", "eyes feel irritated", "eye discomfort"],
        "eye_discharge": ["eye discharge", "eyes are goopy", "crust on eyes in morning", "discharge from eyes", "gunky eyes"],
        "redness_of_eyes": ["red eyes", "pink eye", "eyes are red", "bloodshot eyes"],
        "watering_from_eyes": ["watery eyes", "eyes are watering", "teary eyes"],
        "confusion": ["confused", "cant think straight", "disoriented", "not making sense", "mental fog"],
        "face_drooping": ["face drooping", "one side of face drooping", "asymmetricface", "crooked smile"],
        "arm_weakness": ["arm is weak", "cant lift arm", "weakness in arm", "left arm feels weak"],
        "speech_difficulty": ["slurred speech", "cant speak properly", "trouble speaking", "difficulty speaking"],
        "sudden_headache": ["sudden severe headache", "thunderclap headache", "worst headache of my life", "headache came on suddenly"],
        "restlessness": ["restless", "cant sit still", "always moving", "feel like i need to move"],
        "poor_concentration": ["cant concentrate", "brain fog", "difficulty focusing", "poor focus", "trouble thinking"],
        "muscle_tension": ["tense muscles", "muscle tension", "tight muscles", "muscles feel tight"],
        "left_arm_pain": ["left arm hurts", "pain in left arm", "left shoulder pain radiating"],
        "jaw_pain": ["jaw hurts", "jaw pain", "pain in jaw", "aching jaw"],
        "pelvic_pain": ["pelvic pain", "pain in pelvis", "lower pelvic pain", "groin pain"],
        "irregular_periods": ["irregular periods", "missed period", "late period", "period is irregular", "abnormal menstrual cycle"],
        "painful_periods": ["painful periods", "menstrual cramps", "period pain", "bad cramps during period"],
        "heavy_menstrual_bleeding": ["heavy periods", "heavy bleeding during period", "flooding periods"],
        "pain_during_intercourse": ["pain during intercourse", "painful sex", "sex is painful"],
        "difficulty_urinating": ["hard to urinate", "difficulty peeing", "urine flow is weak", "cant urinate properly"],
        "weak_urine_stream": ["weak urine stream", "poor urine flow", "urine dribbles"],
        "dark_stools": ["dark stool", "black stool", "tarry stool", "stool is dark"],
        "bloating": ["bloated", "bloating", "belly feels full", "stomach is swollen", "tummy is bloated"],
        "back_ache": ["backache", "back is aching", "lower back pain", "back pain"],
        "bone_pain": ["bone pain", "bones are aching", "aching bones", "deep bone pain"],
        "white_patches_on_skin": ["white patches on skin", "skin losing color", "white spots on skin"],
        "pale_skin": ["pale skin", "skin looks pale", "skin turned white", "pallor"],
        "slow_movement": ["moving slowly", "slow movements", "sluggish movements", "movements are slow"],
        "muscle_stiffness": ["stiff muscles", "muscle stiffness", "muscles are rigid", "muscles wont relax"],
    }

    # Helper: Check if any keyword in a list is in the text (Word boundary matching + Gerund/Plural support)
    def has_keywords(k_list, text):
        for k in k_list:
            # Handle multi-word keywords with flexible spacing (e.g., "nose blocked" matches "nose is blocked")
            if " " in k:
                words = k.split()
                # Create a pattern that allows "is", "are", "am", "feel", "feels", "my", "the" between words
                flex_pattern = r"\b" + r"\s+(?:is\s+|are\s+|am\s+|feel\s+|feels\s+|my\s+|the\s+)?".join([re.escape(w) for w in words]) + r"\b"
                if re.search(flex_pattern, text, re.IGNORECASE):
                    return True

            # Escape and handle multi-word keywords for the standard check
            pattern = re.escape(k)
            # Improved suffix handling:
            # 1. Handle base word + ing/s/ed (e.g., cough -> coughing)
            # 2. Handle stem + doubled consonant + ing (e.g., vomit -> vomitting)
            # We use a simpler alternation for clarity
            pattern = rf"{k}|{k}ing|{k}s|{k}ed|{k}es"
            if len(k) > 3 and k.endswith(('t', 'p', 'n', 'm', 'g')):
                 # Common doubled consonants
                 pattern += f"|{k}{k[-1]}ing"
            
            if re.search(r'\b' + pattern + r'\b', text, re.IGNORECASE):
                return True
        return False

    # Helper: Disambiguate bites
    def is_valid_match(feature, text):
        if feature == "bite_mark":
            # Must have insect subject AND a bite action
            if not has_keywords(["insect", "bug", "mosquito", "spider", "bee", "wasp", "ant"], text):
                return False
            if not has_keywords(["bite", "bit", "bitten", "stung", "sting"], text):
                return False
        if feature == "dog_bite":
            # Must have dog subject AND a bite action
            if not has_keywords(["dog", "puppy", "hound", "canine"], text):
                return False
            if not has_keywords(["bite", "bit", "bitten", "snap"], text):
                return False
        return True

    # Apply keyword rules
    user_words = [w for w in text_clean.split() if len(w) > 2] # Pre-filter short words
    extracted_set = set()
    
    for feature, keywords in keyword_rules.items():
        # Check 1: Direct Matching (Fastest)
        if has_keywords(keywords, text_clean):
            if is_valid_match(feature, text_clean):
                if feature in feature_names:
                    extracted_set.add(feature)
                    continue

        # Check 2: Word-Level Fuzzy Matching (Only if direct fails)
        match_found = False
        stop_words = {"have", "feel", "with", "from", "that", "this", "they", "some", "hand"}
        for word in user_words:
            if word in stop_words: continue
            for k in keywords:
                # OPTIMIZATION: Quick length check before expensive fuzzy match
                # If length difference is more than 2, it's unlikely to have >85% ratio
                if abs(len(word) - len(k)) > 2: continue
                
                threshold = 86 if len(word) <= 4 else 85 
                if fuzz.ratio(word, k) >= threshold:
                    if is_valid_match(feature, text_clean):
                        if feature in feature_names:
                            extracted_set.add(feature)
                            match_found = True
                            break
            if match_found: break

    # 2. Fuzzy match fallback for anything missed (Token Set Ratio on Full Text)
    # Only run on symptoms not already found
    THRESHOLD = 80
    for i, symptom in enumerate(feature_names):
        if symptom in extracted_set:
            input_vector[i] = 1 # Update vector
            continue
            
        symptom_clean = symptom.strip().lower().replace('_', ' ')
        # OPTIMIZATION: Quick substring check before token_set_ratio
        if symptom_clean in text_clean or fuzz.token_set_ratio(symptom_clean, text_clean) >= THRESHOLD:
             input_vector[i] = 1
             extracted_set.add(symptom)
             
    return input_vector.reshape(1, -1), list(extracted_set)

def get_precautions(disease):
    """
    Returns a list of precautions/recommendations for the predicted disease.
    Focuses on extremely common, non-emergency home use ailments and First Aid.
    """
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
        "Chapped Lips": ["Use a lip balm containing petrolatum or beeswax", "Stay hydrated", "Avoid licking your lips"],
        "Diabetes": ["Monitor blood sugar regularly", "Follow prescribed diet plan", "Exercise daily", "Take medications as directed"],
        "Heart Attack (early warning)": ["Call emergency services immediately", "Chew an aspirin if not allergic", "Sit or lie down calmly while waiting for help"],
        "Stroke (early signs)": ["Call emergency services immediately (FAST protocol)", "Note the time symptoms started", "Do not give food or water"],
        "Anxiety Disorder": ["Practice deep breathing exercises", "Limit caffeine and alcohol", "Try mindfulness or meditation", "Speak with a mental health professional"],
        "Thyroid (Hypothyroidism)": ["Take prescribed thyroid medication", "Get regular thyroid checks", "Maintain a balanced diet"],
        "Thyroid (Hyperthyroidism)": ["Avoid iodine-rich foods", "Rest and reduce stress", "Follow prescribed treatment plan"],
        "Eczema (Atopic Dermatitis)": ["Moisturize frequently", "Avoid known triggers like soaps/detergents", "Use prescribed topical steroids"],
        "Rosacea": ["Use gentle skin care products", "Avoid sun and wind exposure", "Avoid spicy foods and alcohol"],
        "Shingles (Herpes Zoster)": ["Apply cool compresses", "Keep rash clean and dry", "Consult doctor for antiviral medication"],
        "Meningitis (early signs)": ["Seek emergency medical care immediately", "Do not delay treatment", "Avoid self-medication"],
        "Conjunctivitis (Pink Eye)": ["Avoid touching your eyes", "Wash hands frequently", "Do not share towels or pillowcases"],
        "Glaucoma (early signs)": ["Use prescribed eye drops", "Get regular eye pressure checks", "Avoid straining the eyes"],
        "Peptic Ulcer": ["Avoid NSAIDs and aspirin", "Avoid spicy/acidic foods", "Follow H. pylori treatment if diagnosed"],
        "Gastritis": ["Eat smaller meals", "Avoid alcohol and coffee", "Follow prescribed antacid therapy"],
        "Fatty Liver": ["Lose weight gradually", "Avoid alcohol completely", "Exercise regularly", "Eat a plant-rich diet"],
        "Liver Cirrhosis (early signs)": ["Avoid alcohol completely", "Take prescribed medications", "Consult a hepatologist"],
        "Chronic Kidney Disease (early)": ["Control blood pressure and sugar", "Reduce salt and protein intake", "Stay hydrated with doctor's guidance"],
        "Prostate Issues": ["Urinate when you feel the urge", "Limit caffeine and alcohol", "Consult a urologist"],
        "PCOS (Polycystic Ovary Syndrome)": ["Maintain a healthy weight", "Exercise regularly", "Consult a gynecologist for hormone therapy"],
        "Endometriosis": ["Use prescribed pain relievers", "Apply a heating pad to the pelvis", "Consult a gynecologist"],
        "Fibroids": ["Eat a low-fat, plant-rich diet", "Exercise regularly", "Consult a gynecologist"],
        "Ovarian Cyst": ["Take prescribed pain medication", "Monitor with follow-up ultrasound", "Consult a doctor if pain is severe"],
        "Osteoporosis (early signs)": ["Increase calcium and Vitamin D", "Do weight-bearing exercises", "Avoid smoking and alcohol"],
        "Bell's Palsy": ["Use eye drops to protect the eye", "Apply warm compresses to the face", "Consult a doctor for steroids"],
        "Trigeminal Neuralgia": ["Take prescribed anticonvulsants", "Avoid triggers like cold wind", "Consult a neurologist"],
        "Epilepsy (post-seizure)": ["Rest in a safe place", "Do not eat or drink until fully alert", "Consult your neurologist"],
        "Multiple Sclerosis (early)": ["Stay cool and avoid heat", "Exercise regularly", "Follow prescribed disease-modifying therapy"],
        "Parkinson's (early signs)": ["Follow prescribed medication schedule", "Do physical therapy", "Use assistive devices if needed"],
        "Thalassemia": ["Get regular blood check-ups", "Follow prescribed treatment", "Maintain a healthy diet"],
        "Sickle Cell Anemia": ["Stay hydrated", "Avoid extreme temperatures", "Take prescribed medications"],
        "Lupus (SLE early signs)": ["Protect skin from sun", "Follow prescribed anti-inflammatory medications", "Rest during flares"],
        "Rheumatoid Arthritis": ["Perform gentle range-of-motion exercises", "Apply warm/cold packs", "Follow prescribed DMARDs"],
        "Fibromyalgia": ["Improve sleep hygiene", "Engage in low-impact exercise", "Try stress management techniques"],
        "Chronic Fatigue Syndrome": ["Pace your activities carefully", "Maintain a sleep schedule", "Consult a doctor for management"],
        "Alopecia Areata": ["Consult a dermatologist", "Reduce stress", "Try prescribed topical immunotherapy"],
        "Vitiligo": ["Use high-SPF sunscreen", "Consult a dermatologist", "Consider prescribed repigmentation therapy"],
        "Pityriasis Rosea": ["Use mild, moisturizing soap", "Manage itching with antihistamines", "Avoid excessive sun exposure"]
    }
    return precautions_db.get(disease, [
        "Please consult a medical professional for accurate advice and treatment.",
        "Monitor your symptoms closely.",
        "Rest and stay hydrated."
    ])
