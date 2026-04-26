import streamlit as st
import os
import tempfile
from pathlib import Path
from transcribe import transcribe_video
from dotenv import load_dotenv

# Load environment variables (for GOOGLE_API_KEY)
load_dotenv()

# --- Page Config ---
st.set_page_config(
    page_title="Marathi Transcriber",
    page_icon="🎙️",
    layout="centered"
)

# --- Custom CSS for Premium Look ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #ff4b4b;
        color: white;
        font-weight: bold;
    }
    .stTextArea>div>div>textarea {
        color: #1f1f1f !important;
        background-color: #ffffff !important;
        border-radius: 10px;
        border: 2px solid #ff4b4b;
        font-size: 1.1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Header ---
st.title("🎙️ Marathi Video Transcriber")
st.info("Upload your screen recording, and I'll extract the Marathi audio and transcribe it using Gemini.")

# --- File Uploader ---
uploaded_file = st.file_uploader("Upload Screen Recording", type=["mp4", "mkv", "avi", "mov", "webm"])

if uploaded_file is not None:
    # Show video preview
    st.video(uploaded_file)
    
    if st.button("🚀 Start Transcription"):
        try:
            # Create a temporary file to save the uploaded video
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                tmp_file.write(uploaded_file.read())
                video_path = tmp_file.name

            with st.status("⏳ Processing...", expanded=True) as status:
                st.write("🎬 Extracting audio from video...")
                # Note: We use transcribe_video from your existing script
                transcript = transcribe_video(video_path, language="Marathi")
                status.update(label="✅ Transcription Complete!", state="complete", expanded=False)

            # --- Display Result ---
            st.subheader("📝 Marathi Transcript")
            
            # The "Big Box" you wanted (Text Area)
            st.text_area(
                label="Transcript Area",
                value=transcript,
                height=400,
                key="transcript_box",
                label_visibility="collapsed"
            )

            # Custom Direct Copy Button (JavaScript)
            st.components.v1.html(f"""
                <button id="copyBtn" style="
                    width: 100%;
                    padding: 10px;
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    font-weight: bold;
                    font-family: sans-serif;
                ">📋 Copy to Clipboard</button>
                <script>
                    document.getElementById('copyBtn').onclick = function() {{
                        const text = `{transcript.replace('`', '\\`').replace('$', '\\$')}`;
                        navigator.clipboard.writeText(text).then(() => {{
                            this.innerText = '✅ Copied!';
                            this.style.backgroundColor = '#45a049';
                            setTimeout(() => {{
                                this.innerText = '📋 Copy to Clipboard';
                                this.style.backgroundColor = '#4CAF50';
                            }}, 2000);
                        }});
                    }};
                </script>
            """, height=50)
            
            st.write("") # Spacer
            
            # Download button
            st.download_button(
                label="💾 Download as .txt",
                data=transcript,
                file_name=f"{Path(uploaded_file.name).stem}_transcript.txt",
                mime="text/plain"
            )

            # Cleanup the temporary video file
            if os.path.exists(video_path):
                os.remove(video_path)

        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            if "GOOGLE_API_KEY" not in os.environ:
                st.warning("Please make sure your GOOGLE_API_KEY is set in the .env file.")

else:
    st.write("---")
    st.caption("Supported formats: MP4, MKV, AVI, MOV, WEBM")
    st.caption("Powered by Gemini 3.1 & MoviePy")
