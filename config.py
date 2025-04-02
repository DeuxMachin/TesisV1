import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-testing'
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database', 'proteins_discovery.db')
    TEMP_DIR = os.path.join(os.path.dirname(__file__), 'data', 'temp')
    OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'data', 'output')
    
    # Asegurar que los directorios existan
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)