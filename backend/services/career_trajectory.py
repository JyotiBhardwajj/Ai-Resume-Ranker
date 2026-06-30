import logging
from datetime import datetime
from typing import Dict, List, Any

from backend.models.candidate import Candidate, CareerHistory
from backend.services.career_parser import (
    get_seniority_level, 
    get_role_complexity, 
    is_leadership_role, 
    extract_from_candidate as extract_career_summary
)

logger = logging.getLogger(__name__)


def calculate_month_gap(end_date_str: str, start_date_str: str) -> int:
    """
    Helper to calculate gap in months between two date strings of format YYYY-MM-DD.
    """
    if not end_date_str or not start_date_str:
        return 0
    try:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        if start_date <= end_date:
            return 0
        diff_months = (start_date.year - end_date.year) * 12 + (start_date.month - end_date.month)
        return max(0, diff_months)
    except Exception:
        return 0


class CareerTrajectoryScorer:
    """
    Scorer service to compute Career Trajectory Score based on promotions,
    seniority growth, leadership progression, role progression, and career consistency.
    """

    @classmethod
    def calculate_score(cls, candidate: Candidate) -> Dict[str, Any]:
        """
        Calculates a trajectory score (0 to 100) and extracts key metrics.

        Args:
            candidate: Validated Candidate model instance.

        Returns:
            Dictionary containing career_trajectory_score, growth_summary,
            promotion_count, and leadership_roles count.
        """
        career_history = candidate.career_history
        N = len(career_history)
        if N == 0:
            return {
                "career_trajectory_score": 0,
                "growth_summary": "No professional career history listed.",
                "promotion_count": 0,
                "leadership_roles": 0
            }

        # Sort chronologically (oldest first)
        sorted_roles = sorted(career_history, key=lambda x: str(x.start_date))

        # 1. Map Seniority, Complexity, and Leadership indicators
        roles_data = []
        for role in sorted_roles:
            sl = get_seniority_level(role.title)
            cl = get_role_complexity(role.title)
            has_lead_kw = is_leadership_role(role.title, role.description)
            roles_data.append({
                "company": role.company,
                "title": role.title,
                "description": role.description,
                "sl": sl,
                "cl": cl,
                "duration_months": role.duration_months,
                "is_current": role.is_current,
                "start_date": role.start_date,
                "end_date": role.end_date,
                "has_lead_kw": has_lead_kw
            })

        # --- 2. Calculate S_promotions ---
        promotion_count = 0
        for i in range(N - 1):
            co1 = roles_data[i]["company"].lower().strip()
            co2 = roles_data[i+1]["company"].lower().strip()
            if co1 == co2:
                if roles_data[i+1]["sl"] > roles_data[i]["sl"]:
                    promotion_count += 1
        s_promotions = min(promotion_count * 25, 100)

        # --- 3. Calculate S_progression ---
        cl_initial = roles_data[0]["cl"]
        cl_latest = roles_data[-1]["cl"]
        if cl_initial >= 3 and cl_latest >= 3:
            s_progression = 90.0
        else:
            diff = cl_latest - cl_initial
            s_progression = max(0.0, min(100.0, 50.0 + diff * 15.0))

        # --- 4. Calculate S_seniority ---
        total_yoe = candidate.profile.years_of_experience
        sl_initial = roles_data[0]["sl"]
        sl_latest = roles_data[-1]["sl"]
        delta_sl = sl_latest - sl_initial

        if delta_sl >= 0:
            if sl_initial >= 3 and sl_latest >= 3:
                s_seniority = 90.0
            else:
                velocity = delta_sl / max(total_yoe, 1.0)
                s_seniority = min((velocity / 0.25) * 50.0 + 50.0, 100.0)
        else:
            s_seniority = max(0.0, 50.0 + delta_sl * 25.0)

        # --- 5. Calculate S_leadership ---
        cli = 0.0
        leadership_roles = 0
        for r in roles_data:
            lc = 0.0
            if r["sl"] == 5:
                lc = 1.0
            elif r["sl"] == 4:
                lc = 0.6
            elif r["sl"] == 3 and r["has_lead_kw"]:
                lc = 0.3
            
            if lc > 0.0:
                leadership_roles += 1

            duration_years = r["duration_months"] / 12.0
            cli += lc * duration_years
        s_leadership = min(cli * 20.0, 100.0)

        # --- 6. Calculate S_consistency ---
        p_hop = 0
        p_gap = 0
        p_stag = 0

        # Job-hopping (Exclude currently active roles)
        for r in roles_data:
            if not r["is_current"] and r["duration_months"] < 12:
                p_hop += 15

        # Gaps
        for i in range(N - 1):
            # Format dates to extract gap
            d1_end = roles_data[i]["end_date"]
            d2_start = roles_data[i+1]["start_date"]
            if d1_end and d2_start:
                gap = calculate_month_gap(str(d1_end), str(d2_start))
                if gap > 3:
                    p_gap += (gap - 3) * 10
        p_gap = min(p_gap, 40)  # cap gap penalty

        # Stagnation
        if total_yoe >= 8 and sl_latest <= 2:
            p_stag = 20

        s_consistency = max(0.0, 100.0 - p_hop - p_gap - p_stag)

        # --- 7. Final Weighted CTS ---
        # 20% Promotions, 20% Progression, 20% Seniority, 20% Leadership, 20% Consistency
        cts = (s_promotions * 0.2) + (s_progression * 0.2) + (s_seniority * 0.2) + (s_leadership * 0.2) + (s_consistency * 0.2)
        cts = int(round(cts))

        # --- 8. Generate growth summary explanation ---
        summary_parts = []
        if promotion_count > 0:
            summary_parts.append(f"{promotion_count} internal promotion(s)")
        if sl_latest > sl_initial:
            summary_parts.append("clear seniority progression")
        if leadership_roles > 0:
            summary_parts.append(f"{leadership_roles} role(s) with leadership/mentoring duties")
        if s_consistency >= 80.0:
            summary_parts.append("high employment consistency")
        else:
            summary_parts.append("some employment transitions")

        growth_summary = "Candidate demonstrates " + ", ".join(summary_parts) + f". Stated peak seniority level is {sl_latest}."

        return {
            "career_trajectory_score": cts,
            "growth_summary": growth_summary,
            "promotion_count": promotion_count,
            "leadership_roles": leadership_roles
        }
