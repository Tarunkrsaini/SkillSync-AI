import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def generate_roadmap(job_role, skills):

    prompt = f"""
    Create a complete learning roadmap for becoming a professional {job_role}.

    Candidate Skills:
    {', '.join(skills)}

    Include:

    1. Beginner Topics
    2. Intermediate Topics
    3. Advanced Topics
    4. Recommended Projects
    5. Free Learning Resources
    6. Interview Preparation Tips

    Format the response with headings and bullet points.
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