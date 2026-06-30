"""
Consulting Penalty Service

Detects candidates whose entire career has been at large IT services / consulting firms
with no product-company experience. Per the JD requirements, these candidates should be
down-weighted as they historically show poor fit for an AI-native product startup.

From the actual job_description.docx:
  "People who have only worked at consulting firms (TCS, Infosys, Wipro, Accenture,
   Cognizant, Capgemini, etc.) in their entire career. We've had bad fit experiences
   in both directions. If you're currently at one of these companies but have prior
   product-company experience, that's fine."
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Comprehensive list of known IT services / consulting firms
IT_SERVICES_FIRMS = {
    # Indian IT Giants
    "tcs", "tata consultancy services", "tata consultancy",
    "infosys", "infy",
    "wipro",
    "hcl", "hcl technologies", "hcltech",
    "tech mahindra", "techmahindra",
    "mphasis",
    "mindtree",
    "hexaware",
    "ltimindtree", "lti", "l&t infotech", "larsen & toubro infotech",
    "persistent systems", "persistent",
    "niit technologies",
    "mastech", "mastech digital",
    "zensar", "zensar technologies",
    "eclerx",
    "cyient",
    "sonata software",
    "kpit technologies",
    "sasken",

    # Global Consulting / Outsourcing
    "accenture",
    "cognizant", "cognizant technology solutions",
    "capgemini",
    "ibm", "ibm global services",
    "deloitte",
    "ey", "ernst & young",
    "kpmg",
    "pwc", "pricewaterhousecoopers",
    "mckinsey", "mckinsey & company",
    "bcg", "boston consulting group",
    "bain & company", "bain",
    "booz allen", "booz allen hamilton",
    "leidos",
    "unisys",
    "cgi group", "cgi",
    "dxc technology", "dxc",
    "ntt data",
    "atos",
    "fujitsu",
    "igate", "igate patni",
    "patni computer systems",
    "genpact",
    "wns", "wns global services",
    "firstsource",
    "teleperformance",

    # IT Staffing firms
    "infosys bpo",
    "wipro bpo",
    "tcs bpo",
    "accenture operations",
}


def get_consulting_penalty(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates whether a candidate has spent their entire career at consulting/IT services firms.

    Args:
        candidate_data: Raw candidate dictionary from JSONL.

    Returns:
        Dict with:
            - penalty_score (float): 0.0 (no penalty) to 1.0 (full consulting career, maximum penalty)
            - is_consulting_only (bool): True if ALL roles are at consulting firms
            - has_product_experience (bool): True if any role is at a non-consulting company
            - consulting_months (int): Total months at consulting firms
            - product_months (int): Total months at product companies
    """
    career_history = candidate_data.get("career_history", [])

    if not career_history:
        return {
            "penalty_score": 0.0,
            "is_consulting_only": False,
            "has_product_experience": False,
            "consulting_months": 0,
            "product_months": 0,
        }

    consulting_months = 0
    product_months = 0

    for role in career_history:
        company = role.get("company", "").lower().strip()
        duration = role.get("duration_months", 0) or 0
        industry = role.get("industry", "").lower().strip()

        # Check if company name or industry matches consulting firms
        is_consulting = False

        # Check exact or substring match of company name
        for firm in IT_SERVICES_FIRMS:
            if firm in company or company in firm:
                is_consulting = True
                break

        # Also check industry field
        if not is_consulting:
            consulting_industries = {
                "it services", "information technology services",
                "staffing", "staffing & recruiting",
                "outsourcing", "bpo", "business process outsourcing",
                "consulting", "management consulting",
                "professional services",
            }
            for ci in consulting_industries:
                if ci in industry:
                    is_consulting = True
                    break

        if is_consulting:
            consulting_months += duration
        else:
            product_months += duration

    total_months = consulting_months + product_months

    if total_months == 0:
        return {
            "penalty_score": 0.0,
            "is_consulting_only": False,
            "has_product_experience": False,
            "consulting_months": 0,
            "product_months": 0,
        }

    consulting_ratio = consulting_months / total_months
    has_product_experience = product_months > 0
    is_consulting_only = not has_product_experience

    # Penalty is proportional to consulting ratio
    # Pure consulting career → full penalty (0.40 score multiplier)
    # Mostly consulting with some product → moderate penalty
    # Mostly product → minimal or no penalty
    if consulting_ratio >= 0.95:
        penalty_score = 0.80  # Heavy penalty — entire career at consulting firms
    elif consulting_ratio >= 0.75:
        penalty_score = 0.45  # Moderate penalty — mostly consulting
    elif consulting_ratio >= 0.50:
        penalty_score = 0.20  # Mild penalty — balanced
    else:
        penalty_score = 0.0  # No penalty — mostly product experience

    return {
        "penalty_score": penalty_score,
        "is_consulting_only": is_consulting_only,
        "has_product_experience": has_product_experience,
        "consulting_months": consulting_months,
        "product_months": product_months,
        "consulting_ratio": round(consulting_ratio, 2),
    }
