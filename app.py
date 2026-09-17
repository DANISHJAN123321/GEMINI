import os
import time
from google import genai
from google.genai import types
import streamlit as st

# ==========================================
# Page Configuration & Styling
# ==========================================
st.set_page_config(
    page_title="Gemini Ultimate Studio", page_icon="⚡", layout="wide"
)

st.markdown(
    """
    <style>
    .stApp { background-color: #0b0f19; color: #f3f4f6; }
    .sidebar .stSidebar { background-color: #111827; }
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        color: white; border: none; border-radius: 10px; font-weight: bold;
        padding: 0.6rem; width: 100%;
    }
    .stTextArea textarea, .stTextInput input { background-color: #1e293b; color: #f3f4f6; }
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
# Sidebar Navigation & Setup
# ==========================================
with st.sidebar:
  st.markdown("### ⚡ Gemini Ultimate Studio")
  app_mode = st.radio(
      "Choose Module:",
      [
          "💬 AI Chat Assistant",
          "🎨 Direct API Image Generator",
          "✍️ Prompt & Copywriting Studio",
      ],
  )
  st.markdown("---")
  st.markdown("**API Engine:** Official `google-genai` SDK")
  st.markdown("**Model Tier:** Free Tier Enabled")


# ==========================================
# MODULE 1: AI Chat Assistant
# ==========================================
if app_mode == "💬 AI Chat Assistant":
  st.title("💬 Gemini Conversational Assistant")
  st.markdown(
      "Chat live with the official Gemini API using conversational history."
  )
  st.markdown("---")

  # Display past messages
  for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
      st.markdown(message["content"])

  # User chat input
  if user_query := st.chat_input("Ask Gemini anything..."):
    if not api_key:
      st.error("API Key not found in Streamlit Secrets!")
    else:
      # Append and display user message
      st.session_state.chat_messages.append(
          {"role": "user", "content": user_query}
      )
      with st.chat_message("user"):
        st.markdown(user_query)

      # Generate AI response
      with st.chat_message("assistant"):
        with st.spinner("Gemini is thinking..."):
          try:
            client = genai.Client(api_key=api_key)
            # Format chat history for the official API structure
            formatted_history = [
                {"role": m["role"], "parts": [{"text": m["content"]}]}
                for m in st.session_state.chat_messages[:-1]
            ]
            chat = client.chats.create(
                model="gemini-2.5-flash", history=formatted_history
            )
            response = chat.send_message(user_query)
            ai_reply = response.text

            st.markdown(ai_reply)
            st.session_state.chat_messages.append(
                {"role": "model", "content": ai_reply}
            )
          except Exception as e:
            st.error(f"Chat Error: {e}")


# ==========================================
# MODULE 2: Direct API Image Generator
# ==========================================
elif app_mode == "🎨 Direct API Image Generator":
  st.title("🎨 Official Gemini API Image Studio")
  st.markdown(
      "Generate images directly through the native Gemini API free tier"
      " endpoint."
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
    gen_image_btn = st.button("✨ Generate Image via API")

  with col2:
    st.markdown("#### 🖼️ Output Preview")
    if gen_image_btn:
      if not api_key:
        st.error("API Key missing in Streamlit Secrets!")
      else:
        with st.spinner(
            "Calling official Gemini API image generation endpoint..."
        ):
          try:
            client = genai.Client(api_key=api_key)
            ratio_code = aspect_ratio.split(" ")[0]

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=image_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"]
                ),
            )

            image_found = False
            if response and response.candidates:
              for candidate in response.candidates:
                if candidate.content and candidate.content.parts:
                  for part in candidate.content.parts:
                    if getattr(part, "inline_data", None) and part.inline_data:
                      img_bytes = part.inline_data.data
                      st.image(
                          img_bytes,
                          caption=f"Generated via Gemini API ({ratio_code})",
                          use_container_width=True,
                      )
                      st.download_button(
                          label="📥 Download Generated Image",
                          data=img_bytes,
                          file_name="gemini_api_image.jpg",
                          mime="image/jpeg",
                      )
                      image_found = True
                      st.session_state.image_history.append(img_bytes)

            if not image_found:
              if response and response.text:
                st.info(f"Model text response: {response.text}")
              else:
                st.warning(
                    "No image data returned. Try a more detailed description."
                )
          except Exception as e:
            st.error(
                f"Generation Error: {e}. If quota is reached, check your free"
                " tier token limits."
            )
    else:
      st.info(
          "👉 Configure your description on the left and click **'Generate Image"
          " via API'**."
      )


# ==========================================
# MODULE 3: Prompt & Copywriting Studio
# ==========================================
elif app_mode == "✍️ Prompt & Copywriting Studio":
  st.title("✍️ Professional Content & Prompt Studio")
  st.markdown(
      "Leverage Gemini text intelligence to craft high-conversion copywriting"
      " and image prompts."
  )
  st.markdown("---")

  col_a, col_b = st.columns([1, 1.3])

  with col_a:
    tool_type = st.selectbox(
        "Select Writing Tool:",
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

          # Define specific instructions based on selection
          if tool_type == "AI Image Prompt Engineer":
            instruction = (
                "Act as an expert AI prompt engineer. Expand this concept into a"
                " rich, detailed visual art prompt focusing on lighting and"
                " style. Return only the prompt text."
            )
          elif tool_type == "Marketing Copywriter (AIDA)":
            instruction = (
                "Act as a professional direct-response copywriter. Write a"
                " marketing pitch using the AIDA framework (Attention, Interest,"
                " Desire, Action)."
            )
          elif tool_type == "Blog Post Structure":
            instruction = (
                "Act as a content strategist. Outline a comprehensive blog"
                " post including H2 headings and key breakdown points."
            )
          else:
            instruction = (
                "Act as an email marketer. Generate 5 high-open-rate subject"
                " lines for this topic."
            )

          response = client.models.generate_content(
              model="gemini-2.5-flash",
              contents=raw_input,
              config=types.GenerateContentConfig(
                  system_instruction=instruction, temperature=0.7
              ),
          )
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
