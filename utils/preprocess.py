"""
utils/preprocess.py
Data preprocessing utilities for Smart Ticket Prioritization System.
Handles text cleaning, feature engineering, and encoding.
"""

import re
import string
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder


# ──────────────────────────────────────────────
# TEXT CLEANING
# ──────────────────────────────────────────────

def clean_text(text: str) -> str:
    """
    Clean and normalize raw ticket text.
    - Lowercase
    - Remove special characters / extra whitespace
    """
    if not isinstance(text, str):
        text = str(text)
    text = text.lower()
    text = re.sub(r'http\S+|www\S+', '', text)          # remove URLs
    text = re.sub(r'[^a-z0-9\s]', ' ', text)            # keep alphanum
    text = re.sub(r'\s+', ' ', text).strip()            # collapse spaces
    return text


def combine_text_features(row) -> str:
    """
    Combine title + description + issue_type into one text blob for TF-IDF.
    """
    parts = [
        str(row.get('title', '')),
        str(row.get('description', '')),
        str(row.get('issue_type', ''))
    ]
    return clean_text(' '.join(parts))


# ──────────────────────────────────────────────
# CATEGORICAL ENCODING
# ──────────────────────────────────────────────

CATEGORICAL_COLS = ['issue_type', 'customer_type', 'channel', 'impact_level']

# Fixed category maps for consistent inference
ISSUE_TYPE_MAP = {
    'Payment Issue': 0, 'Login Issue': 1, 'Technical Bug': 2,
    'Feature Request': 3, 'Security Problem': 4,
    'Account Suspension': 5, 'Server Down': 6, 'Other': 7
}

CUSTOMER_TYPE_MAP = {'Premium': 0, 'Regular': 1}
CHANNEL_MAP = {'Email': 0, 'Chat': 1, 'Phone Call': 2}
IMPACT_LEVEL_MAP = {'Low': 0, 'Medium': 1, 'High': 2}

ENCODERS = {
    'issue_type': ISSUE_TYPE_MAP,
    'customer_type': CUSTOMER_TYPE_MAP,
    'channel': CHANNEL_MAP,
    'impact_level': IMPACT_LEVEL_MAP,
}


def encode_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply label encoding to categorical columns using fixed maps.
    Returns a copy with encoded columns.
    """
    df = df.copy()
    for col, mapping in ENCODERS.items():
        if col in df.columns:
            df[col + '_enc'] = df[col].map(mapping).fillna(0).astype(int)
    return df


def encode_single_record(record: dict) -> dict:
    """
    Encode a single prediction record using the fixed maps.
    """
    encoded = {}
    for col, mapping in ENCODERS.items():
        val = record.get(col, '')
        encoded[col + '_enc'] = mapping.get(val, 0)
    return encoded


# ──────────────────────────────────────────────
# NUMERICAL FEATURE NORMALIZATION (simple clip)
# ──────────────────────────────────────────────

def clip_numerical(df: pd.DataFrame) -> pd.DataFrame:
    """Clip numerical features to reasonable ranges."""
    df = df.copy()
    if 'previous_complaints' in df.columns:
        df['previous_complaints'] = df['previous_complaints'].clip(0, 50)
    if 'hours_open' in df.columns:
        df['hours_open'] = df['hours_open'].clip(0, 720)
    return df


# ──────────────────────────────────────────────
# FEATURE ASSEMBLY
# ──────────────────────────────────────────────

STRUCTURED_FEATURE_COLS = [
    'issue_type_enc', 'customer_type_enc', 'channel_enc',
    'previous_complaints', 'hours_open', 'impact_level_enc'
]


def build_structured_features(df: pd.DataFrame) -> np.ndarray:
    """
    Return numpy array of structured features for model input.
    """
    return df[STRUCTURED_FEATURE_COLS].values.astype(float)


def build_single_structured(record: dict) -> np.ndarray:
    """
    Build structured feature vector from a single encoded record dict.
    """
    row = [
        record.get('issue_type_enc', 0),
        record.get('customer_type_enc', 0),
        record.get('channel_enc', 0),
        float(record.get('previous_complaints', 0)),
        float(record.get('hours_open', 0)),
        record.get('impact_level_enc', 0),
    ]
    return np.array(row).reshape(1, -1)
