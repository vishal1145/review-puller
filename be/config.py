from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')

GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY') 