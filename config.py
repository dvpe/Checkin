import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    
    # Configurações do banco de dados
    DB_HOST = os.environ.get('DB_HOST') or 'localhost'
    DB_USER = os.environ.get('DB_USER') or 'root'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'password'
    DB_NAME = os.environ.get('DB_NAME') or 'campanhas_vans_db'
    
    # Usar SQLAlchemy apenas para migrações, não para operações regulares
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://{user}:{password}@{host}/{db}'.format(
            user=DB_USER, password=DB_PASSWORD, host=DB_HOST, db=DB_NAME
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurações de upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    
    # Configurações da API
    API_TITLE = 'API de Gerenciamento de Campanhas em Vans Escolares'
    API_VERSION = '1.0'
    
    # CORS settings
    CORS_ORIGINS = '*'