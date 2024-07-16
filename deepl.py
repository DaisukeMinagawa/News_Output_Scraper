import os
import deepl
from dotenv import load_dotenv


# Set your Deepl API key
load_dotenv()
API_Key = os.getenv("DEEPL_API_KEY")
deepl.set_auth_key(API_Key)