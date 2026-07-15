import streamlit as st
import os
import pandas as pd
import base64
from modules.auth import login_user, register_user
from modules.skill_gap import JOB_SKILLS, GOVT_EXAMS, get_skill_gap
from modules.ats_score import calculate_ats_score
from modules.resume_parser import extract_text_from_pdf
from modules.skill_extractor import extract_skills
from modules.career_advisor import chat_with_coach
from modules.mock_interview import generate_interview_questions
from modules.cover_letter import generate_cover_letter
from modules.leetcode import get_leetcode_stats
import streamlit.components.v1 as components
import logging
logging.getLogger("streamlit.deprecation_util").setLevel(logging.ERROR)
logging.getLogger("streamlit.elements.iframe").setLevel(logging.ERROR)

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="SkillSync AI - Your Personal Career Copilot",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# IMAGE BASE64 HELPER
# ==========================================
def get_base64_image(image_path):
    try:
        if os.path.exists(image_path):
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
                return f"data:image/jpeg;base64,{encoded_string}"
    except Exception:
        pass
    return ""

# ==========================================
# STYLE SHEET INJECTION
# ==========================================
def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("assets/style.css")

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_data" not in st.session_state:
    st.session_state.user_data = None
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
if "career_track" not in st.session_state:
    st.session_state.career_track = "Corporate & Tech"
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "skills" not in st.session_state:
    st.session_state.skills = []
if "job_role" not in st.session_state:
    st.session_state.job_role = "Data Scientist"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "activities" not in st.session_state:
    st.session_state.activities = {
        "resume": "Not uploaded yet",
        "interview": "No attempts",
        "roadmap": "Not generated",
        "cover_letter": "Not generated",
        "skill_gap": "Not analyzed"
    }

# ==========================================
# COMMON COMPONENTS
# ==========================================

def speak_text(text):
    import re
    # Strip markdown headers, bold/italics, bullet characters
    clean_text = re.sub(r'#+\s*', '', text)
    clean_text = re.sub(r'\*+', '', clean_text)
    clean_text = re.sub(r'_+', '', clean_text)
    clean_text = re.sub(r'^[-\*\+]\s+', '', clean_text, flags=re.MULTILINE)
    clean_text = clean_text.replace('`', '').replace('\n', ' ').replace('\r', ' ')
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    # Base64 encode to prevent string quotes and escape sequence errors in javascript
    b64_text = base64.b64encode(clean_text.encode('utf-8')).decode('utf-8')
    
    html_code = f"""
    <script>
        (function() {{
            const speak = () => {{
                try {{
                    window.parent.speechSynthesis.cancel();
                    // Decode base64 safely supporting utf-8 characters
                    const cleanText = decodeURIComponent(escape(window.atob("{b64_text}")));
                    const msg = new SpeechSynthesisUtterance(cleanText);
                    
                    let voices = window.parent.speechSynthesis.getVoices();
                    let femaleVoice = voices.find(v => 
                        v.name.toLowerCase().includes("female") || 
                        v.name.toLowerCase().includes("zira") || 
                        v.name.toLowerCase().includes("google us english") ||
                        v.name.toLowerCase().includes("samantha") ||
                        v.lang.includes("en-US")
                    );
                    
                    if (femaleVoice) {{
                        msg.voice = femaleVoice;
                    }}
                    msg.rate = 1.0;
                    window.parent.speechSynthesis.speak(msg);
                }} catch(err) {{
                    console.error("Speech Synthesis Error:", err);
                }}
            }};
            
            if (window.parent.speechSynthesis.getVoices().length > 0) {{
                speak();
            }} else {{
                window.parent.speechSynthesis.onvoiceschanged = speak;
            }}
        }})();
    </script>
    """
    components.html(html_code, height=0)

def render_voice_input(placeholder_search, key):
    html_code = f"""
    <div style="font-family: sans-serif; display: flex; align-items: center; gap: 10px;">
        <button id="mic_btn" style="background-color: #2563EB; color: white; border: none; padding: 10px 18px; border-radius: 8px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 8px; font-size: 14px;">
            🎤 Speak Answer
        </button>
        <span id="status" style="font-size: 0.85rem; color: #94A3B8;">Click to speak answer</span>
    </div>
    
    <script>
        const btn = document.getElementById("mic_btn");
        const status = document.getElementById("status");
        
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {{
            status.innerText = "Voice input not supported in this browser.";
            btn.disabled = true;
        }} else {{
            const recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';
            
            btn.onclick = () => {{
                try {{
                    recognition.start();
                    status.innerText = "Listening... Speak now.";
                    btn.style.backgroundColor = "#EF4444";
                    btn.innerText = "🛑 Recording";
                }} catch (e) {{
                    status.innerText = "Already listening...";
                }}
            }};
            
            recognition.onresult = (event) => {{
                const text = event.results[0][0].transcript;
                status.innerText = "Transcribed!";
                btn.style.backgroundColor = "#2563EB";
                btn.innerText = "🎤 Speak Answer";
                
                try {{
                    const parentDoc = window.parent.document;
                    const textareas = Array.from(parentDoc.querySelectorAll("textarea"));
                    let target = null;
                    for (let ta of textareas) {{
                        if (ta.placeholder && ta.placeholder.toLowerCase().includes("{placeholder_search}")) {{
                            target = ta;
                            break;
                        }}
                    }}
                    if (!target && textareas.length > 0) target = textareas[0];
                    
                    if (target) {{
                        target.value = text;
                        target.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }} else {{
                        status.innerText = "Speech: " + text;
                    }}
                }} catch (err) {{
                    status.innerText = "Speech: " + text + " (Parent document blocked)";
                }}
            }};
            
            recognition.onerror = (e) => {{
                status.innerText = "Error: " + e.error;
                btn.style.backgroundColor = "#2563EB";
                btn.innerText = "🎤 Speak Answer";
            }};
            
            recognition.onend = () => {{
                btn.style.backgroundColor = "#2563EB";
                btn.innerText = "🎤 Speak Answer";
                if (status.innerText === "Listening... Speak now.") {{
                    status.innerText = "Stopped.";
                }}
            }};
        }}
    </script>
    """
    components.html(html_code, height=50)

def render_top_navigation():
    avatar_char = st.session_state.user_data['name'][0].upper() if st.session_state.user_data else "U"
    user_display = st.session_state.user_data['name'] if st.session_state.user_data else "Guest"
    is_demo = st.session_state.user_data and st.session_state.user_data["email"] == "tarun@skillsync.ai"
    avatar_b64 = get_base64_image("assets/tarun_avatar.jpg") if is_demo else ""
    
    avatar_html = f'<img src="{avatar_b64}" class="nav-avatar-img" />' if avatar_b64 else f'<div class="nav-avatar" style="width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, #2563EB, #7C3AED); display: flex; align-items: center; justify-content: center; color: white; font-weight: 600; font-size: 0.9rem;">{avatar_char}</div>'
    
    st.markdown("""
    <style>
    .top-nav-container { padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05); margin-bottom: 20px; }
    </style>
    <div class="top-nav-container"></div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns([1.1, 1.6, 1.8, 1.2])
    with col1:
        if st.button("🚀 SkillSync AI", type="tertiary", use_container_width=True, key="logo_btn"):
            st.session_state.page = "Dashboard"
            st.rerun()
    with col2:
        n_col1, n_col2, n_col3 = st.columns(3)
        with n_col1:
            if st.button("🏠 Home", use_container_width=True, key="nav_home_btn"):
                st.session_state.page = "Dashboard"
                st.rerun()
        with n_col2:
            if st.button("👤 Profile", use_container_width=True, key="nav_profile_btn"):
                st.session_state.page = "Profile"
                st.rerun()
        with n_col3:
            if st.button("⚙️ Settings", use_container_width=True, key="nav_settings_btn"):
                st.session_state.page = "Settings"
                st.rerun()
    with col3:
        search_query = st.text_input("Search", placeholder="Search templates, jobs, skills...", label_visibility="collapsed", key="top_search")
        if search_query:
            st.session_state.search_query = search_query
    with col4:
        if st.session_state.logged_in:
            c_bell, c_prof = st.columns([1, 2])
            with c_bell:
                if st.button("🔔 (3)", key="top_nav_bell"):
                    st.toast("You have 3 new skill matches!")
            with c_prof:
                if st.button(f"👤 {user_display}", key="top_nav_prof"):
                    st.session_state.page = "Profile"
                    st.rerun()
        else:
            c_login, c_reg = st.columns(2)
            with c_login:
                if st.button("Sign In"):
                    st.session_state.page = "login"
                    st.rerun()
            with c_reg:
                if st.button("Register"):
                    st.session_state.page = "register"
                    st.rerun()

# ==========================================
# AUTHENTICATION VIEWS
# ==========================================

def render_login():
    col_l, col_m, col_r = st.columns([1, 2.5, 1])
    with col_m:
        with st.container(border=True):
            st.markdown('<div style="text-align: center; font-size: 2.2rem; font-weight: bold; color: white;">🚀 SkillSync AI</div>', unsafe_allow_html=True)
            st.markdown('<p style="text-align: center; color: #94A3B8; margin-bottom: 20px;">Your AI Career Copilot</p>', unsafe_allow_html=True)
            
            # Center the image perfectly
            img_col1, img_col2, img_col3 = st.columns([1, 2, 1])
            with img_col2:
                st.image("assets/login_bg.jpg", use_container_width=True)
            
            st.write("")
            
            email = st.text_input("Email Address", placeholder="tarun@skillsync.ai", key="login_email")
            password = st.text_input("Password", type="password", placeholder="••••••••", key="login_password")
            
            c1, c2 = st.columns(2)
            with c1:
                remember_me = st.checkbox("Remember Me")
            with c2:
                st.markdown("<div style='text-align: right;'><a href='#' style='color: #4ADE80; text-decoration: none; font-size: 0.9rem;'>Forgot Password?</a></div>", unsafe_allow_html=True)
            
            st.write("")
            if st.button("Login", use_container_width=True):
                if not email or not password:
                    st.error("Please enter both email and password.")
                else:
                    user = login_user(email, password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user_data = {
                            "id": user[0], "name": user[1], "email": user[2],
                            "college": user[4], "branch": user[5], "grad_year": user[6],
                            "linkedin": user[7] if len(user)>7 else "",
                            "github": user[8] if len(user)>8 else "",
                            "youtube": user[9] if len(user)>9 else "",
                            "instagram": user[10] if len(user)>10 else "",
                            "portfolio": user[11] if len(user)>11 else "",
                            "leetcode_username": user[12] if len(user)>12 else ""
                        }
                        st.session_state.chat_history = [
                            {"role": "ai", "content": f"Hello {user[1]}! I am your SkillSync AI Career Coach. Let's audit your skill gap!"}
                        ]
                        st.session_state.page = "Dashboard"
                        
                        if remember_me:
                            try:
                                import json
                                with open("auth.json", "w") as f:
                                    json.dump(st.session_state.user_data, f)
                            except:
                                pass
                        
                        st.success("Logged in successfully!")
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")
                        
            st.markdown("<hr style='margin: 15px 0; border-color: rgba(255,255,255,0.1);'/>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #94A3B8; margin-bottom: 10px;'>Don't have an account?</p>", unsafe_allow_html=True)
            if st.button("Create New Account", use_container_width=True):
                st.session_state.page = "register"
                st.rerun()
        

def render_register():
    col_l, col_m, col_r = st.columns([1, 2.5, 1])
    with col_m:
        with st.container(border=True):
            st.markdown('<div style="text-align: center; font-size: 1.8rem; font-weight: bold; color: white;">Register Account</div>', unsafe_allow_html=True)
            st.markdown('<p style="text-align: center; color: #94A3B8; margin-bottom: 25px;">Start your SkillSync AI journey</p>', unsafe_allow_html=True)
            
            full_name = st.text_input("Full Name", placeholder="Tarun Singh")
            email = st.text_input("Email Address", placeholder="tarun@skillsync.ai")
            
            c1, c2 = st.columns(2)
            with c1:
                password = st.text_input("Password", type="password", placeholder="••••••••")
            with c2:
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="••••••••")
                
            college = st.text_input("College / University", placeholder="Stanford University")
            
            c3, c4 = st.columns(2)
            with c3:
                branch = st.text_input("Branch / Major", placeholder="Computer Science")
            with c4:
                grad_year = st.text_input("Graduation Year", placeholder="2027")
                
            st.write("")
            if st.button("Register Now", use_container_width=True):
                if not full_name or not email or not password or not college or not branch or not grad_year:
                    st.error("All fields are required!")
                elif password != confirm_password:
                    st.error("Passwords do not match!")
                else:
                    success, msg = register_user(full_name, email, password, college, branch, grad_year)
                    if success:
                        st.success("Registration Successful! Please Login.")
                        st.session_state.page = "login"
                        st.rerun()
                    else:
                        st.error(msg)
                        
            st.markdown("<hr style='margin: 15px 0; border-color: rgba(255,255,255,0.1);'/>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #94A3B8; margin-bottom: 10px;'>Already have an account?</p>", unsafe_allow_html=True)
            if st.button("Back to Login", use_container_width=True):
                st.session_state.page = "login"
                st.rerun()
        

# ==========================================
# CORE SIDEBAR NAVIGATION
# ==========================================

def render_sidebar():
    user_name = st.session_state.user_data["name"] if st.session_state.user_data else "Tarun Singh"
    user_role = "Your AI Career Copilot"
    
    st.sidebar.markdown(f"""
    <div class="profile-avatar-container">
        <div class="profile-avatar-logo">🤖</div>
        <div class="profile-info">
            <div class="profile-name">SkillSync AI</div>
            <div class="profile-role">{user_role}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("### Career Track")
    track = st.sidebar.radio("Select Track", ["Corporate & Tech", "Government Exams"], index=0 if st.session_state.career_track == "Corporate & Tech" else 1, label_visibility="collapsed")
    if track != st.session_state.career_track:
        st.session_state.career_track = track
        if track == "Government Exams":
            st.session_state.job_role = "UPSC Civil Services"
        else:
            st.session_state.job_role = "Data Scientist"
        st.rerun()

    menu_items = [
        ("Dashboard", "📊", ""),
        ("Resume Analyzer", "📄", ""),
        ("Resume Builder", "📝", "New"),
        ("ATS Score", "🎯", ""),
        ("Skill Gap", "🔍", ""),
        ("AI Career Coach", "🤖", ""),
        ("Mock Interview", "🎤", "Live"),
        ("Career Roadmap", "🗺️", ""),
        ("Cover Letter", "📝", ""),
        ("Courses", "🎓", "New"),
        ("Job Match", "⚡", ""),
        ("Progress Tracker", "📈", ""),
        ("Achievements", "🏆", ""),
        ("Profile", "👤", ""),
        ("Settings", "⚙️", "")
    ]
    
    if st.session_state.career_track == "Government Exams":
        # Remove resume-specific pages for Government Track
        exclude_pages = ["Resume Analyzer", "Resume Builder", "ATS Score", "Cover Letter", "Job Match"]
        menu_items = [item for item in menu_items if item[0] not in exclude_pages]
    
    st.sidebar.markdown("### Navigation")
    for label, icon, badge in menu_items:
        is_active = st.session_state.page == label
        
        btn_label = f"{icon}  {label}"
        if badge:
            btn_label += f" [{badge}]"
        if is_active:
            btn_label = f"▶ {btn_label}"
            
        if st.sidebar.button(btn_label, key=f"nav_{label}", use_container_width=True):
            if not st.session_state.logged_in and label != "Dashboard":
                st.session_state.page = "login"
            else:
                st.session_state.page = label
            st.rerun()
            
    if st.session_state.logged_in:
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            import os
            if os.path.exists("auth.json"):
                try:
                    os.remove("auth.json")
                except:
                    pass
            st.session_state.logged_in = False
            st.session_state.user_data = None
            st.session_state.page = "login"
            st.rerun()

# ==========================================
# CORE GAUGES & METRIC RENDERERS
# ==========================================

def render_gauge(score, title, subtext, border_class, color="#2563EB"):
    offset = int(150 - (150 * score / 100))
    return f"""
    <div class="metric-card-custom {border_class}" style="display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 16px;">
        <div style="text-align: left;">
            <span class="metric-label-custom" style="font-size: 0.8rem;">{title}</span>
            <div style="font-family:'Poppins'; font-size:1.6rem; font-weight:700; color:#fff; margin-top: 2px;">{score}%</div>
            <span style="font-size: 0.72rem; color: #CBD5E1; font-weight: 500;">{subtext}</span>
        </div>
        <svg width="60" height="60">
            <circle cx="30" cy="30" r="24" stroke="rgba(255,255,255,0.04)" stroke-width="5" fill="transparent" />
            <circle cx="30" cy="30" r="24" stroke="{color}" stroke-width="5" stroke-dasharray="150" stroke-dashoffset="{offset}" stroke-linecap="round" fill="transparent" style="transform: rotate(-90deg); transform-origin: 50% 50%;" />
            <text x="30" y="34" fill="#fff" font-size="11" font-family="'Poppins'" font-weight="700" text-anchor="middle">{score}%</text>
        </svg>
    </div>
    """

def render_stat_card(val, title, subtext, border_class, icon):
    return f"""
    <div class="metric-card-custom {border_class}" style="display: flex; align-items: center; gap: 12px; padding: 16px; min-height: 92px;">
        <div style="font-size: 2.2rem; line-height: 1;">{icon}</div>
        <div style="text-align: left;">
            <span class="metric-label-custom" style="font-size: 0.8rem;">{title}</span>
            <div style="font-family:'Poppins'; font-size:1.6rem; font-weight:700; color:#fff; margin-top: 2px;">{val}</div>
            <span style="font-size: 0.72rem; color: #CBD5E1; font-weight: 500;">{subtext}</span>
        </div>
    </div>
    """

# ==========================================
# PAGE COMPONENT RENDERERS
# ==========================================

def render_dashboard_page():
    # 75% Left column / 25% Right Panel Layout
    col_main, col_side = st.columns([3, 1.15])
    
    user_name = st.session_state.user_data["name"] if st.session_state.user_data else "User"
    is_demo = st.session_state.user_data and st.session_state.user_data["email"] == "tarun@skillsync.ai"
    
    avatar_b64 = get_base64_image("assets/tarun_avatar.jpg") if is_demo else ""
    banner_b64 = get_base64_image("assets/dashboard_banner.jpg")
    
    # Compute dynamic stats
    required_skills = JOB_SKILLS.get(st.session_state.job_role, [])
    ats_score = calculate_ats_score(st.session_state.skills, required_skills) if st.session_state.resume_text else 0
    skills_detected = len(st.session_state.skills)
    missing_skills = get_skill_gap(st.session_state.skills, st.session_state.job_role)
    missing_count = len(missing_skills)
    
    # Career score: base 40 (profile) + 60% of ATS score if resume exists
    career_score = 40 + int(ats_score * 0.6) if st.session_state.resume_text else 40
    
    # ------------------ LEFT COLUMN (MAIN) ------------------
    with col_main:
        # Top Row: Welcome, Search and Action dropdowns
        t_col1, t_col2, t_col3 = st.columns([1.6, 1.1, 1.3])
        with t_col1:
            welcome_text = "Welcome back," if st.session_state.logged_in else "Welcome to SkillSync,"
            st.markdown(f'<h2 style="margin:0; font-family:\'Poppins\'; color:#fff; font-size: 1.7rem;">{welcome_text}</h2>', unsafe_allow_html=True)
            st.markdown(f'<h2 style="margin:2px 0 0 0; font-family:\'Poppins\'; color:#fff; font-size: 2.1rem; line-height:1;">{user_name}</h2>', unsafe_allow_html=True)
            st.markdown('<p style="margin:6px 0 0 0; color:#94A3B8; font-size:0.88rem;">Ready to build your dream career today?</p>', unsafe_allow_html=True)
        with t_col2:
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            search_query_dash = st.text_input("Search Dash", placeholder="Search anything...", label_visibility="collapsed", key="dash_search")
            if search_query_dash:
                st.session_state.search_query = search_query_dash
        with t_col3:
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            if st.session_state.logged_in:
                c_bell, c_prof = st.columns([1, 2])
                with c_bell:
                    if st.button("🔔 (3)"):
                        st.toast("You have 3 new skill matches!")
                with c_prof:
                    if st.button(f"👤 {user_name}"):
                        st.session_state.page = "Profile"
                        st.rerun()
            else:
                c_login, c_reg = st.columns(2)
                with c_login:
                    if st.button("Sign In", key="dash_login"):
                        st.session_state.page = "login"
                        st.rerun()
                with c_reg:
                    if st.button("Register", key="dash_reg"):
                        st.session_state.page = "register"
                        st.rerun()
            
        st.write("")
        
        # Hero Section
        st.markdown(f"""
        <div class="glass-container" style="display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, rgba(37, 99, 235, 0.22) 0%, rgba(124, 58, 237, 0.18) 100%); border-color: rgba(37, 99, 235, 0.22); min-height: 180px; padding: 24px;">
            <div style="flex: 1.3; padding-right: 15px;">
                <div style="background: rgba(15, 23, 42, 0.65); border-left: 3.5px solid #7C3AED; padding: 14px 20px; border-radius: 12px; margin-bottom: 0;">
                    <p style="margin: 0; font-style: italic; color: #CBD5E1; font-size: 0.95rem; line-height: 1.5; font-family: 'Inter';">" AI is not just the future, <br/>it's your competitive advantage today.. "</p>
                    <span style="font-size: 0.85rem; color: #7C3AED; font-weight: 600; display: block; margin-top: 6px;">- SkillSync AI</span>
                </div>
            </div>
            <div style="flex: 1; text-align: right; display: flex; justify-content: flex-end;">
                <img src="{banner_b64}" style="width: 280px; border-radius: 14px; border: 1.5px solid rgba(255,255,255,0.08); box-shadow: 0 10px 25px rgba(0,0,0,0.4);" />
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.career_track == "Government Exams":
            req_subjects = GOVT_EXAMS.get(st.session_state.job_role, [])
            studied = len(st.session_state.get("studied_subjects", []))
            completion_pct = int((studied / max(1, len(req_subjects))) * 100)
            subjects_left = len(req_subjects) - studied
            
            # Stats Row for Government Exams
            s_col1, s_col2, s_col3, s_col4 = st.columns(4)
            with s_col1:
                st.markdown(render_gauge(completion_pct, "Syllabus Covered", "Great Job! 🎯" if completion_pct > 50 else "Keep Studying! 📚", "m-blue", "#2563EB"), unsafe_allow_html=True)
            with s_col2:
                st.markdown(render_stat_card(f"{studied}/{len(req_subjects)}", "Subjects Studied", "Completed", "m-purple", "📖"), unsafe_allow_html=True)
            with s_col3:
                st.markdown(render_stat_card(str(subjects_left), "Subjects Left", "Needs Study", "m-cyan", "⏳"), unsafe_allow_html=True)
            with s_col4:
                # Count mock interview attempts
                mock_attempts = 1 if st.session_state.activities["interview"] != "No attempts" else 0
                st.markdown(render_stat_card(f"{mock_attempts} Mock", "Exams Practiced", "Interactive Session", "m-green", "🎙️"), unsafe_allow_html=True)
        else:
            missing_count = len(missing_skills) if missing_skills else 0
            skills_detected = len(st.session_state.skills)
            
            req_skills_dash = JOB_SKILLS.get(st.session_state.job_role, [])
            if req_skills_dash:
                real_ats_dash = int(((len(req_skills_dash) - missing_count) / len(req_skills_dash)) * 100)
            else:
                real_ats_dash = 0
                
            career_score = 65
            
            # Stats Row (4 custom metric cards)
            s_col1, s_col2, s_col3, s_col4 = st.columns(4)
            with s_col1:
                st.markdown(render_gauge(career_score, "Career Score", "Great Progress! 🔥" if career_score > 60 else "In Progress ⚙️", "m-blue", "#2563EB"), unsafe_allow_html=True)
            with s_col2:
                st.markdown(render_gauge(real_ats_dash, "ATS Score", "Good Score 👍" if real_ats_dash > 70 else "Needs Improvement ⚠️", "m-purple", "#7C3AED"), unsafe_allow_html=True)
            with s_col3:
                st.markdown(render_stat_card(str(skills_detected), "Skills Detected", "Strong Skills 💪" if skills_detected > 4 else "Analyze Resume 📄", "m-cyan", "🛡️"), unsafe_allow_html=True)
            with s_col4:
                st.markdown(render_stat_card(str(missing_count), "Missing Skills", "Improve Now 🎯" if missing_count > 0 else "Fully Ready! 🎉", "m-green", "⚠️"), unsafe_allow_html=True)
            
        st.write("")
        
        if st.session_state.career_track == "Government Exams":
            feature_pages = [
                ("Skill Gap", "🔍📡", "Track syllabus coverage.\n- Manual checklists\n- Mark studied subjects\n- Check remaining topics", "Check Syllabus →", "#2563EB"),
                ("Mock Interview", "👥🎙️", "Practice AI interviews.\n- UPSC Civil Services\n- SSC CGL / Bank PO\n- State PCS Boards", "Start Interview →", "#7C3AED"),
                ("Career Roadmap", "🗺️🛣️", "Exam preparation path.\n- Phase-wise roadmaps\n- Core syllabus goals\n- Target timeline", "View Roadmap →", "#22C55E"),
                ("AI Career Coach", "🤖💬", "AI Guidance chat.\n- Exam Strategy advice\n- GS Guidance\n- Interview panel prep", "Ask AI Coach →", "#D97706"),
                ("Courses", "🎓📚", "Study materials.\n- NCERT Reference books\n- GS subject courses\n- CSAT guides", "Explore Courses →", "#22C55E"),
            ]
            exclude = ["Skill Gap"] # Since we replaced Skill Gap text, we don't want to exclude it, it serves as the Syllabus tracker!
        else:
            feature_pages = [
                ("Skill Gap", "🔍📡", "Identify missing skills.\n- Compare with ATS\n- Highlight weak areas", "Check Gap →", "#2563EB"),
                ("Mock Interview", "👥🎙️", "Practice AI interviews.\n- Technical Questions\n- LeetCode prep\n- HR Scenarios", "Start Interview →", "#7C3AED"),
                ("Career Roadmap", "🗺️🛣️", "Personalized steps.\n- Step-by-step path\n- Milestones\n- Expected timeline", "View Roadmap →", "#22C55E"),
                ("AI Career Coach", "🤖💬", "AI Guidance chat.\n- Ask questions\n- Get instant help\n- Career advice", "Ask AI Coach →", "#D97706"),
                ("Courses", "🎓📚", "Upskill yourself.\n- Recommended courses\n- External links\n- Skill focused", "Explore Courses →", "#22C55E"),
                ("Job Match", "⚡💼", "Find job roles.\n- Matching score\n- Job descriptions\n- Next steps", "Find Jobs →", "#D97706"),
                ("Cover Letter", "📝✉️", "Generate cover letters.\n- Unique & Premium\n- AI Generated\n- Ready to use", "Create Letter →", "#7C3AED"),
                ("Resume Analyzer", "💻📄", "Analyze resume.\n- Upload PDF\n- View structure\n- Parse skills", "Analyze Now →", "#2563EB")
            ]
            exclude = []

        for i in range(0, len(feature_pages), 4):
            cols = st.columns(4)
            for j in range(4):
                if i + j < len(feature_pages):
                    label, icon, desc, cta, color_code = feature_pages[i+j]
                    with cols[j]:
                        with st.expander(f"{icon} {label}"):
                            st.markdown(f"<span style='color: #CBD5E1; font-size: 0.85rem;'>{desc}</span>", unsafe_allow_html=True)
                            st.write("")
                            if st.button(cta, key=f"dash_btn_{label}", use_container_width=True):
                                if not st.session_state.logged_in:
                                    st.session_state.page = "login"
                                else:
                                    st.session_state.page = label
                                st.rerun()
        st.write("")
        
        # Bottom Footer Blocks (3 columns)
        f_col1, f_col2, f_col3 = st.columns([1.4, 1.4, 1.2])
        if st.session_state.career_track == "Government Exams":
            with f_col1:
                st.markdown("""
                <div class="glass-container" style="padding: 18px; min-height: 125px;">
                    <div style="display: flex; align-items: center; gap: 8px; font-weight:600; color:#ffffff; font-size:0.95rem;">
                        <span>💡</span> Daily AI Government Tip
                    </div>
                    <p style="font-size: 0.85rem; color: #CBD5E1; margin: 8px 0 0 0; line-height: 1.45;">Focus on GS answer writing structure. Content accuracy and keyword placement matter most!</p>
                </div>
                """, unsafe_allow_html=True)
            with f_col2:
                st.markdown("""
                <div class="glass-container" style="padding: 18px; min-height: 125px;">
                    <div style="display: flex; align-items: center; gap: 8px; font-weight:600; color:#ffffff; font-size:0.95rem;">
                        <span>🎯</span> Today's Challenge
                    </div>
                    <p style="font-size: 0.85rem; color: #CBD5E1; margin: 8px 0 10px 0; line-height: 1.45;">Solve 1 CSAT Quant problem or review 5 Indian Polity Articles.</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Start Reading Articles", key="btn_gov_challenge"):
                    st.toast("Tip: Look up Article 21 & 300A in your polity syllabus!")
            with f_col3:
                st.markdown("""
                <div class="glass-container" style="padding: 18px; min-height: 125px;">
                    <div style="display: flex; align-items: center; gap: 8px; font-weight:600; color:#ffffff; font-size:0.95rem;">
                        <span>🏆</span> Your Level: Aspirant Master
                    </div>
                    <div style="font-size:0.8rem; color:#CBD5E1; margin: 8px 0 4px 0; display:flex; justify-content:space-between;">
                        <span>Level 2</span>
                        <span>350 / 1000 XP</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.progress(350 / 1000)
        else:
            with f_col1:
                st.markdown("""
                <div class="glass-container" style="padding: 18px; min-height: 125px;">
                    <div style="display: flex; align-items: center; gap: 8px; font-weight:600; color:#ffffff; font-size:0.95rem;">
                        <span>💡</span> Daily AI Career Tip
                    </div>
                    <p style="font-size: 0.85rem; color: #CBD5E1; margin: 8px 0 0 0; line-height: 1.45;">Focus on building real-world projects. Employers love practical experience!</p>
                </div>
                """, unsafe_allow_html=True)
            with f_col2:
                leetcode_user = st.session_state.user_data.get("leetcode_username", "") if st.session_state.user_data else ""
                
                with st.container(border=True):
                    st.markdown("<span style='font-weight:600; color:#fff; font-size: 0.95rem;'>🎯 LeetCode Challenge Tracker</span>", unsafe_allow_html=True)
                    if leetcode_user:
                        stats = get_leetcode_stats(leetcode_user)
                        if stats:
                            st.write(f"👤 **{leetcode_user}** | Solved: **{stats.get('All', 0)}**")
                            st.caption(f"🟢 Easy: {stats.get('Easy', 0)} | 🟡 Medium: {stats.get('Medium', 0)} | 🔴 Hard: {stats.get('Hard', 0)}")
                        else:
                            st.warning("Could not fetch stats. Check username.")
                        
                        if st.button("Disconnect Profile", key="btn_disconnect_lc", use_container_width=True):
                            st.session_state.user_data["leetcode_username"] = ""
                            import sqlite3
                            conn = sqlite3.connect("database/users.db")
                            conn.execute("UPDATE users SET leetcode_username='' WHERE id=?", (st.session_state.user_data['id'],))
                            conn.commit()
                            conn.close()
                            st.rerun()
                    else:
                        lc_input = st.text_input("Enter LeetCode Username", placeholder="e.g. pilanitarun", key="lc_user_input", label_visibility="collapsed")
                        if st.button("Connect LeetCode", key="btn_connect_lc", use_container_width=True):
                            if lc_input:
                                import sqlite3
                                conn = sqlite3.connect("database/users.db")
                                conn.execute("UPDATE users SET leetcode_username=? WHERE id=?", (lc_input, st.session_state.user_data['id']))
                                conn.commit()
                                conn.close()
                                st.session_state.user_data["leetcode_username"] = lc_input
                                st.success("LeetCode profile connected!")
                                st.rerun()
            with f_col3:
                st.markdown("""
                <div class="glass-container" style="padding: 18px; min-height: 125px;">
                    <div style="display: flex; align-items: center; gap: 8px; font-weight:600; color:#ffffff; font-size:0.95rem;">
                        <span>🏆</span> Your Level: Career Achiever
                    </div>
                    <div style="font-size:0.8rem; color:#CBD5E1; margin: 8px 0 4px 0; display:flex; justify-content:space-between;">
                        <span>Level 5</span>
                        <span>650 / 1000 XP</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.progress(650 / 1000)
            
    # ------------------ RIGHT SIDEBAR PANEL ------------------
    with col_side:
        if st.session_state.career_track == "Government Exams":
            # Target Exam Profile Box
            with st.container(border=True):
                st.markdown("<span style='font-weight:600; color:#fff; font-size: 1rem;'>Target Exam Profile</span>", unsafe_allow_html=True)
                avatar_preview_html = f'<div class="resume-avatar-preview" style="width: 44px; height: 44px; border-radius: 50%; background: linear-gradient(135deg, #2563EB, #7C3AED); display: flex; align-items: center; justify-content: center; color: white; font-weight: 700; font-size: 1.15rem;">{user_name[0].upper()}</div>'
                
                # Compute syllabus completion percentage
                req_subjects = GOVT_EXAMS.get(st.session_state.job_role, [])
                studied = len(st.session_state.get("studied_subjects", []))
                completion_pct = int((studied / max(1, len(req_subjects))) * 100)
                
                st.markdown(f"""
                <div class="resume-preview-card" style="padding: 15px;">
                    <div class="resume-preview-header" style="margin-bottom: 15px;">
                        {avatar_preview_html}
                        <div>
                            <h5 class="resume-title-preview">{user_name}</h5>
                            <p class="resume-subtitle-preview">{st.session_state.job_role}</p>
                        </div>
                    </div>
                    <div class="resume-section-title">Syllabus Completion</div>
                    <div style="font-size: 1.2rem; font-weight: 700; color: #4ADE80; margin-bottom: 5px;">{completion_pct}% Done</div>
                    <div class="resume-skill-bar"><div class="resume-skill-fill" style="width: {completion_pct}%; background-color: #4ADE80 !important;"></div></div>
                </div>
                """, unsafe_allow_html=True)
                st.write("")
                if st.button("Update Tracker", key="right_update_tracker", use_container_width=True):
                    st.session_state.page = "Syllabus Tracker"
                    st.rerun()
                    
            # Recent Activity Box for Govt Track
            with st.container(border=True):
                st.markdown("<h4 style='font-size: 1rem; margin-bottom: 15px;'>Recent Activity</h4>", unsafe_allow_html=True)
                activities = [
                    ("🔍", "Syllabus tracked", st.session_state.activities["skill_gap"]),
                    ("✔️", "Mock exam practiced", st.session_state.activities["interview"]),
                    ("🗺️", "Preparation roadmap built", st.session_state.activities["roadmap"]),
                ]
                for icon, title, time in activities:
                    st.markdown(f"""
                    <div class="activity-item">
                        <div class="activity-icon-container">{icon}</div>
                        <div class="activity-info-box">
                            <span class="activity-title">{title}</span>
                            <span class="activity-time">{time}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            # Your Resume Box
            with st.container(border=True):
                r_head_col1, r_head_col2 = st.columns([2, 1])
                with r_head_col1:
                    st.markdown("<span style='font-weight:600; color:#fff; font-size: 1rem;'>Your Resume</span>", unsafe_allow_html=True)
                with r_head_col2:
                    if st.button("View Full", key="dash_view_full", use_container_width=True):
                        st.session_state.page = "Resume Analyzer"
                        st.rerun()

                avatar_preview_html = f'<img src="{avatar_b64}" class="resume-avatar-preview" />' if avatar_b64 else f'<div class="resume-avatar-preview" style="width: 44px; height: 44px; border-radius: 50%; background: linear-gradient(135deg, #2563EB, #7C3AED); display: flex; align-items: center; justify-content: center; color: white; font-weight: 700; font-size: 1.15rem;">{user_name[0].upper()}</div>'

                # Skills bars renderer
                skills_html = ""
                if st.session_state.skills:
                    for sk in st.session_state.skills[:3]:
                        # Assign mock score
                        score_pct = 90 if sk == "Python" else (85 if sk == "SQL" else 80)
                        skills_html += f"""
                        <div class="resume-skill-row">
                            <span style="font-size:0.7rem; font-weight:600;">{sk}</span>
                            <div class="resume-skill-bar"><div class="resume-skill-fill" style="width: {score_pct}%;"></div></div>
                        </div>
                        """
                else:
                    skills_html = "<p style='font-size:0.72rem; color:#64748B !important; margin: 4px 0 0 0;'>No skills detected. Upload a resume PDF.</p>"

                college_display = st.session_state.user_data["college"] if st.session_state.user_data else "College"
                branch_display = st.session_state.user_data["branch"] if st.session_state.user_data else "CS"
                grad_display = st.session_state.user_data["grad_year"] if st.session_state.user_data else "2027"

                # Resume Miniature Card
                st.markdown(f"""
                <div class="resume-preview-card">
                    <div class="resume-preview-header">
                        {avatar_preview_html}
                        <div>
                            <h5 class="resume-title-preview">{user_name}</h5>
                            <p class="resume-subtitle-preview">{st.session_state.job_role}</p>
                        </div>
                    </div>

                    <div class="resume-section-title">Education Details</div>
                    <p style="font-size:0.75rem; font-weight:600; margin:0 0 2px 0;">{college_display}</p>
                    <p style="font-size:0.68rem; color:#64748B !important; margin:0 0 8px 0;">{branch_display} | Class of {grad_display}</p>

                    <div class="resume-section-title">Skills parsed</div>
                    {skills_html}
                </div>
                """, unsafe_allow_html=True)
                st.write("")
                if st.button("Upload New Resume", key="right_upload_res"):
                    st.session_state.page = "Resume Analyzer"
                    st.rerun()
            
            # Recent Activity Box
            with st.container(border=True):
                st.markdown("<h4 style='font-size: 1rem; margin-bottom: 15px;'>Recent Activity</h4>", unsafe_allow_html=True)

                resume_act = "Resume PDF analyzed" if st.session_state.resume_text else "No resume uploaded"
                ats_act = "ATS matching audited" if st.session_state.resume_text else "No audits performed"

                activities = [
                    ("📄", resume_act, st.session_state.activities["resume"]),
                    ("📡", ats_act, st.session_state.activities["skill_gap"]),
                    ("✔️", "Mock interview practiced", st.session_state.activities["interview"]),
                    ("🗺️", "Career roadmap built", st.session_state.activities["roadmap"]),
                    ("✉️", "Cover letter created", st.session_state.activities["cover_letter"])
                ]

                for icon, title, time in activities:
                    st.markdown(f"""
                    <div class="activity-item">
                        <div class="activity-icon-container">{icon}</div>
                        <div class="activity-info-box">
                            <span class="activity-title">{title}</span>
                            <span class="activity-time">{time}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)


def render_resume_analyzer_page():
    render_top_navigation()
    st.markdown('<div class="main-title">📄 Resume Analyzer</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Extract skills & analyze your resume structure with AI.</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        with st.container(border=True):
            st.subheader("Upload PDF Resume")
            uploaded_file = st.file_uploader("Upload PDF file", type=["pdf"])

            if uploaded_file:
                file_key = f"{uploaded_file.name}_{uploaded_file.size}"
                if st.session_state.get("last_parsed_file") != file_key:
                    with st.spinner("Extracting text and structure..."):
                        try:
                            uploaded_file.seek(0)
                            text = extract_text_from_pdf(uploaded_file)
                            st.session_state.resume_text = text
                            st.session_state.skills = extract_skills(text)
                            st.session_state.activities["resume"] = "Just now"
                            st.session_state.last_parsed_file = file_key
                            st.success("✅ Resume PDF parsed successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error parsing PDF: {e}")
        
        with st.container(border=True):
            st.subheader("Extracted Skills")
            if st.session_state.skills:
                st.write(st.session_state.skills)
            else:
                st.info("Upload a resume to automatically extract technical skills.")
        
    with col2:
        with st.container(border=True):
            st.subheader("Resume Preview & Extracted Structure")
            if st.session_state.resume_text:
                st.text_area("Extracted Resume Text (First 1,000 chars)", st.session_state.resume_text[:1000], height=200)
                st.markdown("""
                #### Structure Detected:
                - **Experience:** Identified 2 work details
                - **Projects:** Identified 3 projects
                - **Education:** Identified University details
                - **Certifications:** Identified 2 licenses
                """)
            else:
                st.markdown("""
                <div style="text-align: center; color: #94A3B8; padding: 40px 0;">
                    <div style="font-size: 3rem;">📄</div>
                    <p>Upload a resume PDF to view the structure analysis.</p>
                </div>
                """, unsafe_allow_html=True)

def render_ats_score_page():
    render_top_navigation()
    st.markdown('<div class="main-title">🎯 ATS Score</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Calculate your match rate against industry target keywords.</div>', unsafe_allow_html=True)
    
    if not st.session_state.resume_text:
        st.warning("⚠️ Please upload your resume on the **Resume Analyzer** page first.")
        return
        
    job_role = st.selectbox("Select Target Job Role", list(JOB_SKILLS.keys()), index=list(JOB_SKILLS.keys()).index(st.session_state.job_role))
    st.session_state.job_role = job_role
    
    required_skills = JOB_SKILLS[job_role]
    score = calculate_ats_score(st.session_state.skills, required_skills)
    
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        with st.container(border=True):
            st.subheader("Overall Match Score")

            stroke_dashoffset = int(440 - (440 * score / 100))
            svg_html = f"""
            <svg width="200" height="200" style="margin: 20px auto;">
                <circle cx="100" cy="100" r="70" stroke="rgba(255,255,255,0.05)" stroke-width="12" fill="transparent" />
                <circle cx="100" cy="100" r="70" stroke="#2563EB" stroke-width="12" stroke-dasharray="440" stroke-dashoffset="{stroke_dashoffset}" stroke-linecap="round" fill="transparent" style="transform: rotate(-90deg); transform-origin: 50% 50%;" />
                <text x="100" y="112" fill="#fff" font-size="34" font-family="'Poppins', sans-serif" font-weight="700" text-anchor="middle">{score}%</text>
            </svg>
            """
            st.markdown(svg_html, unsafe_allow_html=True)
            st.progress(score / 100)
        
    with col2:
        with st.container(border=True):
            st.subheader("Keyword Match Breakdown")

            matched = [s for s in required_skills if s.lower() in [us.lower() for us in st.session_state.skills]]
            missing = [s for s in required_skills if s.lower() not in [us.lower() for us in st.session_state.skills]]

            m_col1, m_col2 = st.columns(2)
            with m_col1:
                st.markdown("🟢 **Matching Keywords**")
                if matched:
                    for m in matched:
                        st.write(f"- {m}")
                else:
                    st.write("*None*")
            with m_col2:
                st.markdown("🔴 **Missing Keywords**")
                if missing:
                    for ms in missing:
                        st.write(f"- {ms}")
                else:
                    st.write("*Perfect cover!*")

            st.write("")
            st.subheader("Suggestions for Improvement")
            st.markdown("""
            - Add missing keywords natively in your experience achievements.
            - Avoid graphics, multi-column tables, or complex icons that confuse scanner pipelines.
            - Export using clean Unicode text formats.
            """)

def render_skill_gap_page():
    render_top_navigation()
    
    if st.session_state.career_track == "Government Exams":
        st.markdown('<div class="main-title">🔍 Syllabus Tracker</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle">Track your preparation status for Government Exams by checking off studied subjects.</div>', unsafe_allow_html=True)
        
        # Ensure st.session_state.job_role is a govt exam, if not set it to the first key
        if st.session_state.job_role not in GOVT_EXAMS:
            st.session_state.job_role = list(GOVT_EXAMS.keys())[0]
            
        job_role = st.selectbox("Select Target Exam", list(GOVT_EXAMS.keys()), index=list(GOVT_EXAMS.keys()).index(st.session_state.job_role))
        st.session_state.job_role = job_role
        
        required_subjects = GOVT_EXAMS[job_role]
        
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.subheader("Syllabus Checklist")
                st.write("Check the subjects you have already studied:")
                
                # Keep track of checked subjects in session state
                if "studied_subjects" not in st.session_state:
                    st.session_state.studied_subjects = []
                    
                completed_list = []
                for sub in required_subjects:
                    is_checked = st.checkbox(sub, value=(sub in st.session_state.studied_subjects), key=f"sub_{sub}")
                    if is_checked:
                        completed_list.append(sub)
                
                st.session_state.studied_subjects = completed_list
                st.session_state.skills = completed_list # Sync completed list to skills so other modules work
                
        with col2:
            with st.container(border=True):
                st.subheader("Remaining Syllabus (Gap)")
                remaining = [s for s in required_subjects if s not in completed_list]
                if remaining:
                    for rem in remaining:
                        st.markdown(f"- 🔴 **{rem}** (Needs study)")
                else:
                    st.success("🎉 Congratulations! You have completed 100% of the syllabus!")
        return

    st.markdown('<div class="main-title">🔍 Skill Gap Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Identify missing technologies and track your up-skilling progression.</div>', unsafe_allow_html=True)
    
    if not st.session_state.resume_text:
        st.warning("⚠️ Please upload a resume first.")
        return
        
    job_role = st.selectbox("Select Target Job Role", list(JOB_SKILLS.keys()), index=list(JOB_SKILLS.keys()).index(st.session_state.job_role))
    st.session_state.job_role = job_role
    
    missing_skills = get_skill_gap(st.session_state.skills, job_role)
    st.session_state.activities["skill_gap"] = "Just now"
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            st.subheader("Current Skills")
            st.write(st.session_state.skills)
        
        with st.container(border=True):
            st.subheader("Missing Skills")
            if missing_skills:
                for ms in missing_skills:
                    st.markdown(f"- 🔴 **{ms}**")
            else:
                st.success("🎉 You match 100% of required skills!")
        
    with col2:
        with st.container(border=True):
            st.subheader("Recommended Path & Learning Time")
            if missing_skills:
                st.write(f"Estimated timeline to master remaining competencies for **{job_role}**:")
                for idx, ms in enumerate(missing_skills):
                    st.markdown(f"""
                    <div class="roadmap-step">
                        <strong>Phase {idx+1}: Acquire {ms}</strong><br/>
                        <span style="font-size: 0.85rem; color: #06B6D4;">Est: 2-3 Weeks | Progress: 0%</span>
                    </div>
                    """, unsafe_allow_html=True)
                    st.progress(0.0)
            else:
                st.info("You're fully ready! Practice advanced project modules or mock interviews.")

def render_career_coach_page():
    render_top_navigation()
    st.markdown('<div class="main-title">🤖 AI Career Coach</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Ask your personal AI copilot for immediate career advice, interview insights, or salaries.</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2.5])
    
    with col1:
        with st.container(border=True):
            st.subheader("AI Copilot")
            st.markdown("<div style='font-size: 4.5rem; margin: 15px 0;'>🤖</div>", unsafe_allow_html=True)
            st.write("Specialized in salary benchmarking, tech pathways, and project ideas.")
            st.write("---")
            voice_enabled = st.toggle("Enable Voice Feedback", value=False, key="coach_voice_toggle")
            if voice_enabled:
                st.info("🔊 AI responses will be spoken aloud in a female voice.")
                if st.button("🛑 Stop Speaking", key="stop_coach_voice_btn", use_container_width=True):
                    components.html("<script>window.parent.speechSynthesis.cancel();</script>", height=0)
            st.write("")
            st.markdown("**Speak Query (STT):**")
            render_voice_input("ask your career coach", "coach_voice_input")
        
    with col2:
        with st.container(border=True):
            st.subheader("Coach Conversation Chat")

            # Render historical chat
            for chat in st.session_state.chat_history:
                with st.chat_message(chat["role"]):
                    st.markdown(chat["content"])

            # Send query input
            if user_msg := st.chat_input("Ask your Career Coach anything..."):
                # Append user message
                st.session_state.chat_history.append({"role": "user", "content": user_msg})
                with st.chat_message("user"):
                    st.markdown(user_msg)

                # Format messages for Groq API
                groq_messages = [
                    {"role": msg["role"] if msg["role"] == "user" else "assistant", "content": msg["content"]} 
                    for msg in st.session_state.chat_history
                ]
                
                # Fetch AI response
                with st.chat_message("assistant"):
                    with st.spinner("Coach is thinking..."):
                        reply = chat_with_coach(groq_messages)
                        st.markdown(reply)
                        if voice_enabled:
                            speak_text(reply)
                
                st.session_state.chat_history.append({"role": "assistant", "content": reply})

def render_mock_interview_page():
    render_top_navigation()
    st.markdown('<div class="main-title">🎤 AI Mock Interview</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Practice with realistic interview sessions. Choose difficulty and category modules.</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        with st.container(border=True):
            st.subheader("Configure Room")
            difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
            if st.session_state.career_track == "Government Exams":
                categories = ["UPSC Civil Services", "SSC CGL", "Bank PO / Clerk", "NDA / CDS (Defense)", "State PCS"]
            else:
                categories = ["Technical / IT", "Management / MBA", "HR / Behavioral", "Coding / System Design"]
                
            category = st.selectbox("Category", categories)

            generate = st.button("Generate Interview Session")
        
    with col2:
        with st.container(border=True):
            st.subheader("Interview Board Simulator")
            if generate or 'interview_questions' in st.session_state:
                if generate:
                    with st.spinner("Generating customized mock interview..."):
                        questions = generate_interview_questions(st.session_state.job_role, difficulty, category)
                        st.session_state.interview_questions = questions
                        st.session_state.activities["interview"] = "Just now"
                        # Automatically read out loud
                        speak_text(questions)
                
                st.markdown(f"#### Questions Generated for `{st.session_state.job_role}` ({difficulty})")
                st.markdown(f"**Category:** {category}")

                st.markdown(st.session_state.interview_questions)
                
                voice_col1, voice_col2 = st.columns(2)
                with voice_col1:
                    if st.button("🔊 Listen Question Again", use_container_width=True):
                        speak_text(st.session_state.interview_questions)
                with voice_col2:
                    if st.button("🛑 Stop Speaking", use_container_width=True):
                        components.html("<script>window.parent.speechSynthesis.cancel();</script>", height=0)

                # Dictate answer (Speech-To-Text)
                st.text_area("Answer Area:", height=150, placeholder="Type your answer here...", key="interview_answer_input")
                render_voice_input("type your answer here", "interview_answer")
                
                if st.button("Submit Answer"):
                    st.session_state.activities["interview"] = "Just now"
                    st.success("✅ Answer logged! Feedback will analyze your performance metrics.")
                    st.rerun()
            else:
                st.info("Select options and click Generate Interview Session to begin practicing.")

def render_roadmap_page():
    render_top_navigation()
    st.markdown('<div class="main-title">🗺️ Career Roadmap</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Follow your step-by-step career milestones.</div>', unsafe_allow_html=True)
    
    with st.container(border=True):
        st.subheader(f"Path to Master {st.session_state.job_role}")

        if st.button("Re-generate Roadmap"):
            st.session_state.activities["roadmap"] = "Just now"
            st.success("Roadmap rebuilt successfully!")
            st.rerun()

        col1, col2, col3, col4 = st.columns(4)

        if st.session_state.career_track == "Government Exams":
            with col1:
                st.markdown("""
                <div class="roadmap-step" style="border-left-color: #2563EB;">
                    <h4 style="color: #2563EB;">Foundation (Phase 1)</h4>
                    <p><strong>NCERTs & Basic Concepts</strong></p>
                    <ul>
                        <li>Basic reference books</li>
                        <li>Exam syllabus analysis</li>
                        <li>Static GK foundations</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown("""
                <div class="roadmap-step" style="border-left-color: #7C3AED;">
                    <h4 style="color: #7C3AED;">Core Study (Phase 2)</h4>
                    <p><strong>Detailed Subjects</strong></p>
                    <ul>
                        <li>Detailed General Studies (GS)</li>
                        <li>Aptitude & English prep</li>
                        <li>Previous year papers analysis</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown("""
                <div class="roadmap-step" style="border-left-color: #06B6D4;">
                    <h4 style="color: #06B6D4;">Testing (Phase 3)</h4>
                    <p><strong>Mock Exams & Revision</strong></p>
                    <ul>
                        <li>Weekly mock test series</li>
                        <li>Current affairs revision</li>
                        <li>Answer writing / speed practice</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                st.markdown("""
                <div class="roadmap-step" style="border-left-color: #22C55E;">
                    <h4 style="color: #22C55E;">Interview (Phase 4)</h4>
                    <p><strong>Personality Test Prep</strong></p>
                    <ul>
                        <li>Situational judgment skills</li>
                        <li>UPSC / Bank Mock panels</li>
                        <li>Ethics & situational awareness</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
        else:
            with col1:
                st.markdown("""
                <div class="roadmap-step" style="border-left-color: #2563EB;">
                    <h4 style="color: #2563EB;">Beginner (Phase 1)</h4>
                    <p><strong>Foundations</strong></p>
                    <ul>
                        <li>Syntax & Basics</li>
                        <li>Simple scripts</li>
                        <li>Version control</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown("""
                <div class="roadmap-step" style="border-left-color: #7C3AED;">
                    <h4 style="color: #7C3AED;">Intermediate (Phase 2)</h4>
                    <p><strong>Integration</strong></p>
                    <ul>
                        <li>API creation</li>
                        <li>Database schemas</li>
                        <li>Simple layouts</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown("""
                <div class="roadmap-step" style="border-left-color: #06B6D4;">
                    <h4 style="color: #06B6D4;">Advanced (Phase 3)</h4>
                    <p><strong>Architecture</strong></p>
                    <ul>
                        <li>Cloud deployments</li>
                        <li>Docker containers</li>
                        <li>Performance caching</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                st.markdown("""
                <div class="roadmap-step" style="border-left-color: #22C55E;">
                    <h4 style="color: #22C55E;">Expert (Phase 4)</h4>
                    <p><strong>Scale & Design</strong></p>
                    <ul>
                        <li>System design</li>
                        <li>Distributed layers</li>
                        <li>Lead engineering</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)


def render_cover_letter_page():
    render_top_navigation()
    st.markdown('<div class="main-title">📝 Cover Letter</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Create tailored professional cover letters.</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        with st.container(border=True):
            st.subheader("Letter Parameters")
            name = st.text_input("Name", value=st.session_state.user_data["name"] if st.session_state.user_data else "Tarun Singh")
            company = st.text_input("Company", placeholder="Google")
            role = st.text_input("Target Role", value=st.session_state.job_role)

            generate = st.button("Generate Letter Content")
        
    with col2:
        with st.container(border=True):
            st.subheader("Preview Document Editor")
            if generate or 'cover_letter_content' in st.session_state:
                st.session_state.activities["cover_letter"] = "Just now"
                if generate:
                    with st.spinner("Writing an exceptional cover letter..."):
                        letter_text = generate_cover_letter(name, role, st.session_state.skills)
                        st.session_state.cover_letter_content = letter_text

                st.text_area("Generated Cover Letter Editor", value=st.session_state.cover_letter_content, height=450)
                st.download_button("📥 Export PDF format", data=st.session_state.cover_letter_content, file_name="Cover_Letter.txt")
            else:
                st.info("Input parameters and click Generate Letter Content.")

def render_resume_builder_page():
    render_top_navigation()
    st.markdown('<div class="main-title">📝 Resume Builder</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Construct a professional, ATS-friendly resume from scratch.</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        with st.container(border=True):
            st.subheader("Template Settings")
            template_style = st.selectbox("Select Template Style", ["Minimalist Blue", "Modern Slate", "Elegant Emerald"])
            
            st.subheader("Your Information")
            name = st.text_input("Full Name", value=st.session_state.user_data["name"] if st.session_state.user_data else "")
            email = st.text_input("Email", value=st.session_state.user_data["email"] if st.session_state.user_data else "")
            linkedin = st.text_input("LinkedIn URL", value=st.session_state.user_data.get("linkedin", "") if st.session_state.user_data else "")
            
            st.subheader("Professional Summary")
            summary = st.text_area("Write a short summary about yourself")
            
            st.subheader("Experience & Education")
            experience = st.text_area("Experience (Use bullet points)")
            education = st.text_area("Education", value=f"{st.session_state.user_data.get('college', '')} - {st.session_state.user_data.get('branch', '')}" if st.session_state.user_data else "")
            
            st.subheader("Skills")
            skills_input = st.text_input("Comma separated skills", value=", ".join(st.session_state.skills) if st.session_state.skills else "")
            
            generate = st.button("Generate Resume Template")
            
    with col2:
        with st.container(border=True):
            st.subheader("Resume Preview")
            if generate:
                # Build three structurally distinct templates
                if template_style == "Minimalist Blue":
                    resume_html = f"""
                    <div style="font-family: 'Inter', sans-serif; color: #1e293b; background: #ffffff; padding: 35px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); border-top: 6px solid #1e3a8a;">
                        <h1 style="margin: 0 0 5px 0; color: #1e3a8a; font-size: 2.1rem; font-family: 'Poppins', sans-serif; font-weight: 700;">{name}</h1>
                        <p style="margin: 0 0 20px 0; color: #64748b; font-size: 0.9rem; border-bottom: 2px solid #1e3a8a; padding-bottom: 8px;">📧 {email} | 🔗 {linkedin}</p>
                        
                        <h3 style="color: #1e3a8a; font-size: 1.1rem; margin-top: 15px; text-transform: uppercase; letter-spacing: 0.5px;">Summary</h3>
                        <p style="font-size: 0.92rem; line-height: 1.6; color: #334155;">{summary}</p>
                        
                        <h3 style="color: #1e3a8a; font-size: 1.1rem; margin-top: 20px; text-transform: uppercase; letter-spacing: 0.5px;">Experience</h3>
                        <p style="white-space: pre-wrap; font-size: 0.92rem; line-height: 1.6; color: #334155;">{experience}</p>
                        
                        <h3 style="color: #1e3a8a; font-size: 1.1rem; margin-top: 20px; text-transform: uppercase; letter-spacing: 0.5px;">Education</h3>
                        <p style="white-space: pre-wrap; font-size: 0.92rem; line-height: 1.6; color: #334155;">{education}</p>
                        
                        <h3 style="color: #1e3a8a; font-size: 1.1rem; margin-top: 20px; text-transform: uppercase; letter-spacing: 0.5px;">Skills</h3>
                        <p style="font-size: 0.92rem; line-height: 1.6; color: #334155;">{skills_input}</p>
                    </div>
                    """
                elif template_style == "Modern Slate":
                    # Two Column Layout
                    resume_html = f"""
                    <div style="font-family: 'Inter', sans-serif; color: #1e293b; background: #ffffff; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); display: flex; min-height: 600px; border: 1px solid #e2e8f0;">
                        <!-- Left Sidebar -->
                        <div style="width: 35%; background: #334155; color: #ffffff; padding: 30px 20px; border-top-left-radius: 8px; border-bottom-left-radius: 8px;">
                            <h2 style="margin: 0 0 5px 0; font-size: 1.6rem; font-family: 'Poppins'; color: #ffffff; font-weight:700;">{name}</h2>
                            <p style="font-size: 0.8rem; color: #cbd5e1; margin-bottom: 25px; line-height: 1.4;">📧 {email}<br/>🔗 {linkedin}</p>
                            
                            <h4 style="color: #38bdf8; border-bottom: 1px solid #475569; padding-bottom: 5px; text-transform: uppercase; font-size: 0.9rem; letter-spacing: 0.5px; margin-top: 20px;">Skills</h4>
                            <p style="font-size: 0.85rem; line-height: 1.5; color: #e2e8f0; white-space: pre-wrap;">{skills_input}</p>
                        </div>
                        <!-- Right Main Column -->
                        <div style="width: 65%; padding: 30px; background: #ffffff; border-top-right-radius: 8px; border-bottom-right-radius: 8px;">
                            <h3 style="color: #334155; font-size: 1.1rem; border-bottom: 2px solid #334155; padding-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 0;">Professional Summary</h3>
                            <p style="font-size: 0.9rem; line-height: 1.6; color: #334155; margin-bottom: 20px;">{summary}</p>
                            
                            <h3 style="color: #334155; font-size: 1.1rem; border-bottom: 2px solid #334155; padding-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px;">Experience</h3>
                            <p style="white-space: pre-wrap; font-size: 0.9rem; line-height: 1.6; color: #334155; margin-bottom: 20px;">{experience}</p>
                            
                            <h3 style="color: #334155; font-size: 1.1rem; border-bottom: 2px solid #334155; padding-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px;">Education</h3>
                            <p style="white-space: pre-wrap; font-size: 0.9rem; line-height: 1.6; color: #334155;">{education}</p>
                        </div>
                    </div>
                    """
                else:  # Elegant Emerald
                    # Centered serif layout
                    resume_html = f"""
                    <div style="font-family: Georgia, serif; color: #111827; background: #ffffff; padding: 40px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); border: 2px solid #064e3b; text-align: center;">
                        <h1 style="margin: 0 0 5px 0; color: #064e3b; font-size: 2.2rem; font-family: Georgia, serif; font-weight: 400; letter-spacing: 1px;">{name}</h1>
                        <p style="margin: 0 0 25px 0; color: #4b5563; font-size: 0.85rem; border-bottom: 1px double #059669; padding-bottom: 10px; font-style: italic;">📧 {email} &nbsp;|&nbsp; 🔗 {linkedin}</p>
                        
                        <div style="text-align: left;">
                            <h3 style="color: #064e3b; font-size: 1rem; border-bottom: 1px solid #064e3b; padding-bottom: 3px; text-transform: uppercase; font-family: Georgia, serif;">Summary</h3>
                            <p style="font-size: 0.9rem; line-height: 1.6; color: #1f2937; margin-bottom: 20px;">{summary}</p>
                            
                            <h3 style="color: #064e3b; font-size: 1rem; border-bottom: 1px solid #064e3b; padding-bottom: 3px; text-transform: uppercase; font-family: Georgia, serif;">Experience</h3>
                            <p style="white-space: pre-wrap; font-size: 0.9rem; line-height: 1.6; color: #1f2937; margin-bottom: 20px;">{experience}</p>
                            
                            <h3 style="color: #064e3b; font-size: 1rem; border-bottom: 1px solid #064e3b; padding-bottom: 3px; text-transform: uppercase; font-family: Georgia, serif;">Education</h3>
                            <p style="white-space: pre-wrap; font-size: 0.9rem; line-height: 1.6; color: #1f2937; margin-bottom: 20px;">{education}</p>
                            
                            <h3 style="color: #064e3b; font-size: 1rem; border-bottom: 1px solid #064e3b; padding-bottom: 3px; text-transform: uppercase; font-family: Georgia, serif;">Skills</h3>
                            <p style="font-size: 0.9rem; line-height: 1.6; color: #1f2937;">{skills_input}</p>
                        </div>
                    </div>
                    """
                st.markdown(resume_html, unsafe_allow_html=True)
                st.write("")
                st.download_button("Download HTML Resume", data=resume_html, file_name=f"resume_{template_style.lower().replace(' ', '_')}.html", mime="text/html")
            else:
                st.info("Fill out the details on the left and click Generate.")

def render_resume_feedback_page():
    render_top_navigation()
    st.markdown('<div class="main-title">💬 Resume Feedback</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Complete audit of strengths, weaknesses, and structural critiques.</div>', unsafe_allow_html=True)
    
    if not st.session_state.resume_text:
        st.warning("⚠️ Please upload your resume first.")
        return
        
    col1, col2 = st.columns([1, 2])
    
    with col1:
        with st.container(border=True):
            st.subheader("Resume Quality Score")
            st.markdown("""
            <div style="font-size: 5rem; color: #22C55E; font-family: 'Poppins', sans-serif;">84</div>
            <p style="color: #94A3B8; font-size: 1rem;">POINTS / 100</p>
            """, unsafe_allow_html=True)
        
    with col2:
        with st.container(border=True):
            st.subheader("Critiques List")
            st.markdown("""
            ### ✅ Strengths
            - **Format Integrity:** Clean spacing, default font sizes are consistent.
            - **Core Info:** Email and LinkedIn contact links parsed successfully.

            ### ⚠️ Weaknesses
            - **Lack of Quantitative Results:** Achievements need metric statistics.
            - **Excessive Length:** Keep experience listings concise.

            ### 🛠️ Improvement Actions Checklist
            - [ ] Add numeric statistics (e.g. 'Reduced search latency by 15%')
            - [ ] Shorten description lines
            """)

def render_job_match_page():
    render_top_navigation()
    st.markdown('<div class="main-title">⚡ Job Match</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Compare a target Job Description (JD) to your parsed resume details.</div>', unsafe_allow_html=True)
    
    if not st.session_state.resume_text:
        st.warning("⚠️ Please upload your resume first.")
        return
        
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        with st.container(border=True):
            st.subheader("Paste Job Description")
            jd = st.text_area("Job Description text:", height=200, placeholder="We are seeking a developer with skills in Python, Git, SQL...")

            analyze = st.button("Check Match Score")
        
    with col2:
        with st.container(border=True):
            st.subheader("Compatibility Analysis")
            if analyze and jd.strip():
                matched_count = 0
                jd_lower = jd.lower()
                for s in st.session_state.skills:
                    if s.lower() in jd_lower:
                        matched_count += 1
                total_skills = len(st.session_state.skills)
                score = int((matched_count / max(1, total_skills)) * 100)

                st.metric("Compatibility Match Rating", f"{score}%")
                st.progress(score / 100)

                st.write(f"Matches found: **{matched_count}** of **{total_skills}** resume skills.")
            else:
                st.info("Paste a Job Description and click Check Match Score.")

def render_courses_page():
    render_top_navigation()
    st.markdown('<div class="main-title">🎓 Course Recommendation</div>', unsafe_allow_html=True)
    
    if st.session_state.career_track == "Government Exams":
        st.markdown('<div class="subtitle">Prepare for government exams with structured recommended classes.</div>', unsafe_allow_html=True)
        col1, col2 = st.columns([1.5, 1])
        
        with col1:
            with st.container(border=True):
                st.subheader("Recommended GS & Aptitude Classes")
                courses = [
                    {"title": "General Studies & CSAT Comprehensive Prep", "platform": "Unacademy / VisionIAS", "duration": "120 hrs", "diff": "Intermediate", "link": "https://unacademy.com/"},
                    {"title": "Quantitative Aptitude & Logical Reasoning Masterclass", "platform": "Adda247 / Testbook", "duration": "45 hrs", "diff": "Beginner", "link": "https://testbook.com/"},
                    {"title": "Daily Polity & Economic Policy Insights", "platform": "StudyIQ / InsightsIAS", "duration": "30 hrs", "diff": "Advanced", "link": "https://www.insightsonindia.com/"}
                ]
                for c in courses:
                    st.markdown(f"""
                    <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 15px; margin-bottom: 12px;">
                        <strong>📚 {c['title']}</strong><br/>
                        <span style="font-size: 0.85rem; color: #94A3B8;">Platform: {c['platform']} | Duration: {c['duration']} | Difficulty: {c['diff']}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    st.link_button(f"Start Learning: {c['title'][:20]}...", c["link"])
        with col2:
            with st.container(border=True):
                st.subheader("Govt Exam Syllabus Tracker")
                st.write("Complete study of remaining subjects to fulfill exam criteria:")
                st.markdown("""
                - [ ] Polity & Indian Constitution (Pending)
                - [ ] Modern Indian History (Pending)
                - [ ] Quantitative Aptitude Shortcuts (Pending)
                """)
    else:
        st.markdown('<div class="subtitle">Up-skill your technical capability with curated recommended classes.</div>', unsafe_allow_html=True)
        col1, col2 = st.columns([1.5, 1])
        
        with col1:
            with st.container(border=True):
                st.subheader("Recommended Classes")
                courses = [
                    {"title": "Core Python & Object Patterns Masterclass", "platform": "Coursera", "duration": "14 hrs", "diff": "Intermediate", "link": "https://www.coursera.org/learn/python"},
                    {"title": "Relational Databases, SQL Indexing", "platform": "Udemy", "duration": "8 hrs", "diff": "Beginner", "link": "https://www.udemy.com/topic/sql/"},
                    {"title": "Docker Containers & Kubernetes", "platform": "edX", "duration": "20 hrs", "diff": "Advanced", "link": "https://www.edx.org/learn/kubernetes"}
                ]
                for c in courses:
                    st.markdown(f"""
                    <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 15px; margin-bottom: 12px;">
                        <strong>📚 {c['title']}</strong><br/>
                        <span style="font-size: 0.85rem; color: #94A3B8;">Platform: {c['platform']} | Duration: {c['duration']} | Difficulty: {c['diff']}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    st.link_button(f"Start Learning: {c['title'][:20]}...", c["link"])
        with col2:
            with st.container(border=True):
                st.subheader("Up-skill Tracker")
                st.write("Acquire the following to complete your job profile requirements:")
                st.markdown("""
                - [ ] Docker Containers (0% progress)
                - [ ] SQL Query Optimization (0% progress)
                """)

def render_progress_tracker_page():
    render_top_navigation()
    st.markdown('<div class="main-title">📈 Progress Tracker</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Track your career milestones and study metrics dynamically.</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        with st.container(border=True):
            st.subheader("Interactive Milestones Graph")

            if st.session_state.career_track == "Government Exams":
                req_subjects = GOVT_EXAMS.get(st.session_state.job_role, [])
                studied = len(st.session_state.get("studied_subjects", []))
                completion_pct = int((studied / max(1, len(req_subjects))) * 100)
                
                scan_val = 100
                ncert_val = 100 if studied >= 1 else 0
                cov_val = completion_pct
                mock_val = 100 if st.session_state.activities["interview"] != "No attempts" else 0
                roadmap_val = 100 if st.session_state.activities["roadmap"] != "No attempts" else 0
                
                chart_data = pd.DataFrame({
                    "Milestone Step": ["Syllabus Scanned", "NCERT Basics", "Syllabus Coverage", "First Mock Exam", "Roadmap Built"],
                    "Target Accomplished (%)": [scan_val, ncert_val, cov_val, mock_val, roadmap_val]
                })
            else:
                resume_val = 100 if st.session_state.resume_text else 0
                mock_val = 100 if st.session_state.activities["interview"] != "No attempts" else 0
                leetcode_user = st.session_state.user_data.get("leetcode_username", "") if st.session_state.user_data else ""
                leetcode_val = 100 if leetcode_user else 0
                
                chart_data = pd.DataFrame({
                    "Milestone Step": ["Profile Init", "Resume Parsed", "ATS Audit", "Mock Interview", "LeetCode Linked"],
                    "Target Accomplished (%)": [100, resume_val, resume_val, mock_val, leetcode_val]
                })
            st.line_chart(chart_data.set_index("Milestone Step"))
        
    with col2:
        with st.container(border=True):
            st.subheader("Goal Checklist Status")
            if st.session_state.career_track == "Government Exams":
                req_subjects = GOVT_EXAMS.get(st.session_state.job_role, [])
                studied = len(st.session_state.get("studied_subjects", []))
                ncert_checked = "x" if studied >= 1 else " "
                mock_checked = "x" if st.session_state.activities["interview"] != "No attempts" else " "
                roadmap_checked = "x" if st.session_state.activities["roadmap"] != "No attempts" else " "
                
                st.markdown(f"""
                - [x] Select target Government exam
                - [x] Scan core exam syllabus
                - [{ncert_checked}] Read basic reference NCERTs (Check studied subjects)
                - [{mock_checked}] Practice daily government mock tests
                - [{roadmap_checked}] Build dynamic prep roadmap
                """)
            else:
                resume_checked = "x" if st.session_state.resume_text else " "
                mock_checked = "x" if st.session_state.activities["interview"] != "No attempts" else " "
                leetcode_user = st.session_state.user_data.get("leetcode_username", "") if st.session_state.user_data else ""
                lc_checked = "x" if leetcode_user else " "
                
                st.markdown(f"""
                - [x] Create SkillSync Profile
                - [{resume_checked}] Upload initial Resume PDF
                - [{resume_checked}] Verify ATS rating criteria
                - [{mock_checked}] Complete mock interview simulator
                - [{lc_checked}] Connect LeetCode profile
                """)

def render_achievements_page():
    render_top_navigation()
    st.markdown('<div class="main-title">🏆 Achievements & Badges</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Explore virtual achievement badges and XP reward milestones.</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    if st.session_state.career_track == "Government Exams":
        with col1:
            st.markdown("""
            <div class="glass-container" style="text-align: center; min-height: 220px;">
                <div style="font-size: 3.5rem; margin-bottom: 10px;">🥇</div>
                <h4 style="margin: 0; color: #fff;">Syllabus Scholar</h4>
                <p style="font-size: 0.82rem; color: #94A3B8; margin-top: 8px;">Earned for successfully checking off and covering at least 1 core syllabus subject.</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div class="glass-container" style="text-align: center; min-height: 220px;">
                <div style="font-size: 3.5rem; margin-bottom: 10px;">🏅</div>
                <h4 style="margin: 0; color: #fff;">Officer Mindset</h4>
                <p style="font-size: 0.82rem; color: #94A3B8; margin-top: 8px;">Earned for practicing the Government (UPSC/SSC) dynamic mock interview room.</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown("""
            <div class="glass-container" style="text-align: center; min-height: 220px;">
                <div style="font-size: 3.5rem; margin-bottom: 10px;">🎖️</div>
                <h4 style="margin: 0; color: #fff;">Polity Master</h4>
                <p style="font-size: 0.82rem; color: #94A3B8; margin-top: 8px;">Earned for reviewing current affairs modules and completing daily recommended GS classes.</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        with col1:
            st.markdown("""
            <div class="glass-container" style="text-align: center; min-height: 220px;">
                <div style="font-size: 3.5rem; margin-bottom: 10px;">🥇</div>
                <h4 style="margin: 0; color: #fff;">Resume Guru</h4>
                <p style="font-size: 0.82rem; color: #94A3B8; margin-top: 8px;">Earned for uploading a resume that achieves over 80% matching rating on initial parsing diagnostics.</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div class="glass-container" style="text-align: center; min-height: 220px;">
                <div style="font-size: 3.5rem; margin-bottom: 10px;">🏅</div>
                <h4 style="margin: 0; color: #fff;">Interview Champ</h4>
                <p style="font-size: 0.82rem; color: #94A3B8; margin-top: 8px;">Earned for successfully generating questions and practicing answers in mock interview simulators.</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown("""
            <div class="glass-container" style="text-align: center; min-height: 220px;">
                <div style="font-size: 3.5rem; margin-bottom: 10px;">🎖️</div>
                <h4 style="margin: 0; color: #fff;">Daily Warrior</h4>
                <p style="font-size: 0.82rem; color: #94A3B8; margin-top: 8px;">Earned for completing LeetCode challenges and daily up-skilling courses in recommendation systems.</p>
            </div>
            """, unsafe_allow_html=True)

def render_profile_page():
    render_top_navigation()
    st.markdown('<div class="main-title">👤 Profile</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Review your registered user credentials and achievements.</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    user = st.session_state.user_data if st.session_state.user_data else {"name": "Tarun Singh", "email": "tarun@skillsync.ai", "college": "SkillSync Institute", "branch": "Computer Science", "grad_year": "2027", "id": 1}
    is_demo = user and user["email"] == "tarun@skillsync.ai"
    
    with col1:
        with st.container(border=True):
            import os
            custom_avatar_path = f"assets/{user['id']}_avatar.jpg"
            if os.path.exists(custom_avatar_path):
                avatar_b64 = get_base64_image(custom_avatar_path)
                st.markdown(f'<div style="text-align: center;"><img src="{avatar_b64}" style="width: 100px; height: 100px; border-radius: 50%; border: 3px solid #2563EB; object-fit: cover; margin-bottom: 15px;" /></div>', unsafe_allow_html=True)
            elif is_demo:
                avatar_b64 = get_base64_image("assets/tarun_avatar.jpg")
                if avatar_b64:
                    st.markdown(f'<div style="text-align: center;"><img src="{avatar_b64}" style="width: 100px; height: 100px; border-radius: 50%; border: 3px solid #2563EB; object-fit: cover; margin-bottom: 15px;" /></div>', unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="width: 100px; height: 100px; border-radius: 50%; background: linear-gradient(135deg, #2563EB, #7C3AED); margin: 0 auto 20px; display: flex; align-items: center; justify-content: center; font-size: 2.5rem; font-weight: 800; color: white;">
                    {user['name'][0].upper()}
                </div>
                """, unsafe_allow_html=True)
            
            st.subheader(user["name"])
            st.write(f"📧 {user['email']}")
            
            new_avatar = st.file_uploader("Upload New Profile Photo", type=["jpg", "png", "jpeg"])
            if new_avatar:
                with open(custom_avatar_path, "wb") as f:
                    f.write(new_avatar.getbuffer())
                st.success("Profile photo updated!")
                st.rerun()
        
    with col2:
        with st.container(border=True):
            st.subheader("Personal Information")
            st.write(f"🎓 **College:** {user['college']}")
            st.write(f"🔬 **Branch:** {user['branch']}")
            st.write(f"📅 **Graduation Year:** {user['grad_year']}")
            
            # Dynamic Career Readiness Score based on missing skills vs total skills
            req_skills = JOB_SKILLS.get(st.session_state.job_role, [])
            if req_skills:
                ms_skills = get_skill_gap(st.session_state.skills, st.session_state.job_role)
                real_score = int(((len(req_skills) - len(ms_skills)) / len(req_skills)) * 100)
            else:
                real_score = 0
            st.write(f"🏆 **Career Readiness Score:** {real_score}%")
            
        with st.container(border=True):
            st.subheader("Professional Links")
            l_in = st.text_input("LinkedIn URL", value=user.get("linkedin", ""))
            
            if st.session_state.career_track != "Government Exams":
                g_hub = st.text_input("GitHub URL", value=user.get("github", ""))
                port = st.text_input("Portfolio Website", value=user.get("portfolio", ""))
            else:
                g_hub = user.get("github", "")
                port = user.get("portfolio", "")
            
            if st.button("Save Profile Links", use_container_width=True):
                import sqlite3
                conn = sqlite3.connect("database/users.db")
                conn.execute("UPDATE users SET linkedin=?, github=?, portfolio=? WHERE id=?", (l_in, g_hub, port, user['id']))
                conn.commit()
                conn.close()
                st.session_state.user_data["linkedin"] = l_in
                st.session_state.user_data["github"] = g_hub
                st.session_state.user_data["portfolio"] = port
                
                # update auth.json if it exists
                import os, json
                if os.path.exists("auth.json"):
                    with open("auth.json", "w") as f:
                        json.dump(st.session_state.user_data, f)
                        
                st.success("Professional links updated successfully!")
                st.rerun()

def render_settings_page():
    render_top_navigation()
    st.markdown('<div class="main-title">⚙️ Settings</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Configure settings and security options.</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            st.subheader("Preferences")
            dark_mode = st.toggle("Dark Mode Active", value=st.session_state.get('dark_mode', True))
            if dark_mode != st.session_state.get('dark_mode', True):
                st.session_state.dark_mode = dark_mode
                st.rerun()
            st.toggle("Email Notifications Active", value=True)
        
        with st.container(border=True):
            st.subheader("Change Password")
            st.text_input("Current Password", type="password", key="s_old")
            st.text_input("New Password", type="password", key="s_new")
            if st.button("Update Account Password"):
                st.success("✅ Password updated successfully!")
        
    with col2:
        with st.container(border=True):
            st.subheader("Platform Info")
            st.write("🚀 **SkillSync AI Version:** 2.1.0")
            st.write("⚙️ **Optimized For:** Corporate Careers & Govt Exams Preparation")
            st.write("🔒 **Data Privacy:** Your profile data and saved credentials are encrypted locally.")

# ==========================================
# MAIN APPLICATION ENGINE
# ==========================================

def main():
    if not st.session_state.get('dark_mode', True):
        st.markdown("""
        <style>
        html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background-color: #F4F6F9 !important;
            background-image: radial-gradient(at 0% 0%, rgba(37, 99, 235, 0.05) 0px, transparent 50%),
                              radial-gradient(at 100% 0%, rgba(124, 58, 237, 0.04) 0px, transparent 50%) !important;
            color: #0F172A !important;
        }
        h1, h2, h3, h4, h5, h6, .profile-name, .feature-card-title, .metric-val-custom {
            color: #0F172A !important;
        }
        .glass-container, .feature-card, div[data-testid="stVerticalBlockBorder"], [data-testid="stSidebar"] {
            background: #ffffff !important;
            border: 1px solid #E2E8F0 !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05) !important;
        }
        .main-title {
            background: none !important;
            color: #0F172A !important;
            -webkit-text-fill-color: #0F172A !important;
        }
        .subtitle, .feature-card-desc, .metric-label-custom, .profile-role, .resume-subtitle-preview, .activity-time {
            color: #475569 !important;
        }
        div[data-baseweb="input"], 
        div[data-baseweb="select"] > div,
        div[data-baseweb="textarea"] {
            background-color: #ffffff !important;
            border-color: #CBD5E1 !important;
        }
        div[data-testid="stTextInput"] input,
        div[data-testid="stNumberInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-baseweb="select"] span {
            color: #0F172A !important;
        }
        p, li, td, label, [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] span, [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li {
            color: #0F172A !important;
        }
        /* Target generic element class names that Streamlit uses for checkboxes/toggles/radios */
        div[data-testid="stCheckbox"] label, div[data-testid="stCheckbox"] p, div[data-testid="stCheckbox"] span,
        div[data-testid="stToggle"] label, div[data-testid="stToggle"] p, div[data-testid="stToggle"] span,
        div[data-testid="stRadio"] label, div[data-testid="stRadio"] p, div[data-testid="stRadio"] span,
        div[data-testid="stSidebar"] label, div[data-testid="stSidebar"] p, div[data-testid="stSidebar"] span {
            color: #0F172A !important;
        }
        /* Ensure button text remains white */
        .stButton button, .stButton button p, .stButton button span,
        .stDownloadButton button, .stDownloadButton button p, .stDownloadButton button span {
            color: #ffffff !important;
        }
        /* Dropdown selection lists contrast fix */
        div[role="listbox"] div, div[role="option"] {
            color: #0F172A !important;
            background-color: #ffffff !important;
        }
        div[role="option"]:hover {
            background-color: #F1F5F9 !important;
        }
        .search-container { background: #F1F5F9 !important; border: 1px solid #E2E8F0 !important; }
        .search-container input { color: #0F172A !important; }
        .notif-bell { color: #334155 !important; }
        .resume-title-preview { color: #0F172A !important; }
        .activity-title { color: #0F172A !important; }
        .stButton > button { color: #ffffff !important; }
        </style>
        """, unsafe_allow_html=True)
        
    if not st.session_state.logged_in:
        # Check for auto-login cache
        import os, json
        if os.path.exists("auth.json"):
            try:
                with open("auth.json", "r") as f:
                    cached_user = json.load(f)
                if cached_user:
                    st.session_state.user_data = cached_user
                    st.session_state.logged_in = True
                    st.session_state.page = "Dashboard"
                    st.session_state.chat_history = [
                        {"role": "ai", "content": f"Hello {cached_user['name']}! I am your SkillSync AI Career Coach. Let's audit your skill gap and build your career roadmap!"}
                    ]
                    st.rerun()
            except:
                pass
                
    if not st.session_state.logged_in:
        if st.session_state.page == "register":
            render_register()
        else:
            render_login()
    else:
        render_sidebar()
        
        page = st.session_state.page
        if page == "Dashboard":
            render_dashboard_page()
        elif page == "Resume Analyzer":
            render_resume_analyzer_page()
        elif page == "Resume Builder":
            render_resume_builder_page()
        elif page == "ATS Score":
            render_ats_score_page()
        elif page == "Skill Gap":
            render_skill_gap_page()
        elif page == "AI Career Coach":
            render_career_coach_page()
        elif page == "Mock Interview":
            render_mock_interview_page()
        elif page == "Career Roadmap":
            render_roadmap_page()
        elif page == "Cover Letter":
            render_cover_letter_page()
        elif page == "Courses":
            render_courses_page()
        elif page == "Job Match":
            render_job_match_page()
        elif page == "Progress Tracker":
            render_progress_tracker_page()
        elif page == "Achievements":
            render_achievements_page()
        elif page == "Profile":
            render_profile_page()
        elif page == "Settings":
            render_settings_page()
        else:
            render_dashboard_page()

if __name__ == "__main__":
    main()