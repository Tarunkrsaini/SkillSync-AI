import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def analyze_resume(resume_text):

    prompt = f"""
    Analyze the following resume.

    Resume:

    {resume_text}

    Give:

    1. Overall Resume Score (out of 100)
    2. Strengths
    3. Weaknesses
    4. Missing Skills
    5. Resume Formatting Suggestions
    6. ATS Improvement Tips
    7. Final Recommendation

    Use headings and bullet points.
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content