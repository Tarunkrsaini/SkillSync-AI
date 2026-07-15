import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def get_career_advice(skills, job_role, missing_skills):

    prompt = f"""
    The user wants to become a {job_role}.

    Current skills:
    {skills}

    Missing skills:
    {missing_skills}

    Give:
    1. Career advice
    2. Learning roadmap
    3. Recommended projects
    4. Interview preparation tips

    Keep the response simple and student-friendly.
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

def chat_with_coach(messages):
    """
    Passes a list of messages (history) to Groq API.
    Messages should be in format [{"role": "user/assistant", "content": "..."}]
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=1024
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error connecting to AI: {e}"