"""
train_model.py
──────────────────────────────────────────────────────────────────────────────
Model training script for Smart Ticket Prioritization System.
Run this ONCE to generate and save model artefacts.

Usage:
    python train_model.py

Outputs:
    models/model.joblib
    models/vectorizer.joblib
    models/encoders.joblib
"""

import os
import sys
import time
import logging
import warnings
import numpy as np
import pandas as pd
import scipy.sparse as sp
import joblib
import json

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix
)

warnings.filterwarnings('ignore')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-8s  %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger(__name__)

# ─── PATHS ───────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, 'dataset')
MODEL_DIR   = os.path.join(BASE_DIR, 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

DATASET_PATH    = os.path.join(DATASET_DIR, 'tickets.csv')
MODEL_PATH      = os.path.join(MODEL_DIR, 'model.joblib')
VECTORIZER_PATH = os.path.join(MODEL_DIR, 'vectorizer.joblib')
ENCODERS_PATH   = os.path.join(MODEL_DIR, 'encoders.joblib')
METRICS_PATH    = os.path.join(MODEL_DIR, 'metrics.json')


# ─── STEP 1: LOAD DATASET ────────────────────────────────────────────────────

def load_data() -> pd.DataFrame:
    if not os.path.exists(DATASET_PATH):
        log.info("Dataset not found – generating synthetic dataset…")
        sys.path.insert(0, DATASET_DIR)
        from generate_dataset import main as gen
        gen()
    log.info(f"Loading dataset from: {DATASET_PATH}")
    df = pd.read_csv(DATASET_PATH)
    log.info(f"Loaded {len(df):,} records  |  columns: {list(df.columns)}")
    return df


# ─── STEP 2: PREPROCESS ──────────────────────────────────────────────────────

from utils.preprocess import (
    clean_text,
    combine_text_features,
    ENCODERS,
    STRUCTURED_FEATURE_COLS
)

ISSUE_TYPE_MAP   = ENCODERS['issue_type']
CUSTOMER_MAP     = ENCODERS['customer_type']
CHANNEL_MAP      = ENCODERS['channel']
IMPACT_MAP       = ENCODERS['impact_level']


def preprocess(df: pd.DataFrame):
    log.info("Preprocessing data…")
    df = df.dropna(subset=['title', 'description', 'priority'])

    # Combined text for TF-IDF
    df['text_combined'] = df.apply(combine_text_features, axis=1)

    # Encode categoricals
    df['issue_type_enc']    = df['issue_type'].map(ISSUE_TYPE_MAP).fillna(0).astype(int)
    df['customer_type_enc'] = df['customer_type'].map(CUSTOMER_MAP).fillna(0).astype(int)
    df['channel_enc']       = df['channel'].map(CHANNEL_MAP).fillna(0).astype(int)
    df['impact_level_enc']  = df['impact_level'].map(IMPACT_MAP).fillna(0).astype(int)

    # Clip numerics
    df['previous_complaints'] = df['previous_complaints'].clip(0, 50)
    df['hours_open']          = df['hours_open'].clip(0, 720)

    log.info("Preprocessing complete.")
    return df


# ─── STEP 3: FEATURE ENGINEERING ─────────────────────────────────────────────

def build_features(df: pd.DataFrame):
    log.info("Building TF-IDF features…")
    vectorizer = TfidfVectorizer(
        max_features=3000,
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=2,
        stop_words='english'
    )
    X_text = vectorizer.fit_transform(df['text_combined'])

    log.info("Assembling structured features…")
    struct_cols = [
        'issue_type_enc', 'customer_type_enc', 'channel_enc',
        'previous_complaints', 'hours_open', 'impact_level_enc'
    ]
    X_struct = sp.csr_matrix(df[struct_cols].values.astype(float))

    # Combine text + structured
    X = sp.hstack([X_text, X_struct])
    log.info(f"Final feature matrix shape: {X.shape}")
    return X, vectorizer


# ─── STEP 4: ENCODE LABELS ───────────────────────────────────────────────────

def encode_labels(df: pd.DataFrame):
    le = LabelEncoder()
    y  = le.fit_transform(df['priority'])
    log.info(f"Classes: {le.classes_}")
    return y, le


# ─── STEP 5: TRAIN ───────────────────────────────────────────────────────────

def train(X, y, le):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    log.info(f"Train size: {X_train.shape[0]:,}  |  Test size: {X_test.shape[0]:,}")

    log.info("Training Random Forest classifier…")
    t0 = time.time()
    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        min_samples_split=4,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    clf.fit(X_train, y_train)
    log.info(f"Training completed in {time.time() - t0:.1f}s")

    # ── Evaluation ──────────────────────────────────────────────────────────
    y_pred    = clf.predict(X_test)
    acc       = accuracy_score(y_test, y_pred)
    class_rep = classification_report(y_test, y_pred, target_names=le.classes_)
    cm        = confusion_matrix(y_test, y_pred)

    log.info(f"\n{'='*60}")
    log.info(f"  TEST ACCURACY: {acc*100:.2f}%")
    log.info(f"{'='*60}")
    log.info(f"\nClassification Report:\n{class_rep}")
    log.info(f"Confusion Matrix:\n{cm}")

    # Cross-validation
    log.info("Running 5-fold cross-validation…")
    cv_scores = cross_val_score(clf, X_train, y_train, cv=5, scoring='accuracy', n_jobs=-1)
    log.info(f"CV Accuracy: {cv_scores.mean()*100:.2f}% ± {cv_scores.std()*100:.2f}%")

    # Persist metrics
    metrics = {
        'accuracy':        round(acc * 100, 2),
        'cv_mean':         round(cv_scores.mean() * 100, 2),
        'cv_std':          round(cv_scores.std() * 100, 2),
        'classes':         list(le.classes_),
        'class_report':    class_rep,
        'confusion_matrix': cm.tolist(),
        'train_size':      int(X_train.shape[0]),
        'test_size':       int(X_test.shape[0]),
    }
    with open(METRICS_PATH, 'w') as f:
        json.dump(metrics, f, indent=2)
    log.info(f"Metrics saved → {METRICS_PATH}")

    return clf, metrics


# ─── STEP 6: SAVE ARTEFACTS ──────────────────────────────────────────────────

def save_artefacts(clf, vectorizer, le):
    log.info("Saving model artefacts…")
    joblib.dump(clf,        MODEL_PATH,      compress=3)
    joblib.dump(vectorizer, VECTORIZER_PATH, compress=3)
    joblib.dump(ENCODERS,   ENCODERS_PATH,   compress=3)
    log.info(f"  model.joblib      → {MODEL_PATH}")
    log.info(f"  vectorizer.joblib → {VECTORIZER_PATH}")
    log.info(f"  encoders.joblib   → {ENCODERS_PATH}")


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("  SMART TICKET PRIORITIZATION – MODEL TRAINING")
    log.info("=" * 60)

    df         = load_data()
    df         = preprocess(df)
    X, vec     = build_features(df)
    y, le      = encode_labels(df)
    clf, _     = train(X, y, le)
    save_artefacts(clf, vec, le)

    log.info("\n✅  All artefacts saved. Run `python app.py` to start the server.")


if __name__ == '__main__':
    main()
