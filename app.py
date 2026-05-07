"""
app.py
──────────────────────────────────────────────────────────────────────────────
Flask application for Smart Ticket Prioritization & Support Intelligence System.

Routes:
  GET  /               → Landing page
  GET  /predict        → Ticket submission form
  POST /predict        → Run prediction → result page
  GET  /dashboard      → Analytics dashboard
  GET  /api/stats      → JSON statistics for charts
  GET  /api/history    → JSON ticket history
  POST /api/clear      → Clear ticket history
"""

import os
import json
import uuid
import logging
from datetime import datetime

from flask import (
    Flask, render_template, request,
    jsonify, redirect, url_for, session, flash
)

# ─── APP SETUP ───────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'stp-secret-2024-final-project')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-8s  %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger(__name__)

# ─── IN-MEMORY TICKET HISTORY ─────────────────────────────────────────────────
# Each entry: { ticket_id, timestamp, priority, confidence, issue_type, ... }
ticket_history: list[dict] = []
MAX_HISTORY = 200


# ─── LAZY MODEL CHECK ────────────────────────────────────────────────────────

def models_exist() -> bool:
    model_dir = os.path.join(os.path.dirname(__file__), 'models')
    required  = ['model.joblib', 'vectorizer.joblib', 'encoders.joblib']
    return all(os.path.exists(os.path.join(model_dir, f)) for f in required)


# ─── ROUTES ──────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    """Landing / hero page."""
    stats = _build_stats()
    return render_template('index.html', stats=stats, models_ready=models_exist())


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    """Ticket submission form + prediction handler."""
    if request.method == 'GET':
        return render_template('predict.html', models_ready=models_exist())

    # ── POST: process form ──────────────────────────────────────────────────
    if not models_exist():
        flash('⚠️  Model not trained yet. Please run train_model.py first.', 'danger')
        return redirect(url_for('predict'))

    try:
        form_data = {
            'title':                request.form.get('title', '').strip(),
            'description':          request.form.get('description', '').strip(),
            'issue_type':           request.form.get('issue_type', 'Other'),
            'customer_type':        request.form.get('customer_type', 'Regular'),
            'channel':              request.form.get('channel', 'Email'),
            'previous_complaints':  int(request.form.get('previous_complaints', 0)),
            'hours_open':           float(request.form.get('hours_open', 0)),
            'impact_level':         request.form.get('impact_level', 'Low'),
        }

        # Basic validation
        if not form_data['title'] or not form_data['description']:
            flash('Please fill in Ticket Title and Description.', 'warning')
            return redirect(url_for('predict'))

        # Run prediction (import here to allow app to start without models)
        from utils.predict import predict_ticket
        result = predict_ticket(form_data)

        # Record to history
        ticket_id = f"TKT-{str(uuid.uuid4())[:8].upper()}"
        history_entry = {
            'ticket_id':      ticket_id,
            'timestamp':      datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'title':          form_data['title'],
            'issue_type':     form_data['issue_type'],
            'customer_type':  form_data['customer_type'],
            'priority':       result['priority'],
            'confidence':     result['confidence'],
            'sla':            result['sla'],
        }
        ticket_history.append(history_entry)
        if len(ticket_history) > MAX_HISTORY:
            ticket_history.pop(0)

        log.info(f"Ticket {ticket_id} → Priority: {result['priority']}  "
                 f"Confidence: {result['confidence']}%")

        return render_template(
            'result.html',
            result=result,
            ticket_id=ticket_id,
            form_data=form_data,
        )

    except Exception as exc:
        log.exception("Prediction error")
        flash(f'Error during prediction: {exc}', 'danger')
        return redirect(url_for('predict'))


@app.route('/dashboard')
def dashboard():
    """Analytics dashboard page."""
    stats = _build_stats()
    return render_template('dashboard.html', stats=stats, history=ticket_history[-20:][::-1])


# ─── JSON API ─────────────────────────────────────────────────────────────────

@app.route('/api/stats')
def api_stats():
    """Return aggregate statistics as JSON for Chart.js."""
    return jsonify(_build_stats())


@app.route('/api/history')
def api_history():
    """Return ticket history as JSON."""
    return jsonify(list(reversed(ticket_history)))


@app.route('/api/clear', methods=['POST'])
def api_clear():
    """Clear ticket history."""
    ticket_history.clear()
    return jsonify({'status': 'cleared'})


# ─── HELPER: STATISTICS ───────────────────────────────────────────────────────

def _build_stats() -> dict:
    """Aggregate ticket_history into chart-friendly statistics."""
    total   = len(ticket_history)
    high    = sum(1 for t in ticket_history if t['priority'] == 'High')
    medium  = sum(1 for t in ticket_history if t['priority'] == 'Medium')
    low     = sum(1 for t in ticket_history if t['priority'] == 'Low')

    # Issue type distribution
    issue_counts: dict[str, int] = {}
    for t in ticket_history:
        it = t.get('issue_type', 'Other')
        issue_counts[it] = issue_counts.get(it, 0) + 1

    # Customer type distribution
    channel_counts: dict[str, int] = {}
    for t in ticket_history:
        ch = t.get('customer_type', 'Regular')
        channel_counts[str(ch)] = channel_counts.get(str(ch), 0) + 1

    # Average confidence
    avg_conf = (
        round(sum(t['confidence'] for t in ticket_history) / total, 1)
        if total else 0
    )

    # Recent trend (last 10 tickets)
    recent = ticket_history[-10:]
    trend_labels    = [t['timestamp'].split(' ')[1] for t in recent]
    trend_high      = [1 if t['priority'] == 'High'   else 0 for t in recent]
    trend_medium    = [1 if t['priority'] == 'Medium' else 0 for t in recent]
    trend_low       = [1 if t['priority'] == 'Low'    else 0 for t in recent]

    return {
        'total':          total,
        'high':           high,
        'medium':         medium,
        'low':            low,
        'avg_confidence': avg_conf,
        'issue_counts':   issue_counts,
        'channel_counts': channel_counts,
        'trend': {
            'labels': trend_labels,
            'high':   trend_high,
            'medium': trend_medium,
            'low':    trend_low,
        }
    }


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────

if __name__ == '__main__':
    port  = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    log.info(f"Starting Smart Ticket Prioritization System on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
