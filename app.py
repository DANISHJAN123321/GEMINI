import os
import random
import time
from google import genai
from google.genai import types
import streamlit as st

# ==========================================
# Page Configuration & Red/White Theme
# ==========================================
st.set_page_config(
    page_title="Gemini Workspace",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&display=swap');

    /* Global Light Theme: Clean Crisp White & Crimson Red Accents */
    .stApp, .main, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stBottom"], [data-testid="stBottomBlockContainer"] { 
        background-color: #ffffff !important; 
        color: #111111 !important; 
        font-family: 'Google Sans', sans-serif;
    }
    
    header[data-testid="stHeader"] { background-color: transparent !important; visibility: hidden; }
    
    .block-container {
        background-color: #ffffff !important;
        color: #111111 !important;
        padding-top: 2rem;
        padding-bottom: 140px;
    }

    /* Sidebar Styling: Pure White with Subtle Red Border */
    section[data-testid="stSidebar"] {
        background-color: #fcfcfc !important;
        border-right: 2px solid #fce8e6;
        padding-top: 5px;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Chat Input Container & Box Styling: High Contrast Visibility */
    [data-testid="stBottom"], [data-testid="stBottomBlockContainer"], div[data-testid="stChatInputContainer"] {
        background-color: #ffffff !important;
        border-top: none !important;
    }
    
    .stChatInput {
        background-color: #ffffff !important;
        border: 2px solid #d93025 !important;
        border-radius: 28px !important;
        padding: 4px !important;
    }
    .stChatInput textarea {
        background-color: transparent !important;
        color: #111111 !important;
        font-family: 'Google Sans', sans-serif !important;
        font-size: 15px !important;
        font-weight: 500 !important;
    }
    .stChatInput textarea::placeholder {
        color: #5f6368 !important;
    }

    /* Smooth Modern Rounded Red & White Buttons */
    div.stButton > button:first-child, .stDownloadButton > button {
        background: #ffffff;
        color: #d93025; 
        border: 2px solid #d93025; 
        border-radius: 24px !important; 
        font-weight: 600;
        padding: 0.5rem 1.2rem; 
        width: 100%;
        text-align: center;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 2px 6px rgba(217,48,37,0.1);
    }
    div.stButton > button:first-child:hover, .stDownloadButton > button:hover {
        background: #d93025;
        color: #ffffff;
        border-color: #d93025;
        transform: translateY(-1px);
    }

    /* Rounded Text Inputs & Selectboxes with Red Accent */
    .stTextInput input, .stSelectbox [data-baseweb="select"] {
        border-radius: 20px !important;
        background-color: #ffffff !important;
        border: 2px solid #f1f3f4 !important;
        color: #111111 !important;
    }
    .stTextInput input:focus, .stSelectbox [data-baseweb="select"]:focus-within {
        border-color: #d93025 !important;
    }

    /* Clean Chat Message Bubbles with High Legibility */
    div[data-testid="stChatMessage"] {
        background-color: #f8f9fa !important;
        border-radius: 16px;
        padding: 16px !important;
        margin-bottom: 12px;
        border: 1px solid #f1f3f4;
    }
    div[data-testid="stChatMessage"] p, div[data-testid="stChatMessage"] span, div[data-testid="stChatMessage"] li {
        color: #202124 !important;
        font-size: 15px !important;
        line-height: 1.6 !important;
    }
    
    /* Tabs & Expanders */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; border-bottom: 2px solid #fce8e6; }
    .stTabs [data-baseweb="tab"] { color: #5f6368 !important; font-family: 'Google Sans', sans-serif; font-weight: 600; border-radius: 12px 12px 0 0; }
    .stTabs [aria-selected="true"] { color: #d93025 !important; border-bottom: 3px solid #d93025 !important; background-color: #fce8e6 !important; }
    div[data-testid="stExpander"] { background-color: #ffffff !important; border: 2px solid #f1f3f4 !important; border-radius: 16px !important; }
    div[data-testid="stExpander"] summary p { color: #202124 !important; font-weight: 600 !important; font-size: 16px; }
    </style>
""",
    unsafe_allow_html=True,
)

# Initialize Gemini Client securely
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

# ==========================================
# Session State & Refresh Persistence Setup
# ==========================================
if "user_name" not in st.session_state:
  # Restore login state from URL query parameters on page refresh
  if "logged_user" in st.query_params:
    st.session_state.user_name = st.query_params["logged_user"]
  else:
    st.session_state.user_name = None

# Multi-Chat History Setup
if "chats" not in st.session_state:
  st.session_state.chats = [{
      "id": 1,
      "title": "New Conversation",
      "messages": [],
  }]
if "active_chat_id" not in st.session_state:
  st.session_state.active_chat_id = 1

if "student_chat" not in st.session_state:
  st.session_state.student_chat = []
if "saved_images" not in st.session_state:
  st.session_state.saved_images = []
if "notes" not in st.session_state:
  st.session_state.notes = [{
      "id": 0,
      "title": "Welcome Note",
      "content": "Write your detailed notes here!",
  }]
if "active_view" not in st.session_state:
  st.session_state.active_view = "💬 Chat Assistant"


# Helper function to get current chat messages
def get_current_messages():
  for c in st.session_state.chats:
    if c["id"] == st.session_state.active_chat_id:
      return c["messages"]
  return st.session_state.chats[0]["messages"]


# Safe Error-Proof API Runner
def query_gemini_safely(prompt_text, selected_model="gemini-3.6-flash"):
  if not api_key:
    return "⚠️ Gemini API Key missing. Please configure it in Streamlit Secrets."
  try:
    client = genai.Client(api_key=api_key)
    for attempt in range(2):
      try:
        response = client.models.generate_content(
            model=selected_model, contents=prompt_text
        )
        return response.text
      except Exception as inner_e:
        if attempt == 1:
          raise inner_e
        time.sleep(1)
  except Exception as e:
    err_msg = str(e)
    if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
      return (
          f"⚠️ **Rate Limit Exceeded:** Model `{selected_model}` is busy. Please"
          " wait a moment."
      )
    else:
      return f"⚠️ **API Error:** {err_msg}"


# ==========================================
# Authentication Hub (Google Login & Persistent Session)
# ==========================================
if not st.session_state.user_name:
  st.markdown(
      "<div style='max-width: 480px; margin: 50px auto; padding: 30px;"
      " background-color: #ffffff; border: 2px solid #fce8e6; border-radius:"
      " 24px; box-shadow: 0 8px 24px rgba(217,48,37,0.08);'>"
      "<div style='text-align: center; margin-bottom: 25px;'><h2"
      " style='color: #d93025; margin-bottom: 5px; font-weight: 700;'>✨ Gemini"
      " Workspace</h2><p style='color: #5f6368; font-size: 14px;'>Secure"
      " Red & White Portal</p></div>",
      unsafe_allow_html=True,
  )

  col_s1, col_center, col_s2 = st.columns([0.1, 3.8, 0.1])
  with col_center:
    # Google Login Button Simulation (Persistent on Login)
    if st.button("🌐 Sign in with Google", use_container_width=True):
      default_user = "Danyal Jan"
      st.session_state.user_name = default_user
      st.query_params["logged_user"] = default_user
      st.rerun()

    st.markdown(
        "<div style='border-top: 2px solid #fce8e6; margin: 25px 0;"
        " text-align: center;'><span style='background-color: #ffffff; padding:"
        " 0 10px; color: #5f6368; font-weight: 600;'>OR</span></div>",
        unsafe_allow_html=True,
    )

    guest_name_input = st.text_input(
        "Enter your name to start", placeholder="Danyal Jan"
    )
    if st.button("🚀 Enter Workspace", use_container_width=True):
      name_to_use = (
          guest_name_input.strip() if guest_name_input.strip() else "Danyal Jan"
      )
      st.session_state.user_name = name_to_use
      st.query_params["logged_user"] = name_to_use
      st.rerun()

  st.markdown("</div>", unsafe_allow_html=True)
  st.stop()


# ==========================================
# Sidebar Navigation & History Management
# ==========================================
with st.sidebar:
  st.markdown(
      "<h3 style='color: #d93025; font-size: 20px; font-weight: 700;'>✨ Gemini"
      " Workspace</h3>",
      unsafe_allow_html=True,
  )
  st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

  # NEW CHAT BUTTON (Archives current chat and starts a fresh one)
  if st.button("➕ New chat"):
    current_msgs = get_current_messages()
    if current_msgs:
      # Create new chat session ID
      new_id = len(st.session_state.chats) + 1
      snippet = (
          current_msgs[0]["content"][:25] + "..."
          if len(current_msgs[0]["content"]) > 25
          else current_msgs[0]["content"]
      )
      st.session_state.chats.append(
          {"id": new_id, "title": snippet, "messages": []}
      )
      st.session_state.active_chat_id = new_id
    st.session_state.active_view = "💬 Chat Assistant"
    st.rerun()

  st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
  if st.button("🔍 Search chats"):
    st.session_state.active_view = "🔍 Search chats"
    st.rerun()
  if st.button("🎓 Students Workspace"):
    st.session_state.active_view = "🎓 Students"
    st.rerun()
  if st.button("🖼️ Image Generator"):
    st.session_state.active_view = "🎨 Image Generator"
    st.rerun()
  if st.button("📁 Library"):
    st.session_state.active_view = "📁 Library"
    st.rerun()
  if st.button("📓 Notebook"):
    st.session_state.active_view = "📓 Notebook"
    st.rerun()

  st.markdown(
      "<p"
      " style='color:#5f6368;font-size:11px;font-weight:700;letter-spacing:0.5px;margin-top:20px;margin-bottom:5px;'>CHAT"
      " HISTORY</p>",
      unsafe_allow_html=True,
  )
  for chat_session in reversed(st.session_state.chats):
    btn_label = f"💬 {chat_session['title']}"
    if chat_session["id"] == st.session_state.active_chat_id:
      btn_label = f"▶ {btn_label}"
    if st.button(btn_label, key=f"hist_chat_{chat_session['id']}"):
      st.session_state.active_chat_id = chat_session["id"]
      st.session_state.active_view = "💬 Chat Assistant"
      st.rerun()

  st.markdown(
      "<div style='margin-top: 30px; border-top: 1px solid #fce8e6;'></div>",
      unsafe_allow_html=True,
  )
  st.write(f"👤 **{st.session_state.user_name}**")
  if st.button("🚪 Logout"):
    st.session_state.user_name = None
    if "logged_user" in st.query_params:
      del st.query_params["logged_user"]
    st.rerun()


# ==========================================
# MODULE 1: Chat Assistant (Model 3.6-flash & 3.1-flash-lite)
# ==========================================
if st.session_state.active_view == "💬 Chat Assistant":
  col_title, col_model = st.columns([2.2, 1.8])
  with col_title:
    current_msgs = get_current_messages()
    if not current_msgs:
      st.markdown(
          "<h1 style='color: #202124; font-weight: 700; font-size:"
          f" 26px;'>Hello, {st.session_state.user_name}</h1>",
          unsafe_allow_html=True,
      )
      st.markdown(
          "<h2 style='color: #5f6368; font-weight: 500; font-size:"
          " 20px;'>How can I help you today?</h2>",
          unsafe_allow_html=True,
      )
  with col_model:
    selected_model = st.selectbox(
        "🧠 Select Model",
        ["gemini-3.6-flash", "gemini-3.1-flash-lite"],
        help=(
            "Switch between Gemini 3.6 Flash (High Performance) and 3.1 Flash"
            " Lite (Ultra Fast)."
        ),
    )

  # Render current active chat messages
  for message in current_msgs:
    with st.chat_message(
        message["role"], avatar="👤" if message["role"] == "user" else "✨"
    ):
      st.markdown(message["content"])

  uploaded_file = st.file_uploader(
      "Attach file", label_visibility="collapsed"
  )
  if user_query := st.chat_input("Ask Gemini..."):
    prompt_content = []
    if uploaded_file:
      prompt_content.append(f"\n[Attached File: {uploaded_file.name}]\n")
    prompt_content.append(user_query)

    # Append to active chat session
    current_msgs.append({"role": "user", "content": user_query})

    # Update chat title if it's the first message
    for c in st.session_state.chats:
      if c["id"] == st.session_state.active_chat_id and c["title"] == "New Conversation":
        c["title"] = user_query[:25] + ("..." if len(user_query) > 25 else "")

    with st.chat_message("user", avatar="👤"):
      st.markdown(user_query)

    with st.chat_message("assistant", avatar="✨"):
      with st.spinner(f"Thinking with {selected_model}..."):
        reply = query_gemini_safely(
            " ".join(prompt_content), selected_model=selected_model
        )
        st.markdown(reply)
        current_msgs.append({"role": "model", "content": reply})


# ==========================================
# MODULE 2: Search Chats
# ==========================================
elif st.session_state.active_view == "🔍 Search chats":
  st.title("🔍 Search Your Chats")
  st.markdown(
      "<p style='color: #5f6368;'>Quickly find content across all your chat"
      " history.</p><hr>",
      unsafe_allow_html=True,
  )

  search_q = st.text_input("Enter keywords...")
  if search_q:
    all_matched = []
    for chat_sess in st.session_state.chats:
      for m in chat_sess["messages"]:
        if search_q.lower() in m["content"].lower():
          all_matched.append((chat_sess["title"], m))

    if all_matched:
      st.success(f"Found {len(all_matched)} matching messages.")
      for chat_title, r in all_matched:
        st.caption(f"📁 Chat: {chat_title}")
        with st.chat_message(
            r["role"], avatar="👤" if r["role"] == "user" else "✨"
        ):
          st.markdown(r["content"])
    else:
      st.warning("No matches found.")


# ==========================================
# MODULE 3: Students Workspace (Fully Restored)
# ==========================================
elif st.session_state.active_view == "🎓 Students":
  st.title("🎓 Student Workspace")
  st.markdown(
      "<p style='color: #5f6368;'>Supercharge your learning with detailed AI"
      " study tools and interactive quizzes.</p>",
      unsafe_allow_html=True,
  )
  tab_learn, tab_quiz = st.tabs(["📖 Socratic Tutor", "📝 Quiz Generator"])

  with tab_learn:
    st.subheader("AI Detailed Study Guide & Socratic Tutor")
    for m in st.session_state.student_chat:
      with st.chat_message(
          m["role"], avatar="👤" if m["role"] == "user" else "✨"
      ):
        st.markdown(m["content"])
    if s_q := st.chat_input("Ask a study question...", key="stu_in"):
      st.session_state.student_chat.append({"role": "user", "content": s_q})
      with st.chat_message("assistant", avatar="✨"):
        s_reply = query_gemini_safely(
            f"Act as a detailed Socratic tutor answering: {s_q}",
            selected_model="gemini-3.6-flash",
        )
        st.markdown(s_reply)
        st.session_state.student_chat.append(
            {"role": "model", "content": s_reply}
        )

  with tab_quiz:
    st.subheader("Interactive Practice Quiz Generator")
    q_topic = st.text_input(
        "Enter subject topic (e.g., Physics, Python Programming):"
    )
    if st.button("Generate Detailed Quiz"):
      if q_topic:
        with st.spinner("Generating custom quiz..."):
          quiz_res = query_gemini_safely(
              f"Create a detailed 3-question multiple-choice quiz with correct answers and explanations about {q_topic}.",
              selected_model="gemini-3.6-flash",
          )
          st.markdown(quiz_res)


# ==========================================
# MODULE 4: Image Generator Studio (Fully Restored)
# ==========================================
elif st.session_state.active_view == "🎨 Image Generator":
  st.title("🎨 Image Generation Studio")
  st.markdown(
      "<p style='color: #5f6368;'>Generate and preview professional artwork"
      " concepts using Gemini.</p><hr>",
      unsafe_allow_html=True,
  )

  img_prompt = st.text_area(
      "Describe your image concept:",
      value="Cinematic futuristic sports car driving through neon Tokyo at night",
      height=100,
  )
  aspect_ratio = st.selectbox(
      "Aspect Ratio", ["1:1 (Square)", "16:9 (Landscape)", "9:16 (Portrait)"]
  )
  gen_img_btn = st.button("✨ Generate Artwork")

  if gen_img_btn:
    with st.spinner("Generating creative visual blueprint..."):
      img_blueprint = query_gemini_safely(
          f"Act as an expert AI prompt engineer. Create an extremely detailed visual art prompt, color palette, lighting details, and composition breakdown for: {img_prompt}",
          selected_model="gemini-3.6-flash",
      )
      st.markdown("### 🖼️ Generated Prompt & Design Blueprint")
      st.markdown(img_blueprint)
      st.success("Visual concept generated successfully!")


# ==========================================
# MODULE 5: Library & Notebooks
# ==========================================
elif st.session_state.active_view == "📁 Library":
  st.title("📁 Media Library")
  st.markdown(
      "<p style='color: #5f6368;'>Your saved generations and assets.</p><hr>",
      unsafe_allow_html=True,
  )
  st.info("No saved assets in your library yet.")


elif st.session_state.active_view == "📓 Notebook":
  st.title("📓 Private Detailed Notes")
  st.markdown("<hr>", unsafe_allow_html=True)
  c1, c2 = st.columns([1, 2])
  with c1:
    if st.button("➕ New Note"):
      st.session_state.notes.append({
          "id": len(st.session_state.notes),
          "title": "New Detailed Note",
          "content": "",
      })
    for idx, n in enumerate(st.session_state.notes):
      if st.button(f"📄 {n['title']}", key=f"note_{idx}"):
        st.session_state.curr_note = idx
  with c2:
    curr = st.session_state.get("curr_note", 0)
    if curr < len(st.session_state.notes):
      note = st.session_state.notes[curr]
      ntitle = st.text_input("Title", value=note["title"])
      ncontent = st.text_area(
          "Detailed Content", value=note["content"], height=350
      )
      if st.button("💾 Save Note"):
        st.session_state.notes[curr]["title"] = ntitle
        st.session_state.notes[curr]["content"] = ncontent
        st.success("Note saved successfully!")
