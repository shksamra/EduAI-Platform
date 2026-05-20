from transformers import TextIteratorStreamer
from threading import Thread
import random
import streamlit as st
import json
import random
import re
import styles, database, ai_engine
import pandas as pd
import torch
from datetime import datetime 
from pydantic import BaseModel, Field, field_validator
from typing import List

# 1. SETUP & THEME
st.set_page_config(page_title="🎓 EduAI ", layout="wide", page_icon="🎓")
styles.apply_styles() # Inject CSS from styles.py

# --- 1. INITIALIZE GLOBAL SESSION STATE ---
# This ensures these variables exist before the UI tries to read them
if 'submitted_quiz' not in st.session_state:
    st.session_state.submitted_quiz = False

if 'active_quiz_data' not in st.session_state:
    st.session_state.active_quiz_data = None

if 'pdf_topics' not in st.session_state:
    st.session_state.pdf_topics = None

# --- 2. AUTHENTICATION ROUTER ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'role' not in st.session_state: st.session_state.role = None

if not st.session_state.auth:
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    st.markdown('<div class="header-text">EduAI Access Portal</div>', unsafe_allow_html=True)
    
    # THREE DISTINCT TABS
    t1, t2, t3 = st.tabs(["🎓 Student Login", "🔒 Admin Login", "📝 Register"])
    
    with t1: # STUDENT LOGIN
        u = st.text_input("Username", key="st_u")
        p = st.text_input("Password", type="password", key="st_p")
        if st.button("🔑 Sign In as Student"):
            role = database.verify_user(u, p)
            if role == "student":
                st.session_state.auth, st.session_state.user, st.session_state.role = True, u, "student"
                st.rerun()
            elif role == "admin":
                st.warning("Admin detected. Please use the Admin Login tab.")
            else: st.error("Invalid student credentials.")

    with t2: # ADMIN LOGIN
        u = st.text_input("Admin Username", key="ad_u")
        p = st.text_input("Admin Password", type="password", key="ad_p")
        if st.button("🗝️ Sign In as Admin"):
            role = database.verify_user(u, p)
            if role == "admin":
                st.session_state.auth, st.session_state.user, st.session_state.role = True, u, "admin"
                st.rerun()
            else: st.error("Access Denied: Admin credentials required.")

    with t3: # REGISTER
        nu = st.text_input("New Username", key="reg_u")
        np = st.text_input("New Password", type="password", key="reg_p")
        if st.button("📝 Create Student Account"):
            # Every self-registered user is a 'student'
            if database.register_user(nu, np): 
                st.success("Account created! Please switch to the Student Login tab.")

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

def admin_dashboard_view():
    st.markdown('<div class="header-text">🏛️ Institutional Control Center</div>', unsafe_allow_html=True)
    
    # --- FETCH DATA ---
    df_users, df_vault, df_scores = database.get_detailed_admin_data()
    
    # --- 1. KPI METRICS (The "Numbers" Row) ---
    col1, col2, col3, col4 = st.columns(4)
    
    total_students = len(df_users[df_users['role'] == 'student'])
    col1.metric("Total Students", total_students, delta="Active")
    
    total_content = len(df_vault)
    col2.metric("Summaries Generated", total_content)
    
    if not df_scores.empty:
        avg_score = (df_scores['score'].sum() / df_scores['total'].sum()) * 100
        col3.metric("Avg. Global Accuracy", f"{int(avg_score)}%")
    else:
        col3.metric("Avg. Global Accuracy", "0%")
        
    col4.metric("System Status", "Healthy", delta_color="normal")

    st.divider()

    # --- 2. ANALYTICS SECTION ---
    t1, t2, t3 = st.tabs(["📈 Usage Trends", "🎓 Student Performance", "👤 User Management"])

    with t1:
        st.subheader("Platform Adoption Analytics")
        c1, c2 = st.columns([2, 1])
        with c1:
            st.write("**Content Source Distribution** (PDF vs Web)")
            if not df_vault.empty:
                source_counts = df_vault['type'].value_counts()
                st.bar_chart(source_counts, color="#2563eb")
            else: st.info("No data yet.")
        with c2:
            st.write("**Activity Summary**")
            st.write(f"- Total PDFs Processed: {len(df_vault[df_vault['type']=='PDF'])}")
            st.write(f"- Total Web Articles: {len(df_vault[df_vault['type']=='WEB'])}")

    with t2:
        st.subheader("Global Gradebook & Mastery")
        if not df_scores.empty:
            # Table of performance
            st.dataframe(df_scores, use_container_width=True, hide_index=True)
            # Performance Chart
            st.write("**Average Score per Student**")
            performance = df_scores.groupby('username')['score'].mean()
            st.line_chart(performance, color="#10b981")
        else:
            st.info("No quiz scores recorded across the institution yet.")

    with t3:
        st.subheader("Registered Users")
        # List of users and their roles
        st.table(df_users)
        
    # --- LOGOUT ---
    st.sidebar.divider()
    if st.sidebar.button("🚪 LOGOUT ADMIN", use_container_width=True):
        st.session_state.auth = False
        st.session_state.role = None
        st.rerun()
    

# 3. INITIALIZE MODELS (Happens once after login)
with st.spinner("🚀 Booting High-Speed AI..."):
    # This must match the name in ai_engine.py exactly
    embed_model, q_tok, q_mod, s_tok, s_mod = ai_engine.load_all_engines()

@st.fragment
def discovery_feed_fragment():
    st.markdown("<h4 style='font-family: Poppins; color: #1e293b; margin-bottom: 10px;'>📈 Discovery Feed</h4>", unsafe_allow_html=True)
    st.caption("Latest handpicked resources")
    
    # Try/Except block to catch errors in the data function
    try:
        blogs = ai_engine.get_trending_blogs()
        if not blogs:
            st.info("No blogs found.")
        
        for blog in blogs:
            st.markdown(f"""
                <a href="{blog['url']}" target="_blank" style="text-decoration: none;">
                    <div class="sidebar-card">
                        <span class="card-tag">{blog['tag']}</span>
                        <div class="card-title" style="margin-top: 5px;">{blog['title']}</div>
                        <div class="card-footer" style="margin-top: 8px;">EXPLORE <span>→</span></div>
                    </div>
                </a>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error("Feed error.")



# --- PDF SUMMARIZER FRAGMENT ---
@st.fragment
def pdf_summarizer_fragment():
    st.subheader("📄 PDF Study Hub")
    
    # 1. Reset Logic
    if st.button("🗑️ Clear PDF", key="clear_pdf"):
        st.session_state.pdf_result = None
        st.rerun()

    u_pdf = st.file_uploader("Upload PDF", type="pdf", key="pdf_f_up")
    
    if u_pdf:
        # Load sections if not already loaded
        if "last_uploaded_pdf" not in st.session_state or st.session_state.last_uploaded_pdf != u_pdf.name:
            st.session_state.pdf_result = None
            st.session_state.last_uploaded_pdf = u_pdf.name
            st.session_state.sections = ai_engine.extract_pdf_index(u_pdf)
        
        # Filter out Introduction if desired
        topic_options = [k for k in st.session_state.sections.keys() if k != "Introduction"]
        sel_topic = st.selectbox("Select Topic:", topic_options, key="pdf_f_topic")
        lvl = st.selectbox("Learning Level:", ["Beginner", "Intermediate", "Advanced"], key="pdf_f_lvl")
        
        # --- THE SINGLE SLOT FOR THE BOX ---
        box_slot = st.empty()

        if st.button("⚡ QUICK SUMMARIZE", key="pdf_f_btn"):
            # 1. Identify the text to summarize
            pdf_source_text = st.session_state.sections.get(sel_topic, "")
            
            if pdf_source_text:
                st.session_state.pdf_result = None # Clear old result
                
                with st.status("AI is analyzing PDF...", expanded=True) as status:
                    full_response = ""
                    
                    # 2. CALL THE CORRECT FUNCTION: stream_fast_abstractive_summary
                    for chunk in ai_engine.stream_fast_abstractive_summary(pdf_source_text, q_tok, q_mod, lvl):
                        full_response += chunk
                        
                        # --- FORMATTING & CLEANING ---
                        # Convert **Bold** to <b>Bold</b>
                        display = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', full_response)
                        # Remove Markdown symbols and add HTML line breaks
                        display = display.replace("#", "").replace("\n", "<br>")
                        
                        # 3. UPDATE THE BOX LIVE
                        box_slot.markdown(f'<div class="content-card">{display}</div>', unsafe_allow_html=True)
                    
                    st.session_state.pdf_result = full_response
                    status.update(label="Summary Complete!", state="complete")
            else:
                st.error("No text found for this topic.")

        # 4. PERSISTENT DISPLAY (Keep the box visible after finishing)
        elif "pdf_result" in st.session_state and st.session_state.pdf_result:
            res = st.session_state.pdf_result
            display = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', res).replace("#", "").replace("\n", "<br>")
            box_slot.markdown(f'<div class="content-card">{display}</div>', unsafe_allow_html=True)

        # 5. SAVE TO VAULT BUTTON
        if "pdf_result" in st.session_state and st.session_state.pdf_result:
            if st.button("💾 SAVE TO MY VAULT", key="save_pdf_vault_btn"):
                database.add_to_vault(st.session_state.user, "PDF", sel_topic, st.session_state.pdf_result)
                st.success(f"Saved: {sel_topic} 📂")

            
# --- WEBSITE SUMMARIZER FRAGMENT ---
@st.fragment
def web_summarizer_fragment():
    st.subheader("🌐 Web Deep-Dive")
    
    # 1. Reset Logic
    if st.button("🗑️ Reset Tab", key="reset_web"):
        st.session_state.web_result = None
        st.rerun()

    # 2. The Input Form
    with st.form("web_form_final"):
        url = st.text_input("Paste Article URL:", key="input_url_web")
        lvl = st.selectbox("Level:", ["Beginner", "Student", "Advanced"], key="input_lvl_web")
        submit = st.form_submit_button("🚀 GENERATE GUIDE")

    # 3. THE SINGLE SLOT
    box_slot = st.empty()

    if submit:
        if not url:
            st.warning("Please enter a URL first.")
        else:
            st.session_state.web_result = None # Clear old result
            
            with st.status("Reading & Analyzing...", expanded=True) as status:
                content = ai_engine.fetch_web_text(url)
                
                if content and "Error" not in content:
                    status.update(label="AI is writing your guide...", state="running")
                    
                    full_text = ""
                    # --- THE FIX: Everything must be inside the if block ---
                    for chunk in ai_engine.process_long_summary(content, lvl, q_tok, q_mod):
                        full_text += chunk
                        
                        # Cleaning & Formatting
                        display_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', full_text)
                        display_text = display_text.replace('\n', '<br>').replace('#', '')
                        
                        # Update the slot live
                        box_slot.markdown(f'<div class="content-card">{display_text}</div>', unsafe_allow_html=True)

                    # --- CRITICAL: Save the result to session state so the button can see it ---
                    st.session_state.web_result = full_text
                    status.update(label="Analysis Complete!", state="complete")
                else:
                    st.error(f"Failed: {content}")
                    status.update(label="Error", state="error")

    # 4. PERSISTENT DISPLAY (Fixes duplication and keeps box visible after generation)
    elif "web_result" in st.session_state and st.session_state.web_result:
        res = st.session_state.web_result
        display_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', res).replace('\n', '<br>').replace('#', '')
        box_slot.markdown(f'<div class="content-card">{display_text}</div>', unsafe_allow_html=True)

    # 5. THE SAVE BUTTON (Now it will see the web_result!)
    if "web_result" in st.session_state and st.session_state.web_result:
        st.write("") 
        if st.button("💾 SAVE TO VAULT", key="save_web_btn"):
            title = url.split("/")[-1] if "/" in url else "Web Article"
            database.add_to_vault(st.session_state.user, "WEB", title[:30], st.session_state.web_result)
            st.success("Saved to your Vault! 📂")     


#--- MCQ QUIZ TAB ---
@st.fragment
def quiz_generator_fragment(q_tok, q_mod):
    # --- 1. INITIALIZE STATE ---
    if "active_quiz_data" not in st.session_state: st.session_state.active_quiz_data = None
    if "submitted_quiz" not in st.session_state: st.session_state.submitted_quiz = False
    if "quiz_pdf_topics" not in st.session_state: st.session_state.quiz_pdf_topics = None
    if "last_processed_file" not in st.session_state: st.session_state.last_processed_file = None

    # --- NEW: RESET BUTTON ---
    col_h, col_res = st.columns([4, 1])
    with col_h:
        st.subheader("🚀 Turbo MCQ Generator")
    with col_res:
        if st.button("🗑️ Reset Tab", key="q_tab_reset", use_container_width=True):
            st.session_state.active_quiz_data = None
            st.session_state.submitted_quiz = False
            st.session_state.quiz_pdf_topics = None
            st.session_state.last_processed_file = None
            st.rerun()

    # --- STEP 1: UPLOAD & AUTO-SCAN ---
    q_pdf = st.file_uploader("1. Upload PDF", type="pdf", key="quiz_file_upro")
    
    if q_pdf and q_pdf.name != st.session_state.last_processed_file:
        with st.status("🔍 Scanning PDF and Extracting Topics...", expanded=True) as status:
            try:
                st.session_state.quiz_pdf_topics = ai_engine.extract_major_sections(q_pdf)
                st.session_state.last_processed_file = q_pdf.name
                st.session_state.active_quiz_data = None 
                st.session_state.submitted_quiz = False
                status.update(label="Scanning Complete!", state="complete", expanded=False)
                #st.rerun() 
            except Exception as e:
                st.error(f"Scan failed: {e}")

    # --- STEP 2: TOPIC SELECTION ---
    if st.session_state.quiz_pdf_topics:
        st.divider()
        topic_options = list(st.session_state.quiz_pdf_topics.keys())
        
        c1, c2 = st.columns([2, 1])
        with c1:
            sel_topic = st.selectbox("2. Select Topic:", topic_options, key="q_sel_topic")
        with c2:
            num_q = st.number_input("Questions:", 3, 10, 3, key="q_num_input")
        
        # --- STEP 3: HIGH-QUALITY GENERATION ---
        if st.button("⚡ GENERATE ACCURATE QUIZ", use_container_width=True, key="q_gen_final"):
            st.session_state.active_quiz_data = None
            st.session_state.submitted_quiz = False
            full_res = "" 
            
            # Using 3000 chars for deep context to ensure accurate distractors
            context = st.session_state.quiz_pdf_topics[sel_topic][:3000] 
            streamer = TextIteratorStreamer(q_tok, skip_prompt=True, skip_special_tokens=True)
            
            # --- THE EXPERT EXAMINER PROMPT ---
            prompt = f"""[CONTEXT]: {context}

[TASK]: You are an Academic Examiner. Generate {num_q} factual MCQs based ONLY on the [CONTEXT] provided.

[STRICT QUALITY RULES]:
1. Provide exactly 4 options per question.
2. One option must be the EXACT CORRECT FACT from the text.
3. The other 3 options must be PLAUSIBLE DISTRACTORS (they must sound realistic and be related to the topic, but are factually incorrect based on the context).
4. DO NOT use generic distractors like "None of the above" or "Everything".
5. NO labels like "A)", "B.", or "1.".
6. Return ONLY a valid JSON array.

[JSON FORMAT]:
[
  {{
    "question": "The specific question?",
    "options": ["Correct Answer Text", "Plausible Wrong 1", "Plausible Wrong 2", "Plausible Wrong 3"],
    "answer": "Correct Answer Text"
  }}
]
JSON:"""
            
            messages = [{"role": "user", "content": prompt}]
            t_in = q_tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            model_in = q_tok([t_in], return_tensors="pt").to(q_mod.device)

            t = Thread(target=q_mod.generate, kwargs=dict(
                **model_in, streamer=streamer, max_new_tokens=1500, 
                temperature=0.1, do_sample=True, repetition_penalty=1.1
            ))
            t.start()

            with st.status("🧠 Drafting Accurate Questions...", expanded=False) as status:
                for text in streamer:
                    full_res += text
                
                try:
                    # 1. Strip out markdown code fences if present
                    cleaned_res = re.sub(r'```json|```', '', full_res).strip()
                    
                    # 2. Extract the JSON array
                    match = re.search(r'\[.*\]', cleaned_res, re.DOTALL)
                    if match:
                        raw_json_string = match.group()
                        
                        # --- FIX: Clean common LLM JSON syntax errors ---
                        # Remove trailing commas right before closing brackets/braces
                        raw_json_string = re.sub(r',\s*\]', ']', raw_json_string)
                        raw_json_string = re.sub(r',\s*\}', '}', raw_json_string)
                        
                        try:
                            data = json.loads(raw_json_string)
                        except json.JSONDecodeError:
                            # Fallback: Use ast.literal_eval if LLM messed up quotes/trailing commas
                            import ast
                            data = ast.literal_eval(raw_json_string)
                            
                        valid_quiz = []
                        for item in data:
                            if isinstance(item, dict) and 'options' in item:
                                # Logic to Clean AI Labels (A, B, C) and handle spacing
                                clean_opts = []
                                for opt in item['options']:
                                    o = str(opt).strip()
                                    o = re.sub(r'^[A-Z0-9*.\-\)\s]+[.\)]\s*', '', o) # Strong Regex
                                    if len(o) > 1: clean_opts.append(o)
                                
                                clean_ans = re.sub(r'^[A-Z0-9*.\-\)\s]+[.\)]\s*', '', str(item.get('answer', ''))).strip()
                                final_opts = list(dict.fromkeys(clean_opts)) # Remove duplicates

                                # --- THE ACCURACY FILTER ---
                                if len(final_opts) >= 4:
                                    final_opts = final_opts[:4]
                                    if clean_ans not in final_opts:
                                        final_opts[0] = clean_ans
                                    
                                    random.shuffle(final_opts) # Randomize position of correct answer
                                    item['options'] = final_opts
                                    item['answer'] = clean_ans
                                    valid_quiz.append(item)
                        
                        if valid_quiz:
                            st.session_state.active_quiz_data = valid_quiz
                            status.update(label="High-Quality Quiz Ready!", state="complete")
                        else:
                            st.error("AI failed to generate high-quality questions. Try a larger topic.")
                            
                except Exception as e:
                    st.error(f"Generation Error: Your AI returned malformed JSON data. Reason: {e}")

    # --- STEP 4: DISPLAY & SUBMIT ---
    if st.session_state.active_quiz_data:
        st.divider()
        quiz_data = st.session_state.active_quiz_data
        
        # Important: Don't initialize correct_count outside the submission check
        current_score = 0
        
        for i, q in enumerate(quiz_data):
            st.markdown(f"**{i+1}. {q['question']}**")
            
            # Key must be consistent to retrieve values later
            choice = st.radio(
                f"q_{i}", q['options'], key=f"q_radio_{i}", 
                index=None, label_visibility="collapsed",
                disabled=st.session_state.submitted_quiz
            )
            
            if st.session_state.submitted_quiz:
                # Retrieve from session state to ensure accuracy after rerun
                user_choice = st.session_state.get(f"q_radio_{i}")
                if user_choice == q['answer']:
                    st.success(f"Correct! ✅")
                    current_score += 1
                else:
                    st.error(f"Incorrect. The correct answer was: **{q['answer']}**")
            st.write("") 

        if not st.session_state.submitted_quiz:
            if st.button("✅ FINISH & SAVE QUIZ", use_container_width=True, key="q_finish"):
                # 1. CALCULATE SCORE
                final_score = 0
                for i, q in enumerate(quiz_data):
                    if st.session_state.get(f"q_radio_{i}") == q['answer']:
                        final_score += 1
                
                # 2. SAVE TO DATABASE (Critical for Admin Analytics)
                import database
                database.save_score(st.session_state.user, final_score, len(quiz_data))
                
                # 3. TOGGLE STATE
                st.session_state.submitted_quiz = True
                #st.rerun()
        else:
            # Using current_score calculated in the loop above during the 'submitted' phase
            st.metric("Your Final Score", f"{current_score} / {len(quiz_data)}")
            if st.button("🔄 Try Another Topic", use_container_width=True, key="q_reset_internal"):
                st.session_state.active_quiz_data = None
                st.session_state.submitted_quiz = False
                #st.rerun()
            

#--- HELP TAB ---
@st.fragment
def help_guide_fragment():
    # --- HEADER ---
    st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <h2 style="color: #1e293b; font-family: Poppins; margin-bottom: 5px;">🚀 Getting Started with EduAI Pro</h2>
            <p style="color: #64748b; font-size: 1.1rem;">Master any document or website in minutes with our AI-powered study tools.</p>
        </div>
    """, unsafe_allow_html=True)

    # --- 3-STEP QUICK START ---
    st.markdown("### ⚡ The 3-Step Workflow")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div style="background: white; padding: 20px; border-radius: 15px; border-top: 4px solid #2563eb; height: 180px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <div style="font-size: 1.5rem; margin-bottom: 10px;">📤</div>
                <b style="color: #1e293b; font-size: 1rem;">1. Input Source</b>
                <p style="color: #64748b; font-size: 0.85rem; margin-top: 5px;">Upload a technical PDF or paste a long article URL from the web.</p>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div style="background: white; padding: 20px; border-radius: 15px; border-top: 4px solid #10b981; height: 180px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <div style="font-size: 1.5rem; margin-bottom: 10px;">🤖</div>
                <b style="color: #1e293b; font-size: 1rem;">2. AI Processing</b>
                <p style="color: #64748b; font-size: 0.85rem; margin-top: 5px;">Choose your learning level (Beginner to Advanced) and let the AI summarize.</p>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
            <div style="background: white; padding: 20px; border-radius: 15px; border-top: 4px solid #f59e0b; height: 180px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <div style="font-size: 1.5rem; margin-bottom: 10px;">💾</div>
                <b style="color: #1e293b; font-size: 1rem;">3. Save & Review</b>
                <p style="color: #64748b; font-size: 0.85rem; margin-top: 5px;">Save summaries to your private <b>Study Vault</b> or test yourself with the Quiz Generator.</p>
            </div>
        """, unsafe_allow_html=True)

    st.divider()

    # --- FEATURE BREAKDOWN ---
    st.markdown("### 🛠️ Feature Deep-Dive")
    
    with st.expander("📄 PDF Summarizer Tips", expanded=True):
        st.markdown("""
        - **Automatic Indexing:** Our AI automatically detects Chapters and Modules in your PDF. 
        - **Targeted Summaries:** Select a specific section from the list to get a concise summary of just that topic.
        - **Best Results:** Use PDFs that have selectable text. Scanned images may not process correctly.
        """)

    with st.expander("🌐 Web Summarizer Tips"):
        st.markdown("""
        - **Clean Reading:** We use **Jina Reader** to strip away ads, popups, and navigation bars from websites.
        - **Adaptive Learning:** 
            - *Beginner (ELI5):* Uses analogies and simple words.
            - *Student:* Focuses on academic definitions and logic.
            - *Advanced:* Provides technical deep-dives into architecture and mechanics.
        """)

    with st.expander("📊 Using Your Study Vault"):
        st.markdown("""
        - Access the **Study Vault** from the sidebar to see everything you've saved.
        - Every saved entry includes the source title, the date, and the AI-generated summary.
        - **Pro Tip:** Review your Vault every 3 days to improve long-term memory retention.
        """)

    # --- FOOTER ---
    st.markdown("""
        <div style="background: #eff6ff; padding: 15px; border-radius: 10px; border: 1px solid #bfdbfe; margin-top: 30px; text-align: center;">
            <p style="margin: 0; color: #1e40af; font-size: 0.9rem;">✨ <b>Need help?</b> Contact your administrator or explore the <b>Discovery Feed</b> for more resources.</p>
        </div>
    """, unsafe_allow_html=True)


def reset_app_state():
    # We clear everything EXCEPT login info
    for key in list(st.session_state.keys()):
        if key not in ['authenticated', 'user']:
            del st.session_state[key]
    st.rerun()

# 4. SIDEBAR (User Profile & Discovery Feed)
with st.sidebar:
    st.markdown(f"<h2 style='color: #1e293b; margin-bottom:0;'>Hello, {st.session_state.user}</h2>", unsafe_allow_html=True)
    st.caption("Personalized Learning Portal")
    st.write("")
    
    # The Appeals-Styled Navigation
    nav = st.radio("Navigate", ["🚀 Learning Hub", "📂 Study Vault", "📊 Analytics"], label_visibility="collapsed")
    
    st.write("")
    if st.button("🚪 LOGOUT", use_container_width=True):
        st.session_state.auth = False
        st.rerun()

        st.write(f"👤 User: **{st.session_state.user}**")
    
    st.divider()
    # GLOBAL REFRESH BUTTON
    if st.button("🔄 Reset Global State", use_container_width=True):
        reset_app_state()

# 5. MAIN PAGE ROUTING



if st.session_state.role == "admin":
    # STRICT ADMIN VIEW: No Student Tabs, No Discovery Feed
        # HIDE SIDEBAR FOR ADMIN
        st.markdown("<style>[data-testid='stSidebar'] {display:none;}</style>", unsafe_allow_html=True)
        
        # Logout button in top right
        if st.button("🚪 Logout Admin"):
            st.session_state.auth = False
            st.rerun()
    
        admin_dashboard_view() 

else:
    # STUDENT VIEW: Your original layout with Feed and Tabscol_content, col_feed = st.columns([4, 1], gap="medium")
    col_content, col_feed = st.columns([4, 1], gap="medium")
    with col_feed:
        discovery_feed_fragment()


    with col_content:
        # --- INSIDE app.py (Learning Hub Section) ---
        if nav == "🚀 Learning Hub":
            st.markdown('<div class="header-text">🎓 EduAI </div>', unsafe_allow_html=True)
            
            tab1, tab2, tab3, tab4 = st.tabs(["📄 PDF Summarizer", "🌐 Web Summarizer", "📝 Quiz Generator", "❓ Help Guide"])

            with tab1:
                pdf_summarizer_fragment() 

            with tab2:
                web_summarizer_fragment() 

            with tab3:
                quiz_generator_fragment(q_tok, q_mod)

            with tab4:
                help_guide_fragment()

        elif nav == "📂 Study Vault":
            st.markdown('<div class="header-text">📂 Personal Study Vault</div>', unsafe_allow_html=True)
            st.caption("Access and manage your saved AI-generated deep dives.")

            # --- 1. FETCH DATA FIRST (This solves the NameError) ---
            history = database.get_vault_data(st.session_state.user)

            # --- 2. DEFINE THE HELPER FUNCTION ---
            def render_vault_item(h, idx):
                doc_type, title, date, content = h
                display_title = title if (title and title.strip()) else f"{doc_type} Summary ({date})"
                
                st.markdown(f"""
                    <div style="background: white; padding: 20px; border-radius: 15px; border-left: 6px solid {'#2563eb' if doc_type == 'PDF' else '#10b981'}; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 20px;">
                        <span style="font-size: 0.75rem; font-weight: bold; color: #64748b; text-transform: uppercase;">{doc_type} • {date}</span>
                        <h4 style="margin: 10px 0; color: #1e293b; font-family: Poppins;">{display_title}</h4>
                        <div style="color: #475569; font-size: 0.95rem; line-height: 1.6; margin-bottom: 15px;">
                            {content[:250]}...
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                col_view, col_dl, col_del = st.columns([3, 1, 1])
                with col_view:
                    with st.expander(f"🔍 View Full Content"):
                        st.markdown(content.replace('\n', '<br>'), unsafe_allow_html=True)
                with col_dl:
                    st.download_button("📥 Download", data=content, file_name=f"{display_title}.txt", key=f"dl_{idx}")
                with col_del:
                    if st.button("🗑️ DELETE", key=f"del_{idx}", use_container_width=True):
                        database.delete_vault_item(st.session_state.user, title, date)
                        st.rerun()

            # --- 3. MAIN DISPLAY LOGIC ---
            if not history:
                st.info("Your vault is empty. Generate and save a summary to see it here!")
            else:
                tab_all, tab_pdf, tab_web = st.tabs(["🗂️ All Resources", "📄 PDF Summaries", "🌐 Web Guides"])

                with tab_all:
                    for i, h in enumerate(history):
                        render_vault_item(h, f"all_{i}")

                with tab_pdf:
                    pdf_items = [h for h in history if h[0] == "PDF"]
                    if not pdf_items: 
                        st.write("No PDF summaries saved.")
                    else:
                        for i, h in enumerate(pdf_items):
                            render_vault_item(h, f"pdf_{i}")

                with tab_web:
                    web_items = [h for h in history if h[0] == "WEB"]
                    if not web_items: 
                        st.write("No web guides saved.")
                    else:
                        for i, h in enumerate(web_items):
                            render_vault_item(h, f"web_{i}")


        elif nav == "📊 Analytics":
            st.markdown('<div class="header-text">📊 Academic Performance Analytics</div>', unsafe_allow_html=True)
            
            # 1. DATA EXTRACTION
            import sqlite3
            conn = sqlite3.connect('learning_platform.db')
            df_vault = pd.read_sql_query(f"SELECT type, date FROM vault WHERE username='{st.session_state.user}'", conn)
            df_scores = pd.read_sql_query(f"SELECT score, total, date FROM scores WHERE username='{st.session_state.user}'", conn)
            conn.close()

            # 2. TOP LEVEL SUMMARY METRICS
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Studies", len(df_vault))
            with col2:
                quiz_count = len(df_scores)
                st.metric("Quizzes Taken", quiz_count)
            with col3:
                if not df_scores.empty:
                    avg = (df_scores['score'].sum() / df_scores['total'].sum()) * 100
                    st.metric("Avg. Accuracy", f"{int(avg)}%")
                else: st.metric("Avg. Accuracy", "0%")
            with col4:
                consistency = len(df_vault['date'].unique()) if not df_vault.empty else 0
                st.metric("Study Days", consistency)

            st.divider()

            # 3. ANALYSIS RADIO NAVIGATION
            # This uses your existing CSS for horizontal tabs
            view = st.radio("Select Analysis Depth:", 
                            ["📚 Resource Distribution", "📝 Quiz Performance Logs"], 
                            horizontal=True, label_visibility="collapsed")

            st.write("") # Spacing

            # --- VIEW 1: RESOURCE DISTRIBUTION ---
            if view == "📚 Resource Distribution":
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.subheader("Source Mix: PDF vs Web")
                    if not df_vault.empty:
                        counts = df_vault['type'].value_counts()
                        st.bar_chart(counts, color="#2563eb")
                    else: st.info("No data in vault yet.")
                
                with c2:
                    st.markdown("""
                    <div style="background: white; padding: 20px; border-radius: 15px; border: 1px solid #e2e8f0;">
                        <h4 style='margin-top:0;'>💡 Source Insight</h4>
                        <p style='font-size: 0.9rem; color: #64748b;'>
                        Your learning is currently balanced between uploaded documents and web articles. 
                        Integrating multiple sources improves cognitive flexibility.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

            # --- VIEW 2: QUIZ PERFORMANCE LOGS ---
            elif view == "📝 Quiz Performance Logs":
                if not df_scores.empty:
                    # A. The Progress Graph
                    st.subheader("Mastery Trend Over Time")
                    df_scores['percentage'] = (df_scores['score'] / df_scores['total']) * 100
                    chart_data = df_scores.groupby('date')['percentage'].mean().sort_index()
                    st.line_chart(chart_data, color="#10b981")

                    # B. The Detailed List (The "When" and "Which Score")
                    st.subheader("Detailed Session History")
                    # Format the table for the user
                    df_display = df_scores[['date', 'score', 'total', 'percentage']].copy()
                    df_display.columns = ['Date Taken', 'Correct', 'Out Of', 'Accuracy %']
                    
                    # Show as an interactive table
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                else:
                    st.info("No quiz scores recorded yet. Complete a quiz in the Learning Hub to see analysis!")




       