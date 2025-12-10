from dotenv import load_dotenv
import os

load_dotenv()

POSTGRES_DNS = os.getenv("POSTGRES_DSN")