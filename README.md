# 🩺 MediBot - Intelligent Medical Diagnostic Assistant

An AI-powered, user-centric healthcare decision support system. MediBot uses Natural Language Processing (NLP) and Machine Learning to translate unstructured user symptoms into accurate medical predictions. Designed with a **"Home-First" heuristic**, the system prioritizes common, treatable ailments to reduce diagnostic anxiety, while integrating real-time geospatial data to map users to nearby healthcare facilities.

## 🌟 Key Features

*   **Intelligent Symptom Parsing:** Utilizes NLP fuzzy string matching (`thefuzz`) to extract and normalize unstructured, conversational text into a structured binary feature matrix of 213 distinct symptoms.
*   **Ensemble Machine Learning:** Employs a robust ensemble of Random Forest and Gaussian Naive Bayes classifiers trained on an augmented dataset of 43,500+ clinical records, achieving >81.5% accuracy across 145 diseases.
*   **"Home-Bias" Heuristic Algorithm:** Custom scoring logic that penalizes severe, rare conditions and boosts common ailments for home-users, actively combating the alarmist "WebMD effect."
*   **Real-time Geolocation APIs:** Integrates the OpenStreetMap Overpass REST API to automatically locate and display hospitals and pharmacies within a 15km radius of the user based on Haversine distance calculations.
*   **Personalized Health Tracking:** Features a local-first, CSV-backed database that logs user interaction history and dynamically generates downloadable medical reports in CSV and PDF formats using `fpdf2`.
*   **Modern Premium UI:** Built with Vanilla JS and HTML/CSS, featuring a responsive, interactive, glassmorphism-inspired chat interface.

## 🚀 How to Run the Project

### 1. Prerequisites
Ensure you have **Python 3.8+** installed on your system.

### 2. Install Dependencies
Clone this repository and install the required libraries:
```bash
pip install -r requirements.txt
```

### 3. Generate the ML Models
*Note: The trained `.pkl` model files are extremely large and are excluded from this repository via `.gitignore`.* 
Before running the application for the first time, you **must** generate the models locally:
```bash
python backend/train_model.py
```
*(This process takes a few minutes and will generate the `model.pkl` and `nb_model.pkl` files).*

### 4. Start the Application
Start the Flask backend web server:
```bash
python backend/app.py
```

### 5. Access the UI
Open your browser and navigate to:  http://127.0.0.1:5001 **. 
Create a profile and begin chatting with MediBot!

---

## 🛠 Project Architecture & Tech Stack

*   **Backend:** Python, Flask
*   **Data Processing:** pandas, NumPy, Regex
*   **Machine Learning:** scikit-learn (RandomForestClassifier, GaussianNB)
*   **Natural Language Processing:** thefuzz, python-Levenshtein
*   **APIs & Integrations:** OpenStreetMap Overpass API (`requests`), `fpdf2` (PDF Generation)
*   **Frontend:** HTML5, CSS3 (Glassmorphism UI), Vanilla JavaScript

---
*Created by Albin John.*
