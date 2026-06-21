from dotenv import load_dotenv
import os
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# مسیر پایگاه داده SQLite
DB_PATH = os.path.join(os.path.dirname(__file__), "database" , "spoilers.db")
