def extract_skills(text):
    
    skills_list = [
        "python",
        "java",
        "c++",
        "javascript",
        "html",
        "css",
        "sql",
        "machine learning",
        "deep learning",
        "data science",
        "streamlit",
        "tensorflow",
        "pandas",
        "numpy",
        "opencv",
        "git",
        "github",
        "react",
        "node.js",
        "mongodb",
        "express"
    ]

    found_skills = []

    text = text.lower()

    for skill in skills_list:
        if skill in text:
            found_skills.append(skill.title())

    return found_skills