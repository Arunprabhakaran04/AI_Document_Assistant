import streamlit as st
import requests
import uuid
from datetime import datetime

API_URL = "http://127.0.0.1:8000"

# Session state initialization
def initialize_session_state():
    defaults = {
        "auth_token": None,
        "email": None,
        "messages": [],
        "chat_id": None,
        "chat_titles": [],
        "has_pdf": False,
        "pdf_filename": None,
        "upload_timestamp": None
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def register():
    st.header("Register")
    
    email = st.text_input("Email", key="reg_user")
    password = st.text_input("Password", type="password", key="reg_pass")
    
    if st.button("Create Account"):
        if not email or not password:
            st.error("Please fill in all fields")
            return
                    
        try:
            res = requests.post(f"{API_URL}/register", json={"email": email, "password": password})
            if res.status_code == 201:
                st.success("Account created successfully! Please login.")
            elif res.status_code == 400:
                error_detail = res.json().get('detail', '')
                if "already exists" in error_detail.lower():
                    st.error("An account with this email already exists. Please use a different email or log in.")
                else:
                    st.error(f"Registration failed: {error_detail}")
            else:
                st.error(f"Registration failed: {res.json().get('detail', 'Unknown error')}")
        except requests.RequestException:
            st.error("Unable to connect to server")

def login():
    st.header("Login")
    
    email = st.text_input("Email", key="log_user")
    password = st.text_input("Password", type="password", key="log_pass")
    
    if st.button("Sign In"):
        if not email or not password:
            st.error("Please fill in all fields")
            return
            
        try:
            res = requests.post(f"{API_URL}/login", json={"email": email, "password": password})
            if res.status_code == 200:
                st.session_state.auth_token = res.json()["access_token"]
                st.session_state.email = email
                load_chat_titles()
                st.success("Login successful!")
                st.rerun()
            else:
                st.error(f"Login failed: {res.json().get('detail', 'Invalid credentials')}")
        except requests.RequestException:
            st.error("Unable to connect to server")

def logout():
    try:
        headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
        requests.post(f"{API_URL}/logout", headers=headers)
    except Exception as e:
        print(f"Logout warning: {e}")
    finally:
        # Reset session state
        for key in ["auth_token", "email", "messages", "chat_id", "chat_titles", "has_pdf", "pdf_filename", "upload_timestamp"]:
            if key in ["messages", "chat_titles"]:
                st.session_state[key] = []
            elif key == "has_pdf":
                st.session_state[key] = False
            else:
                st.session_state[key] = None
        st.rerun()

def load_chat_titles():
    headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
    try:
        res = requests.get(f"{API_URL}/list_chats", headers=headers)
        if res.status_code == 200:
            st.session_state.chat_titles = res.json().get("chats", [])
        else:
            print(f"Failed to load chats: {res.status_code}")
    except requests.RequestException as e:
        print(f"Error loading chat titles: {e}")

def load_chat_messages(chat_id):
    headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
    try:
        res = requests.get(f"{API_URL}/chat_history/{chat_id}", headers=headers)
        if res.status_code == 200:
            messages_data = res.json().get("messages", [])
            # Convert database format to UI format
            formatted_messages = []
            for msg in messages_data:
                formatted_msg = {
                    "role": msg["role"],
                    "content": msg["content"]
                }
                # Add source info for assistant messages
                if msg["role"] == "assistant" and msg.get("source"):
                    if msg["source"] == "rag":
                        formatted_msg["content"] += "\n\n*Answer based on your uploaded document*"
                    elif msg["source"] == "general":
                        formatted_msg["content"] += "\n\n*General AI response*"
                formatted_messages.append(formatted_msg)
            
            st.session_state.chat_id = chat_id
            st.session_state.messages = formatted_messages
        else:
            st.error("Failed to load chat history")
    except requests.RequestException:
        st.error("Unable to connect to server")

def delete_chat(chat_id):
    headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
    try:
        res = requests.delete(f"{API_URL}/chat/{chat_id}", headers=headers)
        if res.status_code == 200:
            # Reload chat list
            load_chat_titles()
            # Clear current chat if it was deleted
            if st.session_state.chat_id == chat_id:
                st.session_state.chat_id = None
                st.session_state.messages = []
            st.success("Chat deleted successfully!")
            st.rerun()
        else:
            st.error("Failed to delete chat")
    except requests.RequestException:
        st.error("Unable to connect to server")

def sidebar_controls():
    st.sidebar.title("AI Assistant")
    st.sidebar.write(f"Welcome, {st.session_state.email}")
    
    if st.sidebar.button("Logout"):
        logout()

    st.sidebar.markdown("---")
    
    # PDF Upload Section
    st.sidebar.subheader("Document Upload")
    
    if st.session_state.has_pdf:
        st.sidebar.success(f"PDF Active: {st.session_state.pdf_filename}")
        if st.session_state.upload_timestamp:
            upload_time = datetime.fromisoformat(st.session_state.upload_timestamp)
            st.sidebar.write(f"Uploaded: {upload_time.strftime('%Y-%m-%d %H:%M')}")
    else:
        st.sidebar.warning("No PDF uploaded - Using general AI")
    
    uploaded_file = st.sidebar.file_uploader("Upload PDF Document", type=["pdf"])
    
    if st.sidebar.button("Upload PDF") and uploaded_file:
        try:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
            res = requests.post(f"{API_URL}/upload_pdf", files=files, headers=headers)
            
            if res.status_code == 201:
                st.session_state.has_pdf = True
                st.session_state.pdf_filename = uploaded_file.name
                st.session_state.upload_timestamp = datetime.now().isoformat()
                st.sidebar.success("PDF uploaded successfully!")
                st.rerun()
            else:
                st.sidebar.error(f"Upload failed: {res.json().get('detail', 'Unknown error')}")
        except requests.RequestException:
            st.sidebar.error("Unable to connect to server")

    st.sidebar.markdown("---")
    
    # Chat Management
    st.sidebar.subheader("Chat Management")
    
    if st.sidebar.button("New Chat"):
        st.session_state.chat_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()
    
    # Previous Chats
    if st.session_state.chat_titles:
        st.sidebar.write("Previous Chats:")
        
        for chat in st.session_state.chat_titles:
            chat_title = chat["title"]
            chat_id = chat["chat_id"]
            
            # Create columns for chat title and delete button
            col1, col2 = st.sidebar.columns([3, 1])
            
            with col1:
                if st.button(chat_title, key=f"load_{chat_id}", help=f"Created: {chat.get('created_at', 'Unknown')}"):
                    load_chat_messages(chat_id)
                    st.rerun()
            
            with col2:
                if st.button("🗑️", key=f"del_{chat_id}", help="Delete chat"):
                    delete_chat(chat_id)
    
    # Clear PDF option
    if st.session_state.has_pdf:
        st.sidebar.markdown("---")
        if st.sidebar.button("Clear PDF"):
            st.session_state.has_pdf = False
            st.session_state.pdf_filename = None
            st.session_state.upload_timestamp = None
            st.sidebar.success("PDF cleared from session")
            st.rerun()

def chat_ui():
    st.title("Chat Assistant")
    
    # Current chat info
    if st.session_state.chat_id:
        st.write(f"**Chat ID:** `{st.session_state.chat_id[:8]}...`")
    
    # PDF Status
    if st.session_state.has_pdf:
        st.info(f"📄 PDF Active: {st.session_state.pdf_filename}")
    else:
        st.warning("⚠️ No PDF uploaded - Using general AI")
    
    # Chat messages container
    chat_container = st.container()
    
    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.write(msg['content'])
            else:
                with st.chat_message("assistant"):
                    st.write(msg['content'])
    
    # Chat input
    user_input = st.chat_input("Ask me anything...")
    
    if user_input:
        # Ensure we have a chat_id
        if not st.session_state.chat_id:
            st.session_state.chat_id = str(uuid.uuid4())
        
        # Add user message to UI immediately
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Prepare API request
        headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
        payload = {
            "query": user_input,
            "chat_id": st.session_state.chat_id,
            "has_pdf": st.session_state.has_pdf
        }
        
        with st.spinner("Thinking..."):
            try:
                response = requests.post(f"{API_URL}/chat", json=payload, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    reply = result.get("response", "")
                    source = result.get("source", "unknown")
                    
                    # Handle different response formats
                    if isinstance(reply, dict):
                        reply = reply.get("result") or next((v for v in reply.values() if isinstance(v, str)), "[No response]")
                    
                    # Add source indicator
                    if source == "rag":
                        reply += "\n\n*Answer based on your uploaded document*"
                    elif source == "general":
                        reply += "\n\n*General AI response*"
                    
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    
                    # Reload chat titles to show the new/updated chat
                    load_chat_titles()
                else:
                    error_msg = f"Error: {response.status_code} - {response.json().get('detail', 'Something went wrong')}"
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    
            except requests.RequestException as e:
                error_msg = f"Unable to connect to server: {str(e)}"
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        st.rerun()

def main():
    st.set_page_config(page_title="AI Document Assistant", page_icon="🤖", layout="wide")
    
    # Initialize session state
    initialize_session_state()
    
    if st.session_state.auth_token:
        sidebar_controls()
        chat_ui()
    else:
        st.sidebar.title("AI Assistant")
        st.sidebar.write("Please sign in to continue")
        
        menu = st.sidebar.radio("Choose an option:", ["Login", "Register"])
        
        if menu == "Login":
            login()
        else:
            register()

if __name__ == "__main__":
    main()