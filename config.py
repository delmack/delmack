# config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'voce-precisa-mudar-esta-chave-secreta'
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # Limite de 16MB para uploads
