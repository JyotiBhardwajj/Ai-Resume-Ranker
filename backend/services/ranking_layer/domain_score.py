class DomainScoreEngine:
    """
    Evaluates how well a candidate's career history aligns with the Job Description's domain.
    """
    
    @staticmethod
    def calculate_domain_fit(jd_domain: str, candidate_career_history: list) -> float:
        """
        Calculates a 0-100 score based on domain overlap.
        
        Args:
            jd_domain: The industry/domain from the JD (e.g., "IT Services").
            candidate_career_history: List of career history dicts from the candidate profile.
            
        Returns:
            float: Domain fit score (0 to 100).
        """
        if not jd_domain:
            return 50.0  # Neutral score if JD domain is unspecified
            
        jd_domain_lower = jd_domain.lower().strip()
        
        total_months = 0
        domain_months = 0
        
        for role in candidate_career_history:
            duration = role.get("duration_months", 0)
            total_months += duration
            
            role_industry = role.get("industry", "").lower().strip()
            # Simple exact or substring match for domain
            if jd_domain_lower in role_industry or role_industry in jd_domain_lower:
                domain_months += duration
                
        if total_months == 0:
            return 0.0
            
        # Calculate percentage of career spent in this domain
        domain_ratio = domain_months / total_months
        
        # Scale to 0-100
        score = domain_ratio * 100.0
        return round(score, 2)
