import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def generate_cover_letter(name, job_role, skills):

    prompt = f"""
    Write a highly unique, engaging, and professional cover letter.
    Do not use generic, robotic templates. Make it sound passionate, modern, and stand out to top recruiters.

    Candidate Name: {name}
    Applying For: {job_role}
    Skills: {', '.join(skills)}

    Keep it professional, one page, and highlight how the candidate's skills make them an exceptional fit for an innovative team.
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