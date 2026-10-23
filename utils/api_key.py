"""Load OpenAI configuration from project .env, environment or Streamlit secrets."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent

def get_api_key():
    # Load from project root independently of the working directory.
    load_dotenv(dotenv_path=ROOT / '.env', override=False)
    key = os.getenv('OPENAI_API_KEY', '').strip().strip('"').strip("'")
    try:
        import streamlit as st
        secret = st.secrets.get('OPENAI_API_KEY', '')
        if secret and str(secret).strip():
            key = str(secret).strip()
    except (FileNotFoundError, KeyError, OSError):
        pass
    return key if key and not key.startswith('sk-your-') else ''

def get_model():
    load_dotenv(dotenv_path=ROOT / '.env', override=False)
    return os.getenv('OPENAI_MODEL', 'gpt-4o-mini').strip() or 'gpt-4o-mini'
