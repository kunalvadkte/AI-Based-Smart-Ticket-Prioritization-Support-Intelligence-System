"""
utils/predict.py
Prediction pipeline – loads saved models and orchestrates inference.
"""

import os
import numpy as np
import scipy.sparse as sp
import joblib

from utils.preprocess import (
    combine_text_features,
    encode_single_record,
    build_single_structured,
)
from utils.sentiment import (
    analyse_sentiment,
    detect_urgency_keywords,
    build_urgency_explanation,
    get_sla_recommendation,
)

# ──────────────────────────────────────────────
# MODEL PATHS
# ──────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR  = os.path.join(BASE_DIR, 'models')

MODEL_PATH      = os.path.join(MODEL_DIR, 'model.joblib')
VECTORIZER_PATH = os.path.join(MODEL_DIR, 'vectorizer.joblib')
ENCODERS_PATH   = os.path.join(MODEL_DIR, 'encoders.joblib')

# LabelEncoder sorts alphabetically → High=0, Low=1, Medium=2
_LE_CLASSES = ['High', 'Low', 'Medium']

# ──────────────────────────────────────────────
# LAZY-LOADED SINGLETONS
# ──────────────────────────────────────────────
_model      = None
_vectorizer = None
_encoders   = None


def _load_models():
    global _model, _vectorizer, _encoders
    if _model is None:
        _model      = joblib.load(MODEL_PATH)
        _vectorizer = joblib.load(VECTORIZER_PATH)
        _encoders   = joblib.load(ENCODERS_PATH)


def _decode_label(raw) -> str:
    """
    Convert model output to a human-readable priority string.
    Handles both integer-encoded (LabelEncoder) and string outputs.
    """
    s = str(raw)
    if s in ('0', '1', '2'):
        return _LE_CLASSES[int(s)]
    # Already a string label
    if s in ('High', 'Low', 'Medium'):
        return s
    # Fallback: try int index
    try:
        return _LE_CLASSES[int(float(s))]
    except Exception:
        return s


# ──────────────────────────────────────────────
# PUBLIC PREDICTION FUNCTION
# ──────────────────────────────────────────────

def predict_ticket(form_data: dict) -> dict:
    """
    Run full prediction pipeline on raw form data.

    Args:
        form_data: dict with keys:
            title, description, issue_type, customer_type,
            channel, previous_complaints, hours_open, impact_level

    Returns:
        Full prediction result dict.
    """
    _load_models()

    # 1. Text features via TF-IDF
    text_blob   = combine_text_features(form_data)
    text_vector = _vectorizer.transform([text_blob])    # sparse (1, n_features)

    # 2. Structured features
    encoded    = encode_single_record(form_data)
    struct_vec = build_single_structured(encoded)       # dense (1, 6)
    struct_sp  = sp.csr_matrix(struct_vec)

    # 3. Combine text + structured features
    X = sp.hstack([text_vector, struct_sp])

    # 4. Predict
    raw_pred   = _model.predict(X)[0]                   # int or str
    proba      = _model.predict_proba(X)[0]
    confidence = round(float(np.max(proba)) * 100, 1)

    # Decode to 'High' / 'Low' / 'Medium'
    priority = _decode_label(raw_pred)

    # Build probability dict keyed by decoded string class names
    raw_classes = [str(c) for c in _model.classes_]
    proba_dict: dict = {}
    for cls, p in zip(raw_classes, proba):
        label = _decode_label(cls)
        proba_dict[label] = round(float(p) * 100, 1)

    # 5. Sentiment + urgency analysis
    full_text   = f"{form_data.get('title', '')} {form_data.get('description', '')}"
    sentiment   = analyse_sentiment(full_text)
    urgency     = detect_urgency_keywords(full_text)
    explanation = build_urgency_explanation(sentiment, urgency, priority)
    sla         = get_sla_recommendation(priority)

    return {
        'priority':      priority,
        'confidence':    confidence,
        'probabilities': proba_dict,
        'sla':           sla,
        'explanation':   explanation,
        'sentiment':     sentiment,
        'urgency':       urgency,
        'input_summary': form_data,
        'text_blob':     text_blob,
    }
