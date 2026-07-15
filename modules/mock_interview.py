import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_interview_questions(job_role, difficulty="Medium", category="Technical"):
    try:
        if category == "Government (UPSC/SSC)":
            prompt = f"""
            Generate 10 {difficulty} level interview questions for a Government Job / Civil Services role (like UPSC/SSC) targeted towards a candidate with a {job_role} background.
            
            Include:
            - Policy and Governance Questions
            - General Awareness and Situational Judgement
            - Ethics and Integrity scenarios
            """
        else:
            prompt = f"""
            Generate 10 {difficulty} level {category} interview questions for a {job_role}.

            Include:
            - {category} specific questions
            - Scenario-based Questions
            """
            
            if category in ["Technical", "Technical / IT", "Coding / System Design"]:
                prompt += "- For Data Structures and Algorithms questions, explicitly provide a relevant LeetCode problem name and its URL (e.g. https://leetcode.com/problems/two-sum/) to practice."

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

    except Exception as e:
        return f"Error: {e}"