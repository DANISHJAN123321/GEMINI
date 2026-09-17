import os
import time
from google import genai
from google.genai import types
import streamlit as st

# ==========================================
# Page Configuration & Gemini.com Theme Styling
# ==========================================
st.set_page_config(
    page_title="Gemini",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { 
        background-color: #131314; 
        color: #e3e3e3; 
        font-family: 'Google Sans', sans-serif;
    }
    section[data-testid="stSidebar"] {
        background-color: #1e1f20;
        border-right: 1px solid #282a2c;
    }
    .stTextInput input, .stTextArea textarea {
        background-color: #1e1f20 !important;
        color: #ffffff !important;
        border: 1px solid #444746 !important;
        border-radius: 12px !important;
        padding: 10px 14px !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #a8c7fa !important;
        box-shadow: 0 0 0 1px #a8c7fa !important;
    }
    div.stButton > button:first-child {
        background: #a8c7fa;
        color: #001d35; 
        border: none; 
        border-radius: 24px; 
        font-weight: 500;
        padding: 0.6rem 1.2rem; 
        width: 100%;
        transition: background 0.2s;
    }
    div.stButton > button:first-child:hover {
        background: #d3e3fd;
    }
    .stRadio label, .stSelectbox label {
        color: #c4c7c5 !important;
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
if "image_history" not in st.session_state:
  st.session_state.image_history = []
if "studio_output" not in st.session_state:
  st.session_state.studio_output = ""

# ==========================================
# Sidebar Navigation
# ==========================================
with st.sidebar:
  st.markdown("### ✨ Gemini Studio")
  app_mode = st.radio(
      "Navigation",
      [
          "💬 Chat Assistant",
          "🎨 Image Generator",
          "✍️ Prompt & Copywriting Studio",
      ],
      label_visibility="collapsed",
  )
  st.markdown("---")
  st.markdown(
      "<p style='color: #8e918f; font-size: 12px;'>Powered by Gemini 3.6"
      " Flash</p>",
      unsafe_allow_html=True,
  )


# Helper function to handle transient errors (503 / 429) automatically
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
        time.sleep(2 * (attempt + 1))  # Exponential backoff delay
        continue
      else:
        raise e


# ==========================================
# MODULE 1: AI Chat Assistant
# ==========================================
if app_mode == "💬 Chat Assistant":
  st.title("Hello, User")
  st.markdown(
      "<p style='color: #8e918f;'>How can I help you today?</p>",
      unsafe_allow_html=True,
  )
  st.markdown("---")

  for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
      st.markdown(message["content"])

  if user_query := st.chat_input("Ask Gemini..."):
    if not api_key:
      st.error("API Key not found in Streamlit Secrets!")
    else:
      st.session_state.chat_messages.append(
          {"role": "user", "content": user_query}
      )
      with st.chat_message("user"):
        st.markdown(user_query)

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
              return chat.send_message(user_query)

            response = call_gemini_with_retry(send_chat)
            ai_reply = response.text

            st.markdown(ai_reply)
            st.session_state.chat_messages.append(
                {"role": "model", "content": ai_reply}
            )
          except Exception as e:
            st.error(
                f"Chat Error: {e}. The server is busy, please try sending"
                " again."
            )


# ==========================================
# MODULE 2: Direct API Image Generator
# ==========================================
elif app_mode == "🎨 Image Generator":
  st.title("🎨 Image Generation Studio")
  st.markdown(
      "<p style='color: #8e918f;'>Create visual artwork using official Gemini"
      " models.</p>",
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
        with st.spinner("Generating artwork (auto-retrying if busy)..."):
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
                      st.session_state.image_history.append(img_bytes)

            if not image_found:
              if response and response.text:
                st.info(f"Model text response: {response.text}")
              else:
                st.warning(
                    "No image data returned. Try a more descriptive prompt."
                )
          except Exception as e:
            st.error(
                f"Generation Error: {e}. Servers are busy, please click generate"
                " again."
            )
    else:
      st.info(
          "👉 Configure your description on the left and click **'Generate"
          " Image'**."
      )


# ==========================================
# MODULE 3: Prompt & Copywriting Studio
# ==========================================
elif app_mode == "✍️ Prompt & Copywriting Studio":
  st.title("✍️ Prompt & Content Studio")
  st.markdown(
      "<p style='color: #8e918f;'>Build professional prompts and copy with AI"
      " intelligence.</p>",
      unsafe_allow_html=True,
  )
  st.markdown("---")

  col_a, col_b = st.columns([1, 1.3])

  with col_a:
    tool_type = st.selectbox(
        "Select Tool:",
        [
            "AI Image Prompt Engineer",
            "Marketing Copywriter (AIDA)",
            "Blog Post Structure",
            "Catchy Email Subject Lines",
        ],
    )
    raw_input = st.text_area(
        "Enter your topic or base concept:",
        placeholder="E.g., A new fitness app launch...",
        height=130,
    )
    craft_btn = st.button("🔮 Craft Content")

  with col_b:
    st.markdown("#### 📄 Workspace Output")
    if craft_btn and raw_input:
      with st.spinner("Crafting content..."):
        try:
          client = genai.Client(api_key=api_key)

          if tool_type == "AI Image Prompt Engineer":
            instruction = (
                "Act as an expert AI prompt engineer. Expand this concept into a"
                " rich, detailed visual art prompt focusing on lighting and"
                " style. Return only the prompt text."
            )
          elif tool_type == "Marketing Copywriter (AIDA)":
            instruction = (
                "Act as a professional direct-response copywriter. Write a"
                " marketing pitch using the AIDA framework."
            )
          elif tool_type == "Blog Post Structure":
            instruction = (
                "Act as a content strategist. Outline a comprehensive blog"
                " post including H2 headings."
            )
          else:
            instruction = (
                "Act as an email marketer. Generate 5 high-open-rate subject"
                " lines for this topic."
            )

          def generate_text():
            return client.models.generate_content(
                model="gemini-3.6-flash",
                contents=raw_input,
                config=types.GenerateContentConfig(
                    system_instruction=instruction
                ),
            )

          response = call_gemini_with_retry(generate_text)
          st.session_state.studio_output = response.text.strip()
        except Exception as e:
          st.error(f"Studio Error: {e}")

    st.text_area(
        "Result:",
        value=st.session_state.studio_output,
        height=280,
        key="studio_display",
    )

    if st.session_state.studio_output:
      st.download_button(
          label="💾 Download Text File",
          data=st.session_state.studio_output,
          file_name="gemini_studio_output.txt",
          mime="text/plain",
      )
