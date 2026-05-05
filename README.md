# Neural Voice Assistant

A powerful, intelligent voice assistant built from scratch using a pure NumPy LSTM-RNN deep learning architecture. This system leverages sequential pattern recognition to understand natural language voice commands, featuring a robust Speech-to-Text pipeline and a beautiful, modern Web UI.

## 🌟 Key Features

*   **Pure NumPy LSTM Core:** The Natural Language Understanding (NLU) engine is a Long Short-Term Memory (LSTM) Recurrent Neural Network built entirely from scratch using only `numpy`—showcasing a deep understanding of backpropagation through time (BPTT) and sequence classification without relying on heavy frameworks like PyTorch or TensorFlow.
*   **23 Advanced Intents:** Capable of understanding and routing 23 distinct tasks, ranging from local OS control to web actions.
*   **Real-time Web Speech API:** Uses a modern Flask backend combined with a glassmorphism-inspired HTML/CSS/JS frontend. Voice transcription happens instantly in the browser via the Web Speech API.
*   **System & Web Automation:**
    *   **OS Actions:** Open/close applications, control system volume (mute, up, down), and media playback.
    *   **Web Actions:** Search Google, Wikipedia, play YouTube videos, and stream music.
    *   **AI Integration:** Answers general knowledge questions by integrating the OpenAI ChatGPT API.
    *   **Information:** Real-time weather parsing, time and date extraction, calculations, and news.
*   **Text-to-Speech:** The assistant audibly responds to commands using native browser Speech Synthesis.

## 🚀 How to Run the Project

### 1. Prerequisites
Ensure you have **Python 3.8+** installed on your system.
*(Note: This project relies on `pyautogui` and `os.system` commands optimized for Windows, though it can be adapted for macOS/Linux).*

### 2. Install Dependencies
Clone this repository and run the following to install required libraries:
```bash
pip install -r requirements.txt
```

### 3. (Optional) Set up ChatGPT API
If you want the assistant to answer complex general questions, set your OpenAI API key as an environment variable before starting the server:
```bash
# On Windows PowerShell
$env:OPENAI_API_KEY="your-api-key-here"
```

### 4. Start the Application
Train the model (if not already trained) and start the Flask web server:
```bash
# 1. Train the NumPy LSTM model on the natural language dataset (takes ~15 seconds)
python train_intent_model.py

# 2. Start the web server
python app.py
```

### 5. Access the Web UI
Open your browser and navigate to: **[http://localhost:5000](http://localhost:5000)**. 
Click the microphone button, grant audio permissions, and speak your command!

---

## 🛠 Project Architecture

1.  **`lstm_numpy.py`**: The mathematical core. Contains the `LSTMRNN` class with forward passes, cell state updates, and BPTT logic.
2.  **`dataset.json`**: The training corpus containing over 100 variations of natural language phrases mapped to 23 intents.
3.  **`nlp_preprocessor.py`**: Tokenizes text, builds a vocabulary mapping, and converts natural language into one-hot encoded sequence vectors for the LSTM.
4.  **`train_intent_model.py`**: The training script that fits the model to the dataset, achieving high accuracy on sequence classification, and pickles the learned weights.
5.  **`app.py`**: A lightweight Flask server that serves the UI and acts as the REST API endpoint (`/api/predict`) for NLU inference.
6.  **`action_executor.py`**: The execution logic. It takes the predicted intent from the LSTM, performs simple rule-based entity extraction, and triggers the actual system or web automation.
7.  **`templates/` & `static/`**: The frontend UI components featuring dynamic sound wave animations and responsive states.

---
*Created by Albin John.*
