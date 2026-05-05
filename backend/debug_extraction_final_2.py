from utils import extract_symptoms, DISEASE_PROFILES
import pickle

with open('backend/model_data.pkl', 'rb') as f:
    feature_names = pickle.load(f)

test_inputs = [
    "i have my nose blocked",
    "from morning my nose is blocked",
    "I have hiccups",
    "i feel my throat is dry",
    "my muscle is cramping",
    "my lips are peeling and dry"
]

print(f"Feature names count: {len(feature_names)}")
print(f"'hiccups' in feature_names: {'hiccups' in feature_names}")

for text in test_inputs:
    _, extracted = extract_symptoms(text, feature_names)
    print(f"Input: '{text}' -> Extracted: {extracted}")
