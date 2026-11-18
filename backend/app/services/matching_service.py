from typing import List, Dict, Any, Optional

def calculate_skill_match(
    candidate_skills: List[str],
    job_required_skills: List[str]
) -> Dict[str, Any]:
    """
    Deterministic skill overlap calculator with edge-case handling.
    
    Edge case:
    If a job description specifies no required skills, returns match_score: None
    along with an explanatory message.
    """
    # Clean and normalize sets
    cand_set = {s.strip().lower() for s in candidate_skills if s and s.strip()}
    job_set = {s.strip().lower() for s in job_required_skills if s and s.strip()}
    
    # Edge case: No required skills on the job
    if len(job_set) == 0:
        return {
            "match_score": None,
            "matched_skills": [],
            "missing_skills": [],
            "recommendations": "No required skills are listed for this job. Review the full job description to determine suitability.",
            "message": "This job does not specify any required skills. Match score cannot be calculated."
        }
        
    matched_set = cand_set.intersection(job_set)
    missing_set = job_set.difference(cand_set)
    
    score = round((len(matched_set) / len(job_set)) * 100.0, 1)
    
    # Original case mapping for display
    matched_skills = [s for s in job_required_skills if s.strip().lower() in matched_set]
    missing_skills = [s for s in job_required_skills if s.strip().lower() in missing_set]
    
    # Actionable gap recommendation
    if score >= 80.0:
        recommendation = "High match! You meet the primary skill requirements for this role. We strongly recommend applying."
    elif score >= 50.0:
        missing_str = ", ".join(missing_skills[:5])
        recommendation = f"Moderate match ({score}%). You possess a strong baseline. To improve your chances, highlight any projects or experience with: {missing_str}."
    else:
        missing_str = ", ".join(missing_skills[:5])
        recommendation = f"Low match ({score}%). This position requires essential skills you currently lack, including: {missing_str}. Consider upskilling before applying."
        
    return {
        "match_score": score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "recommendations": recommendation,
        "message": f"Skill match analysis complete: {len(matched_skills)} of {len(job_required_skills)} required skills matched."
    }
