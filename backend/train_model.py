import pandas as pd
import numpy as np
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import os

def train():
    print("Loading vectorized home dataset...")
    df = pd.read_csv('backend/home_dataset_vectorized.csv')
    
    X = df.drop(columns=['Disease']).values
    y = df['Disease'].values
    
    # Save feature names from columns
    symptoms_list = df.columns[1:].tolist()
    with open('backend/model_data.pkl', 'wb') as f:
        pickle.dump(symptoms_list, f)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training RandomForest model...")
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)
    print(f"RF Model Accuracy on sub-test set: {accuracy_score(y_test, clf.predict(X_test)):.4f}")

    print("Training Naive Bayes model...")
    nb_clf = GaussianNB()
    nb_clf.fit(X_train, y_train)
    print(f"NB Model Accuracy on sub-test set: {accuracy_score(y_test, nb_clf.predict(X_test)):.4f}")

    print("Training final models on full dataset...")
    final_clf = RandomForestClassifier(n_estimators=100, random_state=42)
    final_clf.fit(X, y)
    with open('backend/model.pkl', 'wb') as f:
        pickle.dump(final_clf, f)
        
    final_nb = GaussianNB()
    final_nb.fit(X, y)
    with open('backend/nb_model.pkl', 'wb') as f:
        pickle.dump(final_nb, f)
        
    print("Models trained and saved to backend/model.pkl and backend/nb_model.pkl")
    print("Feature names updated in backend/model_data.pkl")

if __name__ == "__main__":
    if not os.path.exists('backend'):
        os.makedirs('backend')
    train()
