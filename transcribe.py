"""
Marathi Audio Transcription Pipeline
=====================================
Flow: Screen recording (video) ──► MoviePy ──► audio (WAV)
                                               │
                                               ▼
                               Gemini (via LangChain) ──► Marathi transcript
"""

import os
import sys
import tempfile
import argparse
from pathlib import Path

# ── 1. Extract audio from video using MoviePy ────────────────────────────────
def extract_audio(video_path: str, output_audio_path: str | None = None) -> str:
    """
    Extract audio track from a video file and save as WAV.

    Args:
        video_path: Path to the input video file.
        output_audio_path: Where to save the extracted audio.
                           If None, a temp file is created.

    Returns:
        Path to the saved WAV file.
    """
    try:
        from moviepy import VideoFileClip  # moviepy v2.x
    except ImportError:
        from moviepy.editor import VideoFileClip  # moviepy v1.x fallback

    video_path = str(Path(video_path).resolve())
    if not Path(video_path).exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    if output_audio_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        output_audio_path = tmp.name
        tmp.close()

    print(f"[1/3] Extracting audio from: {video_path}")
    clip = VideoFileClip(video_path)
    if clip.audio is None:
        raise ValueError("The video file has no audio track.")

    clip.audio.write_audiofile(
        output_audio_path,
        fps=16000,        # 16 kHz — good for speech recognition
        nbytes=2,         # 16-bit PCM
        codec="pcm_s16le",
        logger=None,      # suppress verbose ffmpeg logs
    )
    clip.close()
    print(f"[1/3] Audio saved to: {output_audio_path}")
    return output_audio_path


# ── 2. Transcribe audio with Gemini via LangChain ────────────────────────────
def transcribe_audio(audio_path: str, language: str = "Marathi") -> str:
    """
    Send an audio file to Gemini and get back a transcript.

    Uses LangChain's ChatGoogleGenerativeAI with inline audio bytes
    (Gemini natively handles audio as multimodal input).

    Args:
        audio_path: Path to the WAV/MP3/etc. audio file.
        language: Language hint for the model.

    Returns:
        Transcription text.
    """
    import base64
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GOOGLE_API_KEY is not set.\n"
            "  Windows PowerShell: $env:GOOGLE_API_KEY = 'your-key'\n"
            "  Or add it to a .env file (see README)."
        )

    # Read audio bytes and base64-encode for inline multimodal payload
    audio_path = str(Path(audio_path).resolve())
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    # Determine MIME type from extension
    ext = Path(audio_path).suffix.lower()
    mime_map = {
        ".wav": "audio/wav",
        ".mp3": "audio/mp3",
        ".m4a": "audio/mp4",
        ".ogg": "audio/ogg",
        ".flac": "audio/flac",
        ".aac": "audio/aac",
    }
    mime_type = mime_map.get(ext, "audio/wav")

    print(f"[2/3] Sending audio to Gemini for {language} transcription ...")

    llm = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",   # supports audio natively
        google_api_key=api_key,
        temperature=0,               # deterministic for transcription
    )

    # Multimodal message: inline audio + instruction text
    message = HumanMessage(
        content=[
            {
                "type": "media",
                "data": audio_b64,
                "mime_type": mime_type,
            },
            {
                "type": "text",
                "text": (
                    f"Please transcribe the following audio accurately. "
                    f"The audio is in {language}. "
                    f"Return ONLY the verbatim transcript with no additional commentary."
                ),
            },
        ]
    )

    response = llm.invoke([message])
    content = response.content
    
    # Handle list-type content (multimodal responses often return a list of parts)
    if isinstance(content, list):
        transcript = "".join([part if isinstance(part, str) else part.get("text", "") for part in content]).strip()
    else:
        transcript = content.strip()
        
    return transcript


# ── 3. End-to-end pipeline ────────────────────────────────────────────────────
def transcribe_video(video_path: str, keep_audio: bool = False, language: str = "Marathi") -> str:
    """
    Full pipeline: video file → extracted audio → Gemini transcript.

    Args:
        video_path: Path to the screen recording.
        keep_audio: If True, the intermediate WAV file is kept on disk.
        language: Language of the audio content.

    Returns:
        Transcript string.
    """
    audio_path = None
    try:
        # Step 1 — Extract audio
        audio_path = extract_audio(video_path)

        # Step 2 — Transcribe
        transcript = transcribe_audio(audio_path, language=language)

        print("[3/3] Transcription complete.\n")
        return transcript

    finally:
        # Clean up temp audio file unless user wants to keep it
        if audio_path and not keep_audio and Path(audio_path).exists():
            Path(audio_path).unlink()
            print(f"[cleanup] Removed temp audio: {audio_path}")


# ── CLI entry-point ───────────────────────────────────────────────────────────
def main():
    # --- QUICK START: ADD YOUR VIDEO PATH HERE ---
    # If you don't want to use the command line, paste your path below:
    # Example: VIDEO_PATH = r"C:\Users\name\Desktop\recording.mp4"
    VIDEO_PATH = r"C:\Users\sujal\Videos\recording_mm.mp4"
    OUTPUT_FILE = "transcript.txt" # Change this to your desired filename
    # ---------------------------------------------

    parser = argparse.ArgumentParser(
        description="Transcribe Marathi audio from a screen recording using Gemini."
    )
    parser.add_argument("video", nargs='?', default=VIDEO_PATH, help="Path to the screen recording")
    parser.add_argument("--language", default="Marathi", help="Language of the audio")
    parser.add_argument("--keep-audio", action="store_true", help="Keep the intermediate WAV file")
    parser.add_argument("--output", "-o", default=OUTPUT_FILE, help="Save transcript to this file")
    
    args = parser.parse_args()

    if not args.video:
        print("❌ Error: No video path provided.")
        print("Please either:")
        print("1. Add it to the VIDEO_PATH variable in this script.")
        print("2. Run via terminal: python transcribe.py 'path/to/video.mp4'")
        return

    transcript = transcribe_video(
        video_path=args.video,
        keep_audio=args.keep_audio,
        language=args.language,
    )

    if args.output:
        Path(args.output).write_text(transcript, encoding="utf-8")
        print(f"Transcript saved to: {args.output}")
    else:
        print("\n" + "=" * 60)
        print("MARATHI TRANSCRIPT")
        print("=" * 60)
        print(transcript)
        print("=" * 60)


if __name__ == "__main__":
    main()
