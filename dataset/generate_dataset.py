"""
Synthetic Dataset Generator for Smart Ticket Prioritization System
Generates 5000+ realistic customer support tickets with all required features.
"""

import pandas as pd
import numpy as np
import random
import os

random.seed(42)
np.random.seed(42)

# ──────────────────────────────────────────────
# SAMPLE TEMPLATES
# ──────────────────────────────────────────────
HIGH_TITLES = [
    "Server completely down – production halted",
    "Critical payment failure affecting all users",
    "Security breach detected – immediate action needed",
    "Database corruption – data loss risk",
    "Account suspended unexpectedly – urgent",
    "API endpoint returning 500 errors in production",
    "Login completely broken for all premium users",
    "DDoS attack in progress – site unreachable",
    "Payment gateway rejected all transactions",
    "Critical bug causing data exposure",
]

MEDIUM_TITLES = [
    "Intermittent login failures reported",
    "Payment processing delayed by 2-3 minutes",
    "Feature not working as expected",
    "Report generation taking too long",
    "Email notifications not arriving",
    "Dashboard displaying incorrect statistics",
    "Export to PDF producing blank file",
    "Search results returning outdated data",
    "Two-factor authentication failing sometimes",
    "Profile update not saving properly",
]

LOW_TITLES = [
    "Request for new feature in dashboard",
    "Change password label text suggestion",
    "Minor UI alignment issue on mobile",
    "Request to add dark mode",
    "Improve onboarding guide",
    "Add CSV export option",
    "Update FAQ section",
    "Spelling error in help documentation",
    "Request for additional report filter",
    "Tooltip text unclear on settings page",
]

HIGH_DESCS = [
    "Our production server has gone completely offline. All users are unable to access the system. This is causing massive revenue loss every minute. Immediate intervention required.",
    "All payment transactions are failing with error code 500. Our entire e-commerce pipeline is halted. Customers cannot complete purchases. We are losing thousands per hour.",
    "We have detected unauthorized access attempts and a possible data breach. Sensitive customer PII may be at risk. Security team needs to investigate immediately.",
    "The database has corrupted records in the orders table. Multiple customers are reporting missing orders and wrong billing. Rollback may be necessary.",
    "A premium customer's account was suspended without warning. They have an active subscription and are unable to access any service. Client is threatening legal action.",
]

MEDIUM_DESCS = [
    "Some users are reporting they cannot log in. The issue appears intermittent and affects about 20% of our user base. It started around 2 hours ago.",
    "Payment processing is taking 3-5 minutes instead of the usual 10 seconds. Customers are complaining but transactions are eventually completing.",
    "The bulk email export feature is not functioning correctly. Files download but appear empty. This affects our marketing team's workflow.",
    "The dashboard KPI cards are showing numbers from last month instead of the current period. Users noticed the discrepancy during a board meeting.",
    "Two-factor authentication codes are sometimes not being delivered via SMS. Users have to retry 2-3 times to receive the code.",
]

LOW_DESCS = [
    "It would be great if we could export the analytics report as a PDF directly from the dashboard. Currently we have to use print screen.",
    "The onboarding tutorial skips some advanced features. New users are confused about how to set up automated workflows.",
    "On mobile screens below 375px, the navigation menu overlaps the logo slightly. It is a minor cosmetic issue.",
    "Many of our users prefer working in dark environments. A dark mode toggle would greatly improve their experience.",
    "There is a small spelling error on the help page – 'recieve' should be 'receive'. Minor but worth fixing.",
]

ISSUE_TYPES = [
    "Payment Issue", "Login Issue", "Technical Bug",
    "Feature Request", "Security Problem",
    "Account Suspension", "Server Down", "Other"
]

CUSTOMER_TYPES = ["Premium", "Regular"]
CHANNELS = ["Email", "Chat", "Phone Call"]
IMPACT_LEVELS = ["Low", "Medium", "High"]

# Priority → weight mappings to make dataset realistic
PRIORITY_WEIGHTS = {"High": 0.30, "Medium": 0.45, "Low": 0.25}


def get_templates(priority):
    if priority == "High":
        return HIGH_TITLES, HIGH_DESCS
    elif priority == "Medium":
        return MEDIUM_TITLES, MEDIUM_DESCS
    else:
        return LOW_TITLES, LOW_DESCS


def generate_record(idx):
    priority = random.choices(
        list(PRIORITY_WEIGHTS.keys()),
        weights=list(PRIORITY_WEIGHTS.values())
    )[0]

    titles, descs = get_templates(priority)

    title = random.choice(titles)
    description = random.choice(descs)

    # Bias issue_type towards priority
    if priority == "High":
        issue_type = random.choices(
            ISSUE_TYPES,
            weights=[0.20, 0.15, 0.15, 0.02, 0.20, 0.15, 0.10, 0.03]
        )[0]
        customer_type = random.choices(CUSTOMER_TYPES, weights=[0.70, 0.30])[0]
        previous_complaints = random.randint(3, 15)
        hours_open = round(random.uniform(0, 4), 2)
        impact_level = random.choices(IMPACT_LEVELS, weights=[0.05, 0.15, 0.80])[0]
    elif priority == "Medium":
        issue_type = random.choices(
            ISSUE_TYPES,
            weights=[0.15, 0.20, 0.20, 0.10, 0.10, 0.10, 0.05, 0.10]
        )[0]
        customer_type = random.choices(CUSTOMER_TYPES, weights=[0.50, 0.50])[0]
        previous_complaints = random.randint(1, 6)
        hours_open = round(random.uniform(1, 20), 2)
        impact_level = random.choices(IMPACT_LEVELS, weights=[0.10, 0.70, 0.20])[0]
    else:
        issue_type = random.choices(
            ISSUE_TYPES,
            weights=[0.05, 0.05, 0.10, 0.40, 0.05, 0.05, 0.05, 0.25]
        )[0]
        customer_type = random.choices(CUSTOMER_TYPES, weights=[0.30, 0.70])[0]
        previous_complaints = random.randint(0, 3)
        hours_open = round(random.uniform(5, 72), 2)
        impact_level = random.choices(IMPACT_LEVELS, weights=[0.70, 0.25, 0.05])[0]

    channel = random.choice(CHANNELS)

    return {
        "ticket_id": f"TKT-{10000 + idx}",
        "title": title,
        "description": description,
        "issue_type": issue_type,
        "customer_type": customer_type,
        "channel": channel,
        "previous_complaints": previous_complaints,
        "hours_open": hours_open,
        "impact_level": impact_level,
        "priority": priority
    }


def main():
    print("Generating synthetic dataset (5200 records)...")
    records = [generate_record(i) for i in range(5200)]
    df = pd.DataFrame(records)

    out_path = os.path.join(os.path.dirname(__file__), "tickets.csv")
    df.to_csv(out_path, index=False)

    print(f"Dataset saved to: {out_path}")
    print(f"Shape: {df.shape}")
    print("\nPriority Distribution:")
    print(df["priority"].value_counts())
    print("\nIssue Type Distribution:")
    print(df["issue_type"].value_counts())
    return df


if __name__ == "__main__":
    main()
