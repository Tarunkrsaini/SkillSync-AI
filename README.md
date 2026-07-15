# 🚀 SkillSync AI - Your Personal AI Career Copilot

SkillSync AI is a premium, glassmorphism-themed, AI-powered web application built to help professionals, college students, and government exam aspirants audit their skills, track syllabi, prepare for interviews, and build dynamic career roadmaps.

---

## ✨ Features

### 1. Dual Career Tracks
*   **Corporate & Tech Pathway**:
    *   **ATS Resume Audit**: Upload your resume PDF, extract technical skills, and analyze your ATS Score against industry requirements.
    *   **Interactive Skills Gap**: Dynamically logs missing skills and offers up-skilling targets.
    *   **LeetCode Live Tracker**: Connect your LeetCode profile dynamically via our GraphQL API integration to see your real-time problems solved statistics on your dashboard!
*   **Government Exams Pathway**:
    *   **Syllabus Coverage Tracker**: Interactive, checklist-based tracker for UPSC Civil Services, SSC CGL, State PCS, and Bank PO syllabus subjects without forcing resume uploads.
    *   **Relevant Recommendations**: Excludes coding references, displaying General Studies (GS), NCERT guides, History, Geography, and Quantitative Aptitude roadmaps instead.

### 2. 🎤 AI Voice Board Room (Speech-to-Text & Text-to-Speech)
*   **AI Speech Output (TTS)**: The AI panel interviewer and Career Coach speak back to you in a high-quality female voice using the browser's native SpeechSynthesis API. Toggle voice feedback on/off or click "Listen Again" or "Stop Speaking".
*   **User Speech Input (STT)**: Speak your answers or ask questions using browser SpeechRecognition (STT), automatically transcribing your voice into the text input area.

### 3. 📝 Premium Resume Builder
*   Generate print-ready HTML resume templates directly on the dashboard.
*   Choose between 3 distinct professional layouts:
    *   📘 **Minimalist Blue** (Classic single-column style)
    *   📓 **Modern Slate** (Executive two-column style with a dark sidebar)
    *   💚 **Elegant Emerald** (Centered serif style with clean emerald borders)

### 4. 🤖 AI Career Coach
*   Interactive, contextual chatbot backed by Groq AI. Ask about career pathways, project benchmarks, reference studies, and salary ranges.

---

## 🛠️ Technology Stack
*   **Frontend & Application Core**: Streamlit (Python)
*   **Styling**: Custom CSS (radial glassmorphism system)
*   **Database**: SQLite3 (for local user session, social links, and LeetCode configs)
*   **APIs & AI Models**: Groq Cloud LLM APIs, LeetCode Public GraphQL API
*   **Audio Core**: Browser HTML5 Web Speech API (SpeechSynthesis & webkitSpeechRecognition)

---

## 📦 Installation & Setup

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/Tarunkrsaini/SkillSync-AI.git
    cd SkillSync-AI
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Server**:
    ```bash
    streamlit run app.py
    ```

---

## 📂 Codebase Directory Structure
*   `app.py` - Core Streamlit frontend controller & page engine.
*   `modules/` - Logic handlers (Auth, LeetCode API, ATS Scanner, Resume Builder, Career Advisor, and Interview generation).
*   `assets/` - Custom UI stylesheets (`style.css`), logos, and user profile photo buffers.
*   `database/` - SQLite3 schemas storing user information.
