import streamlit as st
import PyPDF2
import json
import time
import requests
import re

# تنبيه: يفضل وضع المفتاح في secrets.toml
GROQ_API_KEY = "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"

def generate_with_groq(text_input, mode):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    safe_text = text_input[:7000].replace('"', "'")
    
    # تحديد التعليمات بناءً على الخيار المختار
    if mode == "Solved Q&A Bank":
        instruction = "This text is a solved Q&A bank. Extract the questions and their correct answers. Return ONLY a JSON array."
    elif mode == "Unsolved Q&A Bank":
        instruction = "This text is a question bank WITHOUT answers. Solve it yourself and provide the correct answers. Return ONLY a JSON array."
    else: 
        instruction = "Act as an expert professor. Generate the MAXIMUM possible number of MCQs ""covering every single detail and concept in this lecture. ""Everything MUST be in English language only."

    prompt = (
        f"{instruction} "
        "Format: [{\"question\": \"...\", \"options\": [\"Option 1\", \"Option 2\"], \"answer\": \"Option 1\"}]. "
        f"Text: {safe_text}"
    )
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    }
    
    try:
        # تصحيح رابط الـ API للرابط الرسمي لـ Groq
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=30)
        content = response.json()['choices'][0]['message']['content'].strip()
        match = re.search(r'\[.*\]', content, re.DOTALL)
        return json.loads(match.group(0)) if match else []
    except: 
        return []

st.set_page_config(page_title="AREF AGENT | AI VISION", layout="centered")

# --- استايل CSS (نفس اللي بعته بدون تغيير) ---
st.markdown("""
    <style>
    .stApp { background-image: url("https://i.pinimg.com/1200x/98/e6/3a/98e63a54b4d187919663cfaec2a844c0.jpg"); background-size: cover; background-attachment: fixed; }
    .stApp > div:first-child { background-color: rgba(0, 0, 0, 0.9); min-height: 100vh; }
    @keyframes shake { 0%, 100% { transform: translateX(0); } 25% { transform: translateX(-7px); } 75% { transform: translateX(7px); } }
    .error-box { animation: shake 0.2s; border: 3px solid #ff4b4b !important; box-shadow: 0 0 30px #ff4b4b !important; }
    @keyframes glow { 0%, 100% { box-shadow: 0 0 10px #00ffcc; } 50% { box-shadow: 0 0 30px #00ffcc; } }
    .success-box { animation: glow 1s infinite; border: 3px solid #00ffcc !important; }
    @keyframes pulse-red { 0%, 100% { color: #ff4b4b; text-shadow: 0 0 5px #ff4b4b; } 50% { color: #fff; text-shadow: 0 0 20px #ff4b4b; } }
    .timer-critical { animation: pulse-red 0.5s infinite; font-weight: bold; }
    .neon-title { color: #00d4ff; text-shadow: 0 0 20px #00d4ff; text-align: center; font-size: 4rem; font-weight: 900; }
    .question-card { background: rgba(15, 15, 15, 0.95); padding: 30px; border-radius: 20px; border: 1px solid #444; }
    .status-container { display: flex; justify-content: space-around; align-items: center; background: rgba(0, 212, 255, 0.07); padding: 20px; border-radius: 20px; border: 1px solid rgba(0, 212, 255, 0.3); margin-bottom: 25px; backdrop-filter: blur(10px); }
    .stat-item { text-align: center; }
    .stat-label { font-size: 0.7rem; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
    .stat-value { font-size: 1.4rem; font-weight: bold; color: #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

if 'questions' not in st.session_state:
    st.session_state.update({
        'questions': [], 'current_idx': 0, 'score': 0, 
        'is_finished': False, 'answered': False, 'status': 'normal',
        'correct_text_to_show': "", 'start_time': None
    })

st.markdown('<h1 class="neon-title">AREF AGENT</h1>', unsafe_allow_html=True)

# --- الواجهة الأمامية مع الخيارات الثلاثة ---
if not st.session_state.questions and not st.session_state.is_finished:
    # إضافة الخيارات الثلاثة هنا
    data_mode = st.radio(
        "SELECT DATA TYPE:",
        ["Solved Q&A Bank", "Unsolved Q&A Bank", "Lecture"],
        index=2
    )
    
    file = st.file_uploader("UPLOAD SYSTEM DATA (PDF)", type="pdf")
    
    if file and st.button("ACTIVATE NEURAL LINK"):
        with st.spinner("🧬 ANALYZING DATA..."):
            reader = PyPDF2.PdfReader(file)
            full_text = "".join([p.extract_text() for p in reader.pages])
            # نمرر نوع الخيار للدالة
            data = generate_with_groq(full_text, data_mode)
            if data:
                st.session_state.questions = data
                st.session_state.start_time = time.time()
                st.rerun()

# --- بقية الكود (الأسئلة والنتيجة) كما هو تماماً دون تغيير ---
elif st.session_state.questions and not st.session_state.is_finished:
    idx = st.session_state.current_idx
    total = len(st.session_state.questions)
    remaining_nodes = total - (idx + 1)
    q = st.session_state.questions[idx]
    
    elapsed = time.time() - st.session_state.start_time
    remaining_time = max(0, 45 - int(elapsed))

    t_class = "stat-value"
    if remaining_time <= 10: t_class += " timer-critical"

    if remaining_time == 0 and not st.session_state.answered:
        st.session_state.answered = True
        st.session_state.status = 'wrong'
        st.session_state.correct_text_to_show = q['answer']
        st.rerun()

    st.markdown(f"""
    <div class="status-container">
        <div class="stat-item"><div class="stat-label">Total Nodes</div><div class="stat-value">{total}</div></div>
        <div class="stat-item"><div class="stat-label">Remaining</div><div class="stat-value" style="color:#ffcc00;">{remaining_nodes}</div></div>
        <div class="stat-item"><div class="stat-label">Timer</div><div class="{t_class}">{remaining_time}s</div></div>
        <div class="stat-item"><div class="stat-label">Score</div><div class="stat-value" style="color:#00ffcc;">{st.session_state.score}</div></div>
    </div>
    """, unsafe_allow_html=True)

    b_style = "question-card"
    if st.session_state.status == 'correct': b_style += " success-box"
    elif st.session_state.status == 'wrong': b_style += " error-box"

    st.markdown(f"<div class='{b_style}'><h3>NODE {idx+1}</h3><p style='font-size:1.4rem;'>{q['question']}</p></div>", unsafe_allow_html=True)
    
    choice = st.radio("SELECT RESPONSE:", q['options'], key=f"q_{idx}", disabled=st.session_state.answered)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("VERIFY DATA", use_container_width=True, disabled=st.session_state.answered):
            st.session_state.answered = True
            if choice == q['answer']:
                st.session_state.score += 1
                st.session_state.status = 'correct'
                st.balloons()
            else:
                st.session_state.status = 'wrong'
                st.session_state.correct_text_to_show = q['answer']
            st.rerun()
    
    with c2:
        if st.session_state.answered:
            if st.session_state.status == 'wrong':
                st.error(f"CORRECT RESPONSE: {st.session_state.correct_text_to_show}")
            else:
                st.success("SUCCESS ✅")

            if st.button("NEXT NODE ➡️", use_container_width=True):
                if idx + 1 < total:
                    st.session_state.update({
                        'current_idx': idx + 1,
                        'answered': False,
                        'status': 'normal',
                        'correct_text_to_show': "",
                        'start_time': time.time()
                    })
                    st.rerun()
                else:
                    st.session_state.is_finished = True
                    st.rerun()

    if not st.session_state.answered and remaining_time > 0:
        time.sleep(1)
        st.rerun()

else:
    score = st.session_state.score
    total_questions = len(st.session_state.questions)
    st.markdown(f"""
        <div class='question-card' style='text-align:center;'>
            <h1>MISSION COMPLETE</h1>
            <p style='font-size:2rem;'>FINAL SCORE: {score}/{total_questions}</p>
        </div>
    """, unsafe_allow_html=True)
    
    if score == total_questions:
        st.snow()
        st.success("GOD MODE: ACTIVATED 😂 🦾 تمت البصمجه بنجاح !")
    else:
        st.warning("AGENT RANK: F (SYSTEM FAILURE) - 😂 ارجع بصمج تاني ")
        
    if st.button("REBOOT SYSTEM", use_container_width=True):
        st.session_state.clear()
        st.rerun()
