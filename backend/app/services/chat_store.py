from ...mongo_connection import chat_collection
from datetime import datetime

def store_message(user_id: int, chat_id: str, user_msg: str, assistant_msg: str):
    update_data = {
        "$push": {
            "messages": [
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": assistant_msg}
            ]
        },
        "$setOnInsert": {
            "created_at": datetime.now(),
            "title": user_msg[:40]  # Auto-title from first user message
        }
    }

    chat_collection.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        update_data,
        upsert=True
    )


def fetch_previous_messages(user_id: int, chat_id: str, limit: int = 5):
    doc = chat_collection.find_one({"chat_id": chat_id, "user_id": user_id})
    if doc and "messages" in doc:
        return doc["messages"][-limit:]
    return []


def list_chats(user_id: int):
    return [{"chat_id": doc["chat_id"], "title": doc.get("title", "Untitled Chat")} for doc in chat_collection.find({"user_id": user_id})]



def get_chat_messages(user_id: int, chat_id: str):
    chat = chat_collection.find_one({"chat_id": chat_id, "user_id": user_id})
    return chat["messages"] if chat else []
