def calculate_ats_score(user_skills, required_skills):
    """
    Calculate ATS score based on matching skills.

    Args:
        user_skills (list): Skills extracted from the resume.
        required_skills (list): Skills required for the selected job role.

    Returns:
        int: ATS score (0-100).
    """

    if not required_skills:
        return 0

    matched_skills = 0

    for skill in required_skills:
        if skill.lower() in [s.lower() for s in user_skills]:
            matched_skills += 1

    score = (matched_skills / len(required_skills)) * 100

    return round(score)