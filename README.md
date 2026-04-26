# Marathi Screen Recording Transcriber

Transcribe Marathi audio from any screen recording using **MoviePy** (audio extraction) and **Google Gemini** (via LangChain).

## Pipeline

```
Screen recording (MP4/MKV/AVI…)
        │
        ▼  MoviePy
  Audio WAV (16 kHz, PCM)
        │
        ▼  LangChain + Gemini
  Marathi transcript (text)
```

## Setup

### 1. Install dependencies

```powershell
pip install -r requirements.txt
```

> **Note:** MoviePy also requires **ffmpeg** to be installed and on your PATH.
> Download from https://ffmpeg.org/download.html or install via `winget install ffmpeg`.

### 2. Set your Google API key

Option A — `.env` file (recommended):

```powershell
Copy-Item .env.example .env
# Then open .env and paste your key
```

Option B — PowerShell session:

```powershell
$env:GOOGLE_API_KEY = "your-key-here"
```

Get a free API key at: https://aistudio.google.com/app/apikey

## Usage

### Command line

```powershell
# Basic usage — prints transcript to console
python transcribe.py path\to\recording.mp4

# Save transcript to a file
python transcribe.py path\to\recording.mp4 --output transcript.txt

# Keep the intermediate WAV file
python transcribe.py path\to\recording.mp4 --keep-audio

# Different language
python transcribe.py path\to\recording.mp4 --language Hindi
```

### Import as a module

```python
from transcribe import transcribe_video

transcript = transcribe_video("recording.mp4")
print(transcript)
```
