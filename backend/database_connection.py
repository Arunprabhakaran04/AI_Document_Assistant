from psycopg2 import connect
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os
load_dotenv()

database = os.getenv("database")
user = os.getenv("user")
password = os.getenv("password_db")

def get_db_connection():
    try : 
        conn = connect(host = "localhost", database = database, user = user, password = password, cursor_factory=RealDictCursor)
        print("successfully connected to database")
        return conn
    except Exception as e :
        print("couldnt connecte to the database")
        print(f"error is {e}")
        return None
    