import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback_super_secret_key_CHANGE_ME'
    if SECRET_KEY == 'fallback_super_secret_key_CHANGE_ME' and os.environ.get('FLASK_ENV') == 'production':
        print("WARNING: USING DEFAULT SECRET_KEY! SET SECRET_KEY ENVIRONMENT VARIABLE.")

    DATABASE_URL = os.environ.get('DATABASE_URL') or \
                   'mysql+pymysql://root:@localhost:3306/zodiac_chatbot'

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_TYPE = "filesystem"
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'chatbot_session_'

    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    DATA_DIRECTORY = os.environ.get('DATA_DIRECTORY') or 'data'
    VECTOR_DB_PATH = os.path.join(BASE_DIR, 'data', 'chroma_db')
    TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    GEMINI_MODEL_NAME = 'gemini-2.0-flash'

    SENTENCE_TRANSFORMER_MODEL_NAME = 'distiluse-base-multilingual-cased-v2'
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200

