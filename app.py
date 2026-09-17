import os
import random
import time
from google import genai
from google.genai import types
import streamlit as st

# ==========================================
# Page Configuration & Custom Icon
# ==========================================
st.set_page_config(
    page_title="Gemini",
    page_icon="gemini_star.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&display=swap');

    /* Global Dark Theme Background - Zero White Bleed Everywhere */
    .stApp, .main, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stBottom"], [data-testid="stBottomBlockContainer"] { 
        background-color: #131314 !important; 
        color: #e3e3e3 !important; 
        font-family: 'Google Sans', sans-serif;
    }
    
    header[data-testid="stHeader"] {
        background-color: transparent !important;
        visibility: hidden;
    }
    
    .block-container {
        background-color: #131314 !important;
        color: #e3e3e3 !important;
        padding-top: 2rem;
        padding-bottom: 140px;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #1e1f20 !important;
        border-right: 1px solid #282a2c;
        padding-top: 5px;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Completely Dark Bottom Container for Chat Input */
    [data-testid="stBottom"] {
        background-color: #131314 !important;
        border-top: none !important;
    }
    [data-testid="stBottomBlockContainer"] {
        background-color: #131314 !important;
    }
    
    /* Chat Input Container & Box Styling (Forced Black Input Text) */
    div[data-testid="stChatInputContainer"] {
        background-color: #131314 !important;
        border-top: none !important;
    }
    .stChatInput {
        background-color: #f0f4f9 !important;
        border: 1px solid #444746 !important;
        border-radius: 28px !important;
        padding: 4px !important;
    }
    .stChatInput textarea {
        background-color: transparent !important;
        color: #000000 !important;
        font-family: 'Google Sans', sans-serif !important;
        font-size: 15px !important;
        font-weight: 500 !important;
    }
    .stChatInput textarea::placeholder {
        color: #5e615f !important;
    }

    /* Custom Sidebar Navigation Buttons */
    div.stButton > button:first-child {
        background: #1e1f20;
        color: #e3e3e3; 
        border: 1px solid #444746; 
        border-radius: 20px; 
        font-weight: 500;
        padding: 0.4rem 1rem; 
        width: 100%;
        text-align: left;
        transition: background 0.2s;
    }
    div.stButton > button:first-child:hover {
        background: #282a2c;
        border-color: #8e918f;
    }

    /* Clean Chat Message Bubbles - Prevent Artifacts */
    div[data-testid="stChatMessage"] {
        background-color: transparent !important;
        padding: 12px 0 !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.03);
    }
    
    /* Custom UI for Tabs & Expanders (Student & Notebook Features) */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; border-bottom: 1px solid #282a2c; }
    .stTabs [data-baseweb="tab"] { color: #8e918f !important; font-family: 'Google Sans', sans-serif; }
    .stTabs [aria-selected="true"] { color: #e3e3e3 !important; border-bottom: 2px solid #e3e3e3 !important; }
    div[data-testid="stExpander"] { background-color: #1e1f20 !important; border: 1px solid #444746 !important; border-radius: 12px !important; }
    div[data-testid="stExpander"] summary p { color: #e3e3e3 !important; font-weight: 500 !important; font-size: 16px; }
    
    /* Immersive View Styling */
    .immersive-view { background-color: #131314; padding: 40px; border-radius: 20px; border: 1px solid #444746; font-size: 18px; line-height: 1.8; color: #f0f0f0; }
    </style>
""",
    unsafe_allow_html=True,
)

# Initialize Gemini Client securely
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")


# ==========================================
# Session State Initialization
# ==========================================
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "student_chat" not in st.session_state:
    st.session_state.student_chat = []
if "saved_images" not in st.session_state:
    st.session_state.saved_images = []
if "notes" not in st.session_state:
    st.session_state.notes = [{"id": 0, "title": "Welcome to Notebooks", "content": "Write your ideas, code snippets, and study materials here!"}]
if "active_view" not in st.session_state:
    st.session_state.active_view = "💬 Chat Assistant"
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "is_guest" not in st.session_state:
    st.session_state.is_guest = False

# Auth States
if "registered_users" not in st.session_state:
    st.session_state.registered_users = {}
if "auth_step" not in st.session_state:
    st.session_state.auth_step = "login_register"
if "pending_reg" not in st.session_state:
    st.session_state.pending_reg = {}
if "verification_code" not in st.session_state:
    st.session_state.verification_code = ""

if "captcha_q" not in st.session_state:
    n1, n2 = random.randint(1, 9), random.randint(1, 9)
    st.session_state.captcha_q = f"{n1} + {n2}"
    st.session_state.captcha_ans = str(n1 + n2)

# Helper function for API retries
def call_gemini_with_retry(api_call_func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return api_call_func()
        except Exception as e:
            err_str = str(e)
            if ("503" in err_str or "429" in err_str) and attempt < max_retries - 1:
                time.sleep(2 * (attempt + 1))
                continue
            else:
                raise e

# Simple Text Completion Helper
def query_gemini_text(prompt_text):
    if not api_key:
        return "⚠️ Please configure your Gemini API Key."
    client = genai.Client(api_key=api_key)
    def fetch():
        return client.models.generate_content(model="gemini-3.6-flash", contents=prompt_text)
    response = call_gemini_with_retry(fetch)
    return response.text


# ==========================================
# Authentication Hub
# ==========================================
if not st.session_state.user_name and not st.session_state.is_guest:
    st.markdown(
        "<div style='max-width: 480px; margin: 50px auto; padding: 30px; background-color: #1e1f20; border: 1px solid #444746; border-radius: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.5);'>"
        "<div style='text-align: center; margin-bottom: 20px;'><h2 style='color: #e3e300; margin-bottom: 5px;'>✨ Gemini Workspace</h2><p style='color: #8e918f; font-size: 14px;'>Secure Authentication Portal</p></div>",
        unsafe_allow_html=True,
    )
    col_space1, col_center, col_space2 = st.columns([0.1, 3.8, 0.1])
    with col_center:
        if st.session_state.auth_step == "verify_email":
            st.info(f"🔐 [Simulation Notice] Code: **{st.session_state.verification_code}**")
            entered_code = st.text_input("Enter 6-digit Code", max_chars=6)
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                if st.button("❌ Cancel", use_container_width=True):
                    st.session_state.auth_step = "login_register"
                    st.rerun()
            with col_v2:
                if st.button("✅ Verify", use_container_width=True):
                    if entered_code == st.session_state.verification_code:
                        p_data = st.session_state.pending_reg
                        st.session_state.registered_users[p_data["email"]] = p_data
                        st.session_state.user_name = p_data["name"]
                        st.session_state.auth_step = "login_register"
                        st.rerun()
                    else:
                        st.error("Invalid verification code.")
        else:
            auth_tab1, auth_tab2 = st.tabs(["🔑 Sign In", "📝 Register"])
            with auth_tab1:
                si_email = st.text_input("Email", placeholder="name@example.com", key="si_email")
                si_pass = st.text_input("Password", type="password", key="si_pass")
                if st.button("🚀 Sign In", use_container_width=True):
                    user_record = st.session_state.registered_users.get(si_email)
                    if user_record and user_record["password"] == si_pass:
                        st.session_state.user_name = user_record["name"]
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")
            with auth_tab2:
                reg_name = st.text_input("Full Name", key="reg_name")
                reg_email = st.text_input("Email Address", key="reg_email")
                reg_pass = st.text_input("Password", type="password", key="reg_pass")
                st.caption(f"🔒 Prove you're human: **{st.session_state.captcha_q}** = ?")
                reg_cap = st.text_input("Answer", key="reg_cap")
                if st.button("📨 Send Verification Code", use_container_width=True):
                    if reg_cap.strip() != st.session_state.captcha_ans:
                        st.error("Incorrect CAPTCHA.")
                    elif reg_email in st.session_state.registered_users:
                        st.error("Email already exists.")
                    elif reg_name and reg_email and reg_pass:
                        st.session_state.verification_code = str(random.randint(100000, 999999))
                        st.session_state.pending_reg = {"name": reg_name.strip(), "email": reg_email.strip(), "password": reg_pass}
                        st.session_state.auth_step = "verify_email"
                        st.rerun()
            
            st.markdown("<div style='border-top: 1px solid #444746; margin: 20px 0; text-align: center;'><span style='background-color: #1e1f20; padding: 0 10px; color: #8e918f;'>OR</span></div>", unsafe_allow_html=True)
            if st.button("👤 Continue as Free Guest", use_container_width=True):
                st.session_state.user_name = "Guest"
                st.session_state.is_guest = True
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


# ==========================================
# Sidebar Navigation
# ==========================================
with st.sidebar:
    st.markdown("<h3 style='color: #e3e3e3; font-size: 18px;'>✨ Gemini</h3>", unsafe_allow_html=True)
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    if st.button("➕ New chat"): st.session_state.active_view = "💬 Chat Assistant"; st.rerun()
    if st.button("🔍 Search chats"): st.session_state.active_view = "🔍 Search chats"; st.rerun()
    if st.button("🎓 Students"): st.session_state.active_view = "🎓 Students"; st.rerun()
    if st.button("🖼️ Images"): st.session_state.active_view = "🎨 Image Generator"; st.rerun()
    if st.button("📁 Library"): st.session_state.active_view = "📁 Library"; st.rerun()
    if st.button("📓 Notebook"): st.session_state.active_view = "📓 Notebook"; st.rerun()

    st.markdown("<div style='margin-top: 40px;'>---</div>", unsafe_allow_html=True)
    st.write(f"👤 **{st.session_state.user_name}**")
    if st.button("🚪 Logout", help="Switch Account"):
        st.session_state.user_name = None
        st.session_state.is_guest = False
        st.rerun()


# ==========================================
# MODULE 1: Main Chat Assistant
# ==========================================
if st.session_state.active_view == "💬 Chat Assistant":
    if not st.session_state.chat_messages:
        st.markdown(f"<h1 style='color: #e3e3e3; font-weight: 500;'>Hello, {st.session_state.user_name}</h1>", unsafe_allow_html=True)
        st.markdown("<h2 style='color: #8e918f; font-weight: 400;'>How can I help you today?</h2>", unsafe_allow_html=True)
    
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "✨"):
            st.markdown(message["content"])

    uploaded_file = st.file_uploader("➕ Upload any file (Image, Code, PDF, ZIP)", label_visibility="collapsed")
    if user_query := st.chat_input("Ask Gemini..."):
        file_content = []
        if uploaded_file:
            file_content.append(f"\n[Attached {uploaded_file.name}]\n")
        file_content.append(user_query)

        st.session_state.chat_messages.append({"role": "user", "content": user_query})
        with st.chat_message("user", avatar="👤"): st.markdown(user_query)

        with st.chat_message("assistant", avatar="✨"):
            with st.spinner("Gemini is thinking..."):
                try:
                    reply = query_gemini_text(" ".join(file_content))
                    st.markdown(reply)
                    st.session_state.chat_messages.append({"role": "model", "content": reply})
                except Exception as e:
                    st.error(f"Chat Error: {e}")


# ==========================================
# MODULE 2: Search Chats
# ==========================================
elif st.session_state.active_view == "🔍 Search chats":
    st.title("🔍 Search Your Chats")
    st.markdown("<p style='color: #8e918f;'>Quickly find answers, links, and code from your previous conversations.</p><hr>", unsafe_allow_html=True)
    
    search_q = st.text_input("Enter keywords to search...", placeholder="e.g. Python scripts, FIFA World Cup, etc.")
    
    if search_q:
        results = [m for m in st.session_state.chat_messages if search_q.lower() in m['content'].lower()]
        if results:
            st.success(f"Found {len(results)} matching messages.")
            for r in results:
                with st.chat_message(r['role'], avatar="👤" if r['role']=="user" else "✨"):
                    highlighted = r['content'].replace(search_q, f"**{search_q}**")
                    st.markdown(highlighted)
        else:
            st.warning("No matching messages found in your current session history.")
    else:
        st.info("Start typing above to search through your active chat history.")


# ==========================================
# MODULE 3: Students Workspace (Gemini Edu)
# ==========================================
elif st.session_state.active_view == "🎓 Students":
    if st.session_state.is_guest:
        st.error("🔒 Premium Feature Restricted")
        st.warning("Free guests cannot access the Student Workspace. Please sign in.")
    else:
        st.title("🎓 Student Workspace")
        st.markdown("<p style='color: #8e918f;'>Supercharge your studies with Gemini's AI learning tools.</p>", unsafe_allow_html=True)
        
        tab_learn, tab_quiz, tab_flash, tab_focus = st.tabs(["📖 Guided Learning", "📝 Quiz Yourself", "🗂️ Flashcards", "🌌 Immersive View"])
        
        # --- GUIDED LEARNING ---
        with tab_learn:
            st.subheader("Step-by-Step Socratic Tutor")
            st.info("Gemini will guide you to figure things out step-by-step through questions.")
            
            for m in st.session_state.student_chat:
                with st.chat_message(m["role"], avatar="👤" if m["role"] == "user" else "✨"):
                    st.markdown(m["content"])
                    
            if student_q := st.chat_input("What topic or problem are you stuck on?", key="student_input"):
                st.session_state.student_chat.append({"role": "user", "content": student_q})
                st.rerun()
                
            if st.session_state.student_chat and st.session_state.student_chat[-1]["role"] == "user":
                with st.chat_message("assistant", avatar="✨"):
                    with st.spinner("Preparing guidance..."):
                        socratic_prompt = f"Act as an expert Socratic tutor. A student asks: '{st.session_state.student_chat[-1]['content']}'. DO NOT give the direct answer. Break down the concept and ask a guiding question."
                        s_reply = query_gemini_text(socratic_prompt)
                        st.markdown(s_reply)
                        st.session_state.student_chat.append({"role": "model", "content": s_reply})

        # --- QUIZ YOURSELF ---
        with tab_quiz:
            st.subheader("Interactive AI Practice Test")
            quiz_topic = st.text_input("Enter a subject or paste your notes to generate an interactive quiz:")
            if st.button("📝 Generate Interactive Quiz"):
                if quiz_topic:
                    with st.spinner("Generating quiz questions..."):
                        q_prompt = (
                            f"Create a 3-question multiple choice quiz about '{quiz_topic}'. "
                            "Format each question EXACTLY using these tags:\n"
                            "QUESTION: [Question text]\n"
                            "A) [Option A text]\n"
                            "B) [Option B text]\n"
                            "C) [Option C text]\n"
                            "D) [Option D text]\n"
                            "CORRECT: [A, B, C, or D]\n"
                        )
                        q_res = query_gemini_text(q_prompt)
                        
                        quiz_list = []
                        blocks = q_res.split("QUESTION:")
                        for block in blocks:
                            if not block.strip():
                                continue
                            lines = [l.strip() for l in block.split("\n") if l.strip()]
                            if len(lines) >= 6:
                                q_text = lines[0]
                                opts = {
                                    "A": lines[1][2:].strip(),
                                    "B": lines[2][2:].strip(),
                                    "C": lines[3][2:].strip(),
                                    "D": lines[4][2:].strip()
                                }
                                corr_line = [l for l in lines if l.startswith("CORRECT:")]
                                correct_ans = corr_line[0].replace("CORRECT:", "").strip()[:1].upper() if corr_line else "A"
                                quiz_list.append({"q": q_text, "options": opts, "correct": correct_ans})
                        
                        st.session_state.active_quiz = quiz_list
                        st.success("Quiz generated successfully! Answer below:")
                else:
                    st.warning("Please enter a topic.")

            if "active_quiz" in st.session_state and st.session_state.active_quiz:
                st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                user_answers = {}
                for idx, q_item in enumerate(st.session_state.active_quiz):
                    st.markdown(f"**Q{idx+1}: {q_item['q']}**")
                    opt_keys = list(q_item["options"].keys())
                    formatted_opts = [f"{k}) {q_item['options'][k]}" for k in opt_keys]
                    
                    selected = st.radio(
                        f"Select your answer for Question {idx+1}",
                        formatted_opts,
                        key=f"quiz_q_{idx}",
                        label_visibility="collapsed"
                    )
                    user_answers[idx] = selected[0]
                    st.markdown("---")

                if st.button("📊 Submit and Grade Quiz"):
                    score = 0
                    total = len(st.session_state.active_quiz)
                    for idx, q_item in enumerate(st.session_state.active_quiz):
                        if user_answers.get(idx) == q_item["correct"]:
                            score += 1
                    
                    if score == total:
                        st.success(f"🎉 Excellent work! Your Score: **{score}/{total}**")
                    elif score >= total / 2:
                        st.info(f"👍 Good job! Your Score: **{score}/{total}**")
                    else:
                        st.warning(f"💡 Keep practicing! Your Score: **{score}/{total}**")

        # --- FLASHCARDS ---
        with tab_flash:
            st.subheader("Interactive AI Flashcard Deck")
            flash_topic = st.text_input("Enter a topic for flashcards:")
            if st.button("🗂️ Generate Flashcard Deck"):
                if flash_topic:
                    with st.spinner("Generating interactive flashcards..."):
                        f_prompt = f"Generate 5 distinct flashcards for '{flash_topic}'. Format EXACTLY like this: 'TERM: [term] | DEF: [definition]'. Do not include any other text."
                        f_res = query_gemini_text(f_prompt)
                        
                        deck = []
                        lines = f_res.split("\n")
                        for line in lines:
                            if "TERM:" in line and "DEF:" in line:
                                parts = line.split("| DEF:")
                                term = parts[0].replace("TERM:", "").strip()
                                definition = parts[1].strip() if len(parts) > 1 else ""
                                if term and definition:
                                    deck.append({"term": term, "def": definition})
                        st.session_state.flashcard_deck = deck
                        st.success("Flashcard deck generated successfully!")
                else:
                    st.warning("Please enter a topic.")

            if "flashcard_deck" in st.session_state and st.session_state.flashcard_deck:
                st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
                for idx, card in enumerate(st.session_state.flashcard_deck):
                    flip_key = f"flip_{idx}"
                    if flip_key not in st.session_state:
                        st.session_state[flip_key] = False
                    
                    is_flipped = st.session_state[flip_key]
                    content_to_show = card["term"] if not is_flipped else card["def"]
                    card_title = f"Flashcard {idx+1} ({'Definition' if is_flipped else 'Term'})"
                    label_text = "💡 Click to see Definition" if not is_flipped else "🔄 Click to see Term"
                    
                    st.markdown(f"""
                    <div style="background-color: #1e1f20; border: 1px solid #444746; border-radius: 16px; padding: 25px; text-align: center; margin-bottom: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
                        <p style="color: #8e918f; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">{card_title}</p>
                        <h3 style="color: #e3e3e3; font-size: 20px; font-weight: 500; margin-bottom: 0;">{content_to_show}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(label_text, key=f"btn_card_{idx}", use_container_width=True):
                        st.session_state[flip_key] = not is_flipped
                        st.rerun()

        # --- IMMERSIVE VIEW ---
        with tab_focus:
            st.subheader("Distraction-Free Reading")
            focus_topic = st.text_area("Paste text or ask Gemini to explain a topic:")
            if st.button("🌌 Enter Immersive View"):
                if focus_topic:
                    with st.spinner("Formatting immersive view..."):
                        i_prompt = f"Write a comprehensive, engaging explanation of '{focus_topic}'."
                        i_text = query_gemini_text(i_prompt)
                        st.markdown(f"<div class='immersive-view'>{i_text}</div>", unsafe_allow_html=True)


# ==========================================
# MODULE 4: Library (Image Gallery)
# ==========================================
elif st.session_state.active_view == "📁 Library":
    st.title("📁 Your Media Library")
    st.markdown("<p style='color: #8e918f;'>All your generated visual artwork is safely stored here.</p><hr>", unsafe_allow_html=True)
    
    if not st.session_state.saved_images:
        st.info("Your library is currently empty. Head over to the **Image Generator** to create artwork!")
    else:
        cols = st.columns(3)
        for idx, img_data in enumerate(st.session_state.saved_images):
            with cols[idx % 3]:
                st.image(img_data["bytes"], use_container_width=True)
                with st.expander("Image Details"):
                    st.caption(f"**Prompt:** {img_data['prompt']}")
                    st.download_button("📥 Download", data=img_data["bytes"], file_name=f"gemini_art_{idx}.jpg", mime="image/jpeg", key=f"dl_{idx}")


# ==========================================
# MODULE 5: Image Generator
# ==========================================
elif st.session_state.active_view == "🎨 Image Generator":
    if st.session_state.is_guest:
        st.error("🔒 Feature Restricted for Guests")
    else:
        st.title("🎨 Image Generation Studio")
        st.markdown("<hr>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1.2])
        with col1:
            img_prompt = st.text_area("Image description:")
            if st.button("✨ Generate & Save to Library"):
                with st.spinner("Generating artwork..."):
                    try:
                        client = genai.Client(api_key=api_key)
                        res = client.models.generate_content(
                            model="gemini-3.1-flash-image", 
                            contents=img_prompt, 
                            config=types.GenerateContentConfig(response_modalities=["IMAGE"])
                        )
                        image_saved = False
                        for candidate in res.candidates:
                            for part in candidate.content.parts:
                                if part.inline_data:
                                    img_bytes = part.inline_data.data
                                    st.session_state.saved_images.append({"bytes": img_bytes, "prompt": img_prompt})
                                    image_saved = True
                        if image_saved:
                            st.success("Image generated and saved to your 📁 Library!")
                            st.rerun()
                        else:
                            st.error("No image data returned. Please try modifying your prompt.")
                    except Exception as e:
                        st.error(f"Generation Error: {e}")
        with col2:
            st.info("Generated images will be automatically saved to your **Library** tab.")


# ==========================================
# MODULE 6: Notebook Interface
# ==========================================
elif st.session_state.active_view == "📓 Notebook":
    if st.session_state.is_guest:
        st.error("🔒 Feature Restricted for Guests")
    else:
        st.title("📓 Private Notebooks")
        st.markdown("<hr>", unsafe_allow_html=True)
        
        col_list, col_edit = st.columns([1, 2.5])
        
        with col_list:
            if st.button("➕ Create New Note", use_container_width=True):
                new_id = len(st.session_state.notes)
                st.session_state.notes.append({"id": new_id, "title": f"Untitled Note {new_id}", "content": ""})
                st.session_state.current_note_id = new_id
                
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            for i, note in enumerate(st.session_state.notes):
                if st.button(f"📄 {note['title']}", key=f"n_btn_{i}", use_container_width=True):
                    st.session_state.current_note_id = i

        with col_edit:
            current_id = st.session_state.get("current_note_id", 0)
            if current_id < len(st.session_state.notes):
                active_note = st.session_state.notes[current_id]
                
                new_title = st.text_input("Note Title", value=active_note["title"])
                new_content = st.text_area("Content", value=active_note["content"], height=400)
                
                if st.button("💾 Save Note Changes"):
                    st.session_state.notes[current_id]["title"] = new_title
                    st.session_state.notes[current_id]["content"] = new_content
                    st.success("Note securely saved!")
