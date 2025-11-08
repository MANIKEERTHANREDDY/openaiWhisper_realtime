#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Audio Encryption, Transcription, and Translation Tool
-----------------------------------------------------
This script records or uploads encrypted audio, decrypts it, transcribes it using OpenAI Whisper,
optionally translates it with Google Translate, and re-encrypts it for secure storage.
Designed for Google Colab environment.
"""

import base64
import time
import whisper
import numpy as np
from googletrans import Translator
from cryptography.fernet import Fernet
from google.colab import files
from google.colab.output import eval_js
from IPython.display import HTML, Javascript
import os
import ffmpeg

def generate_key(password):
    return base64.urlsafe_b64encode(password.ljust(32)[:32].encode())

def encrypt_file(filename, password):
    key = generate_key(password)
    fernet = Fernet(key)
    with open(filename, 'rb') as file:
        original = file.read()
    encrypted = fernet.encrypt(original)
    with open(filename, 'wb') as encrypted_file:
        encrypted_file.write(encrypted)
    print(f"File '{filename}' has been encrypted.")

def decrypt_file(filename, password):
    key = generate_key(password)
    fernet = Fernet(key)
    try:
        with open(filename, 'rb') as encrypted_file:
            encrypted = encrypted_file.read()
        decrypted = fernet.decrypt(encrypted)
        with open(filename, 'wb') as decrypted_file:
            decrypted_file.write(decrypted)
        print(f"File '{filename}' has been decrypted.")
    except Exception as e:
        print(f"Decryption failed: {e}")

def list_audio_files():
    files = [f for f in os.listdir('.') if f.endswith('.wav') or f.endswith('.mp3')]
    return files

def select_file(files):
    print("Available audio files:")
    for i, file in enumerate(files):
        print(f"{i + 1}. {file}")
    choice = int(input("Enter the number of the file you want to select: "))
    return files[choice - 1]

def reencode_audio(input_file, output_file):
    try:
        ffmpeg.input(input_file).output(output_file).run(overwrite_output=True)
        print(f"Audio re-encoded to {output_file}")
        return output_file
    except ffmpeg.Error as e:
        print(f"Error re-encoding audio: {e}")
        return None

def record_or_upload():
    choice = input("Do you want to\n(1) Record new audio, \n(2) Use an existing encrypted audio file from Colab? Enter 1, or 2: ")
    if choice == '1':
        js = Javascript("""async function recordAudio() {
            const div = document.createElement('div');
            const audio = document.createElement('audio');
            const strtButton = document.createElement('button');
            const stopButton = document.createElement('button');
            strtButton.textContent = 'Start Recording';
            stopButton.textContent = 'Stop Recording';
            document.body.appendChild(div);
            div.appendChild(strtButton);
            div.appendChild(audio);
            const stream = await navigator.mediaDevices.getUserMedia({audio:true});
            let recorder = new MediaRecorder(stream);
            audio.style.display = 'block';
            audio.srcObject = stream;
            audio.controls = true;
            audio.muted = true;
            await new Promise((resolve) => strtButton.onclick = resolve);
            strtButton.replaceWith(stopButton);
            recorder.start();
            await new Promise((resolve) => stopButton.onclick = resolve);
            recorder.stop();
            let recData = await new Promise((resolve) => recorder.ondataavailable = resolve);
            let arrBuff = await recData.data.arrayBuffer();
            stream.getAudioTracks()[0].stop();
            div.remove();
            let binaryString = '';
            let bytes = new Uint8Array(arrBuff);
            bytes.forEach((byte) => { binaryString += String.fromCharCode(byte); });
            const url = URL.createObjectURL(recData.data);
            const player = document.createElement('audio');
            player.controls = true;
            player.src = url;
            document.body.appendChild(player);
            return btoa(binaryString)};""")
        display(js)
        output = eval_js('recordAudio({})')
        filename = f"audio_{int(time.time())}.wav"
        with open(filename, 'wb') as file:
            binary = base64.b64decode(output)
            file.write(binary)
        print('Recording saved to:', file.name)
        password = input("Enter a password to encrypt the file: ")
        encrypt_file(filename, password)
        decrypt_file(filename, password)
        return filename, password
    elif choice == '/':
        print("Please upload your encrypted audio file.")
        uploaded = files.upload()
        filename = list(uploaded.keys())[0]
        password = input("Enter the password to decrypt the file: ")
        decrypt_file(filename, password)
        return filename, password
    elif choice == '2':
        files_list = list_audio_files()
        if not files_list:
            print("No audio files found in the environment.")
            return None, None
        filename = select_file(files_list)
        password = input("Enter the password to decrypt the file: ")
        decrypt_file(filename, password)
        return filename, password
    else:
        print("Invalid choice.")
        return None, None

def transcribe_and_translate(audio_filename, target_language=None):
    model = whisper.load_model("medium")
    try:
        audio = whisper.load_audio(audio_filename)
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio).to(model.device)
        _, probs = model.detect_language(mel)
        detected_language = max(probs, key=probs.get)
        print(f"Detected language: {detected_language}")
        options = whisper.DecodingOptions()
        result = whisper.decode(model, mel, options)
        transcription = result.text
        print("Transcription:", transcription)
        if target_language:
            translator = Translator()
            translation = translator.translate(transcription, dest=target_language)
            print(f"Translation to {target_language}: {translation.text}")
            return transcription, translation.text
        else:
            return transcription, None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None

def main():
    audio_file, password = record_or_upload()
    if audio_file:
        target_language = input("Enter the target language code, or press Enter to skip translation: ")
        transcribe_and_translate(audio_file, target_language if target_language else None)
        encrypt_file(audio_file, password)

if __name__ == "__main__":
    main()
