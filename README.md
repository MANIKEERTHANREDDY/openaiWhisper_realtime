# Whisper Audio Secure

Tool to record/upload encrypted audio, decrypt, transcribe via OpenAI Whisper, optionally translate via Google Translate, then re-encrypt.

## Quickstart (Google Colab)
1. Open this repo in Colab.
2. Install requirements:
   !pip install -r requirements.txt
3. Run:
   !python3 audio_encrypt_transcribe_translate.py

## Notes
- Designed for Google Colab browser recording via JS.
- Keep encryption passwords safe. Uses symmetric Fernet encryption.

