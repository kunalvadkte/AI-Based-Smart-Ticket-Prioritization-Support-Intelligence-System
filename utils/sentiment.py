"""
utils/sentiment.py
Sentiment analysis and urgency detection utilities.
Uses VADER for robust sentiment scoring on support ticket text.
"""

import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# ──────────────────────────────────────────────
# VADER ANALYSER (singleton)
# ──────────────────────────────────────────────
_analyser = SentimentIntensityAnalyzer()

# Urgency keyword lists (domain-specific)
CRITICAL_KEYWORDS = [
    'down', 'crash', 'breach', 'hack', 'expose', 'loss', 'fail', 'error',
    'critical', 'urgent', 'immediately', 'emergency', 'severe', 'broken',
    'corrupt', 'unavailable', 'blocked', 'suspended', 'attack', 'leak',
    'production', 'outage', 'unreachable', 'data loss', 'compromised'
]

MEDIUM_KEYWORDS = [
    'slow', 'delay', 'intermittent', 'sometime', 'occasionally', 'timeout',
    'loading', 'freeze', 'glitch', 'wrong', 'incorrect', 'mismatch',
    'failed', 'missing', 'not working', 'issue', 'problem', 'bug'
]


# ──────────────────────────────────────────────
# PUBLIC API
# ──────────────────────────────────────────────

def analyse_sentiment(text: str) -> dict:
    """
    Analyse sentiment of ticket text using VADER.

    Returns:
        {
          'compound': float,   # -1 (very negative) to +1 (very positive)
          'label': str,        # 'Negative' | 'Neutral' | 'Positive'
          'pos': float,
          'neg': float,
          'neu': float,
        }
    """
    if not text or not isinstance(text, str):
        text = ""
    scores = _analyser.polarity_scores(text)
    compound = scores['compound']
    if compound <= -0.05:
        label = 'Negative'
    elif compound >= 0.05:
        label = 'Positive'
    else:
        label = 'Neutral'

    return {
        'compound': round(compound, 4),
        'label': label,
        'pos': round(scores['pos'], 4),
        'neg': round(scores['neg'], 4),
        'neu': round(scores['neu'], 4),
    }


def detect_urgency_keywords(text: str) -> dict:
    """
    Scan text for critical / medium urgency keywords.

    Returns:
        {
          'critical_matches': list[str],
          'medium_matches': list[str],
          'urgency_score': int,   # 0-3  (0=none, 3=very high)
        }
    """
    if not text or not isinstance(text, str):
        text = ""
    text_lower = text.lower()

    critical_hits = [kw for kw in CRITICAL_KEYWORDS if kw in text_lower]
    medium_hits   = [kw for kw in MEDIUM_KEYWORDS   if kw in text_lower]

    if len(critical_hits) >= 2:
        score = 3
    elif len(critical_hits) == 1:
        score = 2
    elif len(medium_hits) >= 2:
        score = 1
    else:
        score = 0

    return {
        'critical_matches': critical_hits[:5],   # limit display to top 5
        'medium_matches':   medium_hits[:5],
        'urgency_score':    score,
    }


def build_urgency_explanation(sentiment: dict, urgency: dict, priority: str) -> str:
    """
    Generate a human-readable explanation for the predicted priority.
    """
    parts = []

    # Sentiment insight
    if sentiment['label'] == 'Negative':
        parts.append("Detected strongly negative sentiment in the ticket text.")
    elif sentiment['label'] == 'Neutral':
        parts.append("Ticket sentiment appears neutral.")
    else:
        parts.append("Positive tone detected — may indicate a feature request or inquiry.")

    # Keyword insight
    if urgency['critical_matches']:
        kws = ', '.join([f'"{k}"' for k in urgency['critical_matches'][:3]])
        parts.append(f"Critical keywords found: {kws}.")
    elif urgency['medium_matches']:
        kws = ', '.join([f'"{k}"' for k in urgency['medium_matches'][:3]])
        parts.append(f"Medium-urgency keywords detected: {kws}.")
    else:
        parts.append("No critical urgency keywords detected in text.")

    # Priority-specific closing
    if priority == 'High':
        parts.append("Immediate escalation recommended.")
    elif priority == 'Medium':
        parts.append("Standard escalation protocol applies.")
    else:
        parts.append("Routine handling is appropriate.")

    return ' '.join(parts)


def get_sla_recommendation(priority: str) -> str:
    """Return the SLA string for a given priority."""
    sla_map = {
        'High':   'Resolve within 1 hour',
        'Medium': 'Resolve within 6 hours',
        'Low':    'Resolve within 24 hours',
    }
    return sla_map.get(priority, 'Resolve within 24 hours')
