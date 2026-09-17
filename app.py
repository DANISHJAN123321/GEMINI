import os
import time
from google import genai
from google.genai import types
import streamlit as st

# ==========================================
# Page Configuration & Exact Gemini UI Theme
# ==========================================
st.set_page_config(
    page_title="Gemini",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&display=swap');

    .stApp { 
        background-color: #131314; 
        color: #e3e3e3; 
        font-family: 'Google Sans', sans-serif;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #1e1f20;
        border-right: 1px solid #282a2c;
        padding-top: 5px;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* FIX: Chat Input Box Visibility & Double Text Bug */
    .stChatInput {
        background-color: #1e1f20 !important;
        border: 1px solid #444746 !important;
        border-radius: 28px !important;
        padding: 4px !important;
    }
    .stChatInput textarea {
        background-color: transparent !important;
        color: #ffffff !important;
        font-family: 'Google Sans', sans-serif !important;
        font-size: 15px !important;
    }
    .stChatInput textarea::placeholder {
        color: #8e918f !important;
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

    /* Clean Chat Message Bubbles */
    div[data-testid="stChatMessage"] {
        background-color: transparent !important;
        padding: 12px 0 !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.03);
    }
    div[data-testid="stChatMessage"] p, div[data-testid="stChatMessage"] span, div[data-testid="stChatMessage"] li {
        color: #e3e3e3 !important;
        font-family: 'Google Sans', sans-serif !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Initialize Gemini Client securely via Streamlit Secrets
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

# ==========================================
# Session State Initialization
# ==========================================
if "chat_messages" not in st.session_state:
  st.session_state.chat_messages = []
if "active_view" not in st.session_state:
  st.session_state.active_view = "💬 Chat Assistant"

# ==========================================
# Sidebar Navigation
# ==========================================
with st.sidebar:
  col_logo, col_opt = st.columns([4, 1])
  with col_logo:
    st.markdown(
        "<h3 style='color: #e3e3e3; font-size: 18px; margin: 0; font-family:"
        " \"Google Sans\";'>✨ Gemini</h3>",
        unsafe_allow_html=True,
    )
  with col_opt:
    st.markdown(
        "<div style='border: 1px solid #444746; border-radius: 6px; padding:"
        " 2px 6px; text-align: center; cursor: pointer; color: #c4c7c5; font-size:"
        " 12px;'>🗂️</div>",
        unsafe_allow_html=True,
    )

  st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

  if st.button("➕ New chat", key="nav_new"):
    st.session_state.chat_messages = []
    st.session_state.active_view = "💬 Chat Assistant"
    st.rerun()

  if st.button("🔍 Search chats", key="nav_search"):
    st.session_state.active_view = "🔍 Search chats"
    st.rerun()

  if st.button("🎓 Students", key="nav_students"):
    st.session_state.active_view = "🎓 Students"
    st.rerun()

  if st.button("🖼️ Images", key="nav_images"):
    st.session_state.active_view = "🎨 Image Generator"
    st.rerun()

  if st.button("📁 Library", key="nav_library"):
    st.session_state.active_view = "📁 Library"
    st.rerun()

  st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
  st.markdown(
      "<p"
      " style='color:#8e918f;font-size:11px;font-weight:700;letter-spacing:0.5px;margin-bottom:6px;'>NOTEBOOKS</p>",
      unsafe_allow_html=True,
  )

  if st.button("➕ New notebook", key="nav_new_nb"):
    pass
  if st.button("📓 d", key="nb_1"):
    pass
  if st.button("📓 Untitled notebook", key="nb_2"):
    pass

  st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
  st.markdown(
      "<p"
      " style='color:#8e918f;font-size:11px;font-weight:700;letter-spacing:0.5px;margin-bottom:6px;'>RECENTS</p>",
      unsafe_allow_html=True,
  )
  st.markdown(
      "<p style='color:#c4c7c5; font-size: 13px; padding: 2px 0; cursor:"
      " pointer;'>🔥 Building a Free Fire Panel</p>",
      unsafe_allow_html=True,
  )
  st.markdown(
      "<p style='color:#c4c7c5; font-size: 13px; padding: 2px 0; cursor:"
      " pointer;'>🚀 15-Day Software Development Roadmap</p>",
      unsafe_allow_html=True,
  )

  st.markdown("<div style='margin-top: 60px;'></div>", unsafe_allow_html=True)
  st.markdown("---")

  col_user_img, col_user_name, col_user_set = st.columns([1, 3, 1])
  with col_user_img:
    st.markdown("👤")
  with col_user_name:
    st.markdown(
        "<p style='color: #e3e3e3; font-size: 13px; font-weight: 500; margin:"
        " 0;'>Danyal Jan</p>",
        unsafe_allow_html=True,
    )
  with col_user_set:
    st.markdown("⚙️")


# Helper function to handle transient API errors automatically
def call_gemini_with_retry(api_call_func, max_retries=3):
  for attempt in range(max_retries):
    try:
      return api_call_func()
    except Exception as e:
      err_str = str(e)
      if (
          "503" in err_str
          or "UNAVAILABLE" in err_str
          or "429" in err_str
          or "RESOURCE_EXHAUSTED" in err_str
      ) and attempt < max_retries - 1:
        time.sleep(2 * (attempt + 1))
        continue
      else:
        raise e


# ==========================================
# MODULE 1: Chat Assistant View
# ==========================================
if st.session_state.active_view == "💬 Chat Assistant":
  if not st.session_state.chat_messages:
    st.markdown(
        "<h2 style='color: #c4c7c5; font-weight: 400; margin-top: 20px;"
        " margin-bottom: 0px;'>Hello, Danyal</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<h1 style='color: #e3e3e3; font-weight: 500; margin-top: 0px;"
        " margin-bottom: 20px;'>How can I help you today?</h1>",
        unsafe_allow_html=True,
    )
  else:
    for message in st.session_state.chat_messages:
      with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "file_name" in message and message["file_name"]:
          st.caption(f"📎 Attached file: {message['file_name']}")

  # Compact File/Image Upload Expander
  with st.expander("📁 Attach Image, Document, or File"):
    uploaded_file = st.file_uploader(
        "Choose a file to attach",
        type=["png", "jpg", "jpeg", "txt", "pdf", "py", "csv", "json", "zip"],
        label_visibility="collapsed",
    )

  if user_query := st.chat_input("Ask Gemini..."):
    if not api_key:
      st.error("API Key not found in Streamlit Secrets!")
    else:
      file_content_parts = []
      file_name_display = None

      if uploaded_file is not None:
        file_name_display = uploaded_file.name
        file_bytes = uploaded_file.getvalue()
        if uploaded_file.type.startswith("image/"):
          file_content_parts.append(
              types.Part.from_bytes(data=file_bytes, mime_type=uploaded_file.type)
          )
        else:
          try:
            text_data = file_bytes.decode("utf-8")
            file_content_parts.append(
                f"\n[Attached File Content from {file_name_display}]:\n{text_data}\n"
            )
          except Exception:
            file_content_parts.append(
                f"\n[Attached Binary File: {file_name_display}]\n"
            )

      file_content_parts.append(user_query)

      st.session_state.chat_messages.append({
          "role": "user",
          "content": user_query,
          "file_name": file_name_display,
      })
      with st.chat_message("user"):
        st.markdown(user_query)
        if file_name_display:
          st.caption(f"📎 Attached file: {file_name_display}")

      with st.chat_message("assistant"):
        with st.spinner("Gemini is thinking..."):
          try:
            client = genai.Client(api_key=api_key)
            formatted_history = [
                {"role": m["role"], "parts": [{"text": m["content"]}]}
                for m in st.session_state.chat_messages[:-1]
            ]

            def send_chat():
              chat = client.chats.create(
                  model="gemini-3.6-flash", history=formatted_history
              )
              return chat.send_message(file_content_parts)

            response = call_gemini_with_retry(send_chat)
            ai_reply = response.text

            st.markdown(ai_reply)
            st.session_state.chat_messages.append(
                {"role": "model", "content": ai_reply}
            )
          except Exception as e:
            st.error(f"Chat Error: {e}")

  st.markdown(
      "<p style='text-align: center; color: #8e918f; font-size: 11px; margin-top:"
      " 15px;'>Gemini is AI and can make mistakes.</p>",
      unsafe_allow_html=True,
  )


# ==========================================
# MODULE 2: Image Generator View
# ==========================================
elif st.session_state.active_view == "🎨 Image Generator":
  st.title("🎨 Image Generation Studio")
  st.markdown(
      "<p style='color: #8e918f;'>Create professional visual artwork using"
      " Gemini models.</p>",
      unsafe_allow_html=True,
  )
  st.markdown("---")

  col1, col2 = st.columns([1, 1.2])

  with col1:
    image_prompt = st.text_area(
        "Enter image description:",
        value=(
            "Cinematic neon-lit cyberpunk sports car driving through Tokyo"
            " streets at night"
        ),
        height=120,
    )
    aspect_ratio = st.selectbox(
        "Aspect Ratio", ["1:1 (Square)", "16:9 (Landscape)", "9:16 (Portrait)"]
    )
    gen_image_btn = st.button("✨ Generate Image")

  with col2:
    st.markdown("#### 🖼️ Output Preview")
    if gen_image_btn:
      if not api_key:
        st.error("API Key missing in Streamlit Secrets!")
      else:
        with st.spinner("Generating artwork..."):
          try:
            client = genai.Client(api_key=api_key)
            ratio_code = aspect_ratio.split(" ")[0]

            def generate_img():
              return client.models.generate_content(
                  model="gemini-3.6-flash",
                  contents=image_prompt,
                  config=types.GenerateContentConfig(
                      response_modalities=["IMAGE", "TEXT"]
                  ),
              )

            response = call_gemini_with_retry(generate_img)

            image_found = False
            if response and response.candidates:
              for candidate in response.candidates:
                if candidate.content and candidate.content.parts:
                  for part in candidate.content.parts:
                    if getattr(part, "inline_data", None) and part.inline_data:
                      img_bytes = part.inline_data.data
                      st.image(
                          img_bytes,
                          caption=f"Generated Image ({ratio_code})",
                          use_container_width=True,
                      )
                      st.download_button(
                          label="📥 Download Image",
                          data=img_bytes,
                          file_name="gemini_image.jpg",
                          mime="image/jpeg",
                      )
                      image_found = True

            if not image_found:
              if response and response.text:
                st.info(f"Model text response: {response.text}")
              else:
                st.warning(
                    "No image data returned. Try a more descriptive prompt."
                )
          except Exception as e:
            st.error(f"Generation Error: {e}")
    else:
      st.info("👉 Configure your description and click **'Generate Image'**.")


# ==========================================
# MODULE 3: Other Views
# ==========================================
else:
  st.title(f"📁 {st.session_state.active_view}")
  st.markdown(
      "<p style='color: #8e918f;'>Workspace module loaded successfully.</p>",
      unsafe_allow_html=True,
  )
  st.markdown("---")
  st.info(
      "Use the sidebar to return to the **💬 Chat Assistant** or **🎨 Image"
      " Generator**."
  )
