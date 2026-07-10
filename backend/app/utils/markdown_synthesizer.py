def synthesize_candidate_markdown(candidate_profile: dict) -> str:
    """
    Converts a raw JSON candidate profile into a clean, token-efficient Markdown string.
    This prevents LLMs from getting confused by boilerplate JSON keys, UUIDs, and deep nesting.
    """
    profile = candidate_profile.get("profile", {})
    skills = candidate_profile.get("skills", [])
    career_history = candidate_profile.get("career_history", [])
    education = candidate_profile.get("education", [])

    md = []
    
    # 1. Basic Info
    md.append(f"## Candidate: {profile.get('anonymized_name', 'Unknown')}")
    md.append(f"**Current Title:** {profile.get('current_title', 'Unknown')}")
    md.append(f"**Years of Experience:** {profile.get('years_of_experience', 0)}")
    md.append(f"**Location:** {profile.get('location', 'Unknown')}")
    if profile.get("summary"):
        md.append(f"\n**Summary:** {profile.get('summary')}")
        
    # 2. Skills
    if skills:
        skill_names = [s.get("name") for s in skills if isinstance(s, dict)]
        md.append(f"\n## Skills\n{', '.join(skill_names)}")

    # 3. Career History
    if career_history:
        md.append("\n## Career History")
        for job in career_history:
            title = job.get("title", "Unknown Role")
            company = job.get("company_name", "Unknown Company")
            duration = job.get("duration_months", 0)
            md.append(f"- **{title}** at {company} ({duration} months)")
            desc = job.get("description")
            if desc:
                md.append(f"  Description: {desc}")

    # 4. Education
    if education:
        md.append("\n## Education")
        for edu in education:
            degree = edu.get("degree_name", "Unknown Degree")
            school = edu.get("school_name", "Unknown School")
            md.append(f"- {degree} from {school}")

    return "\n".join(md)
