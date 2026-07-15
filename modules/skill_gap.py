JOB_SKILLS = {

    "Data Scientist": [
        "Python",
        "SQL",
        "Machine Learning",
        "Pandas",
        "Numpy",
        "Deep Learning"
    ],

    "AI/ML Engineer": [
        "Python",
        "Machine Learning",
        "Deep Learning",
        "Tensorflow",
        "Pandas",
        "Numpy"
    ],

    "Web Developer": [
        "HTML",
        "CSS",
        "JavaScript",
        "Git",
        "Github"
    ],

    "Frontend Developer": [
        "HTML",
        "CSS",
        "JavaScript",
        "React",
        "Git"
    ],

    "Backend Developer": [
        "Python",
        "SQL",
        "Git",
        "Github"
    ],

    "Full Stack Developer": [
        "HTML",
        "CSS",
        "JavaScript",
        "Python",
        "SQL",
        "Git",
        "Github"
    ],

    "Software Engineer": [
        "Python",
        "Java",
        "C++",
        "SQL",
        "Git"
    ],
    
    "Cloud Engineer": [
        "AWS",
        "Azure",
        "Docker",
        "Kubernetes",
        "Linux",
        "Networking"
    ]
}

GOVT_EXAMS = {
    "UPSC Civil Services": [
        "Polity & Constitution",
        "History & Culture",
        "Geography",
        "Economics",
        "General Science",
        "Current Affairs",
        "Ethics & Aptitude"
    ],
    "SSC CGL": [
        "Quantitative Aptitude",
        "General Intelligence & Reasoning",
        "General Awareness",
        "English Comprehension"
    ],
    "Bank PO / Clerk": [
        "Quantitative Aptitude",
        "Reasoning Ability",
        "English Language",
        "General/Economy/Banking Awareness",
        "Computer Aptitude"
    ],
    "NDA / CDS (Defense)": [
        "Mathematics",
        "General Ability Test",
        "English",
        "Physics & Chemistry",
        "General Science",
        "Current Affairs"
    ],
    "State PCS": [
        "State History & Geography",
        "General Studies",
        "Polity & Governance",
        "Aptitude Test (CSAT)"
    ]
}


def get_skill_gap(user_skills, job_role):
    if job_role in GOVT_EXAMS:
        required_skills = GOVT_EXAMS[job_role]
    else:
        required_skills = JOB_SKILLS.get(job_role, [])

    missing_skills = []

    for skill in required_skills:
        if skill not in user_skills:
            missing_skills.append(skill)

    return missing_skills