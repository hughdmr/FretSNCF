from model import create_model
from dotenv import load_dotenv
import os

if __name__ == '__main__':
    load_dotenv()
    FILE_INSTANCE = os.getenv('FILE_INSTANCE')
    create_model(FILE_INSTANCE)
