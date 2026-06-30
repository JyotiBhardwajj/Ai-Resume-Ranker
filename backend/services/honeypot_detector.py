"""
Honeypot Detector Service

Detects candidates with subtly impossible profiles that indicate they are
"honeypot" candidates planted by the hackathon judges. These candidates
should be ranked near the bottom.

Honeypot signals (from submission_spec.docx):
  - 8 years of experience at a company founded 3 years ago
  - "expert" proficiency in 10+ skills with 0 months used for all of them
  - Career history with date overlaps exceeding physical possibility
  - Implausibly short tenures across every single role
"""

import logging
from datetime import date, datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)

# IT services / consulting firms where all experience = likely honeypot context
# (used separately in consulting_penalty.py)

# Known company founding estimates (by industry reputation) — rough proxies
# We use company_size + duration_months heuristics since we don't have founding dates


def detect_honeypot(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Checks a raw candidate dict for honeypot signals.

    Args:
        candidate_data: Raw candidate dictionary from JSONL.

    Returns:
        Dict with:
            - is_honeypot (bool): True if profile has impossible signals
            - confidence (float): 0.0 to 1.0 confidence
            - reasons (list[str]): Detected honeypot signals
    """
    reasons = []
    honeypot_score = 0.0

    profile = candidate_data.get("profile", {})
    career_history = candidate_data.get("career_history", [])
    skills = candidate_data.get("skills", [])

    # --- Signal 1: Expert skills with 0 months duration ---
    expert_zero_duration_count = 0
    for skill in skills:
        proficiency = str(skill.get("proficiency", "")).lower()
        duration = skill.get("duration_months")
        if proficiency in ("expert", "advanced") and duration == 0:
            expert_zero_duration_count += 1

    if expert_zero_duration_count >= 5:
        honeypot_score += 0.35
        reasons.append(
            f"{expert_zero_duration_count} expert/advanced skills with 0 months duration"
        )
    elif expert_zero_duration_count >= 3:
        honeypot_score += 0.15
        reasons.append(
            f"{expert_zero_duration_count} expert/advanced skills with 0 months duration"
        )

    # --- Signal 2: Career date overlaps (impossible simultaneous jobs) ---
    date_ranges = []
    for role in career_history:
        start_str = role.get("start_date")
        end_str = role.get("end_date")
        is_current = role.get("is_current", False)

        if not start_str:
            continue
        try:
            start = date.fromisoformat(str(start_str)[:10])
            end = date.today() if is_current or not end_str else date.fromisoformat(str(end_str)[:10])
            date_ranges.append((start, end, role.get("company", "")))
        except (ValueError, TypeError):
            continue

    # Check for significant overlaps (more than 3 months overlap between non-same-company roles)
    overlap_count = 0
    for i in range(len(date_ranges)):
        for j in range(i + 1, len(date_ranges)):
            s1, e1, co1 = date_ranges[i]
            s2, e2, co2 = date_ranges[j]
            if co1.lower().strip() == co2.lower().strip():
                continue  # Same company (internal transfer) is OK
            overlap_start = max(s1, s2)
            overlap_end = min(e1, e2)
            if overlap_start < overlap_end:
                overlap_months = (
                    (overlap_end.year - overlap_start.year) * 12
                    + (overlap_end.month - overlap_start.month)
                )
                if overlap_months > 3:
                    overlap_count += 1

    if overlap_count >= 2:
        honeypot_score += 0.40
        reasons.append(
            f"Career history has {overlap_count} significant date overlaps (impossible simultaneous roles)"
        )
    elif overlap_count == 1:
        honeypot_score += 0.20
        reasons.append("Career history has a date overlap between roles at different companies")

    # --- Signal 3: All roles are implausibly short (all < 3 months, more than 2 roles) ---
    if len(career_history) > 2:
        all_short = all(
            (role.get("duration_months", 12) < 3 and not role.get("is_current", False))
            for role in career_history
        )
        if all_short:
            honeypot_score += 0.30
            reasons.append(
                f"All {len(career_history)} completed roles are under 3 months (implausible)"
            )

    # --- Signal 4: Claimed YoE exceeds sum of career history by huge margin ---
    stated_yoe = profile.get("years_of_experience", 0) or 0
    total_career_months = sum(r.get("duration_months", 0) for r in career_history)
    total_career_years = total_career_months / 12.0

    if stated_yoe > 0 and total_career_years > 0:
        ratio = stated_yoe / max(total_career_years, 0.1)
        if ratio > 3.0 and stated_yoe > 5:
            honeypot_score += 0.25
            reasons.append(
                f"Stated YoE ({stated_yoe:.0f} yrs) is {ratio:.1f}x the total career history months ({total_career_years:.1f} yrs)"
            )

    # --- Signal 5: Suspicious skill count vs total endorsements (keyword stuffing + honeypot) ---
    total_endorsements = sum(s.get("endorsements", 0) for s in skills)
    if len(skills) > 20 and total_endorsements == 0:
        honeypot_score += 0.20
        reasons.append(
            f"{len(skills)} skills listed but 0 total endorsements (keyword stuffing pattern)"
        )

    # Determine honeypot classification
    is_honeypot = honeypot_score >= 0.40
    confidence = min(1.0, honeypot_score)

    if not is_honeypot:
        reasons = []  # Don't report reasons unless flagged

    return {
        "is_honeypot": is_honeypot,
        "confidence": round(confidence, 2),
        "reasons": reasons,
        "honeypot_score": round(honeypot_score, 2),
    }
