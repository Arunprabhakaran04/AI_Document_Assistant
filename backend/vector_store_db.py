import psycopg2
from typing import Optional

def save_vector_store_path(conn, user_id: int, vector_store_path: str):
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE user_vector_stores SET is_active = FALSE WHERE user_id = %s", (user_id,))
        
        cursor.execute("""
            INSERT INTO user_vector_stores (user_id, vector_store_path, is_active) 
            VALUES (%s, %s, %s)
        """, (user_id, vector_store_path, True))
        
        conn.commit()
        print(f"Saved vector store path for user {user_id}: {vector_store_path}")
        
    except Exception as e:
        conn.rollback()
        print(f"Error saving vector store path: {e}")
        raise e
    finally:
        cursor.close()

def get_user_vector_store_path(conn, user_id: int) -> Optional[str]:
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT vector_store_path 
            FROM user_vector_stores 
            WHERE user_id = %s AND is_active = TRUE 
            ORDER BY created_at DESC 
            LIMIT 1
        """, (user_id,))
        
        row = cursor.fetchone()
        if row:
            path = row[0]
            print(f"Found vector store path for user {user_id}: {path}")
            return path
        else:
            print(f"No active vector store found for user {user_id}")
            return None
            
    except Exception as e:
        print(f"Error getting vector store path: {e}")
        return None
    finally:
        cursor.close()