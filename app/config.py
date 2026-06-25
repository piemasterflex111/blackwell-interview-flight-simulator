import os

# Local LLM configuration
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:8001/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3.6-27b-nvfp4-mtp")

# Voice settings
VOICE_ENABLED = os.getenv("VOICE_ENABLED", "true").lower() == "true"
STT_MODEL = os.getenv("STT_MODEL", "small")  # whisper model size
TTS_VOICE = os.getenv("TTS_VOICE", "alloy")

# Session settings
SESSIONS_DIR = os.getenv("SESSIONS_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "sessions"))
MAX_SESSION_LENGTH = int(os.getenv("MAX_SESSION_LENGTH", "20"))  # minutes
PRACTICE_QUESTIONS = int(os.getenv("PRACTICE_QUESTIONS", "10"))
PRACTICE_REPEATS = int(os.getenv("PRACTICE_REPEATS", "3"))

# Interviewer settings
INTERVIEWER_PERSONA = os.getenv("INTERVIEWER_PERSONA", "skeptical_but_fair")
DEFAULT_ROLE = os.getenv("DEFAULT_ROLE", "Python Automation Engineer")
