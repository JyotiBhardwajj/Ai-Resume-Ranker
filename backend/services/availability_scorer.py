"""
Availability Scorer Service

Evaluates how "practically available" a candidate is for hiring based on their
Redrob behavioral signals. A perfect-on-paper candidate who hasn't logged in for
6 months and has a 5% recruiter response rate is, for hiring purposes, not actually available.

From submission_spec.docx:
  "Your ranking system should also weigh behavioral signals — a perfect-on-paper
   candidate who hasn't logged in for 6 months and has a 5% recruiter response rate
   is, for hiring purposes, not actually available. Down-weight them appropriately."

From job_description.docx:
  "Notice period: We'd love sub-30-day notice. We can buy out up to 30 days.
   30+ day notice candidates are still in scope but the bar gets higher."
"""

import logging
from datetime import date, datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)


def calculate_availability_score(redrob_signals: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates an availability score (0–100) based on behavioral signals.

    Args:
        redrob_signals: The redrob_signals dict from a candidate profile.

    Returns:
        Dict with:
            - availability_score (float): 0-100 score (higher = more available)
            - availability_multiplier (float): 0.1 to 1.0 multiplier for final score
            - notes (list[str]): Human-readable availability notes
    """
    if not redrob_signals:
        return {
            "availability_score": 50.0,
            "availability_multiplier": 0.80,
            "notes": ["No behavioral signals available"],
        }

    notes = []
    score = 100.0

    # ---- 1. Open to work flag (critical) ----
    open_to_work = redrob_signals.get("open_to_work_flag", True)
    if not open_to_work:
        score -= 35.0
        notes.append("Not open to work")
    else:
        notes.append("Actively open to work")

    # ---- 2. Last active date (staleness penalty) ----
    last_active_str = redrob_signals.get("last_active_date")
    if last_active_str:
        try:
            last_active = date.fromisoformat(str(last_active_str)[:10])
            today = date.today()
            days_inactive = (today - last_active).days
            months_inactive = days_inactive / 30.0

            if months_inactive > 12:
                score -= 30.0
                notes.append(f"Inactive for {months_inactive:.0f} months (very stale profile)")
            elif months_inactive > 6:
                score -= 20.0
                notes.append(f"Inactive for {months_inactive:.0f} months")
            elif months_inactive > 3:
                score -= 8.0
                notes.append(f"Last active {months_inactive:.0f} months ago")
            else:
                notes.append(f"Recently active ({days_inactive} days ago)")
        except (ValueError, TypeError):
            pass

    # ---- 3. Recruiter response rate (engagement) ----
    response_rate = redrob_signals.get("recruiter_response_rate", 0.5)
    if isinstance(response_rate, (int, float)):
        if response_rate < 0.10:
            score -= 25.0
            notes.append(f"Very low recruiter response rate ({response_rate:.0%})")
        elif response_rate < 0.25:
            score -= 12.0
            notes.append(f"Low recruiter response rate ({response_rate:.0%})")
        elif response_rate < 0.50:
            score -= 4.0
            notes.append(f"Moderate response rate ({response_rate:.0%})")
        else:
            notes.append(f"Good response rate ({response_rate:.0%})")

    # ---- 4. Notice period ----
    notice_days = redrob_signals.get("notice_period_days", 30)
    if isinstance(notice_days, (int, float)):
        if notice_days > 90:
            score -= 15.0
            notes.append(f"Long notice period ({notice_days} days)")
        elif notice_days > 60:
            score -= 8.0
            notes.append(f"Notice period: {notice_days} days")
        elif notice_days <= 30:
            notes.append(f"Short notice period ({notice_days} days) — immediate availability")
        else:
            notes.append(f"Notice period: {notice_days} days")

    # ---- 5. Interview completion rate (reliability signal) ----
    interview_rate = redrob_signals.get("interview_completion_rate", 0.8)
    if isinstance(interview_rate, (int, float)):
        if interview_rate < 0.40:
            score -= 10.0
            notes.append(f"Low interview completion rate ({interview_rate:.0%}) — reliability concern")
        elif interview_rate >= 0.90:
            notes.append(f"High interview reliability ({interview_rate:.0%})")

    # ---- 6. Profile completeness ----
    completeness = redrob_signals.get("profile_completeness_score", 80.0)
    if isinstance(completeness, (int, float)):
        if completeness < 50.0:
            score -= 5.0
            notes.append(f"Incomplete profile ({completeness:.0f}%)")

    # Clamp score to [0, 100]
    score = max(0.0, min(100.0, score))

    # Convert to multiplier (0.1 = severely penalized, 1.0 = fully available)
    # Even the worst candidates get at least a 0.10 multiplier
    multiplier = 0.10 + (score / 100.0) * 0.90
    multiplier = round(multiplier, 3)

    return {
        "availability_score": round(score, 2),
        "availability_multiplier": multiplier,
        "notes": notes,
        "notice_period_days": notice_days if isinstance(notice_days, (int, float)) else 30,
        "response_rate": response_rate if isinstance(response_rate, (int, float)) else 0.5,
    }
