import streamlit as st
import requests
import uuid
from datetime import datetime

API_URL = "http://127.0.0.1:8000"

# Custom CSS for modern, clean design
def load_custom_css():
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Sidebar Styling */
    .css-1d391kg {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
    }
    
    /* Main content area */
    .main-content {
        background: #f8fafc;
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0;
    }
    
    /* Chat message styling */
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: 2rem;
    }
    
    .assistant-message {
        background: white;
        border-left: 4px solid #667eea;
        margin-right: 2rem;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 500;
        margin: 0.5rem 0;
    }
    
    .pdf-active {
        background: #dcfce7;
        color: #166534;
        border: 1px solid #bbf7d0;
    }
    
    .pdf-inactive {
        background: #fef3c7;
        color: #92400e;
        border: 1px solid #fde68a;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* File uploader */
    .stFileUploader {
        border: 2px dashed #667eea;
        border-radius: 12px;
        padding: 1rem;
        background: #f8fafc;
    }
    
    /* Success/Error messages */
    .stSuccess {
        background: #dcfce7 !important;
        border: 1px solid #bbf7d0 !important;
        color: #166534 !important;
    }
    
    .stError {
        background: #fef2f2 !important;
        border: 1px solid #fed7d7 !important;
        color: #dc2626 !important;
    }
    
    /* Sidebar title */
    .sidebar-title {
        color: white;
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    /* Chat input */
    .stChatInput {
        border-radius: 25px;
        border: 2px solid #e2e8f0;
        padding: 0.75rem 1rem;
    }
    
    /* Selectbox styling */
    .stSelectbox {
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# Session state initialization with PDF tracking
def initialize_session_state():
    defaults = {
        "auth_token": None,
        "email": None,
        "messages": [],
        "chat_id": None,
        "chat_titles": [],
        "has_pdf": False,  # NEW: Track PDF upload status
        "pdf_filename": None,  # NEW: Track uploaded PDF name
        "upload_timestamp": None  # NEW: Track when PDF was uploaded
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def register():
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    st.markdown("### 🚀 Create Your Account")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        email = st.text_input("📧 Email Address", key="reg_user", placeholder="Enter your email")
        password = st.text_input("🔒 Password", type="password", key="reg_pass", placeholder="Create a strong password")
        
        if st.button("Create Account", use_container_width=True):
            if not email or not password:
                st.error("Please fill in all fields")
                return
                
            with st.spinner("Creating your account..."):
                try:
                    res = requests.post(f"{API_URL}/register", json={"email": email, "password": password})
                    if res.status_code == 201:
                        st.success("🎉 Account created successfully! Please login.")
                    else:
                        st.error(f"❌ {res.json().get('detail', 'Registration failed')}")
                except requests.RequestException:
                    st.error("❌ Unable to connect to server")
    
    st.markdown('</div>', unsafe_allow_html=True)

def login():
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    st.markdown("### 🔐 Welcome Back")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        email = st.text_input("📧 Email Address", key="log_user", placeholder="Enter your email")
        password = st.text_input("🔒 Password", type="password", key="log_pass", placeholder="Enter your password")
        
        if st.button("Sign In", use_container_width=True):
            if not email or not password:
                st.error("Please fill in all fields")
                return
                
            with st.spinner("Signing you in..."):
                try:
                    res = requests.post(f"{API_URL}/login", json={"email": email, "password": password})
                    if res.status_code == 200:
                        st.session_state.auth_token = res.json()["access_token"]
                        st.session_state.email = email
                        load_chat_titles()
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error(f"❌ {res.json().get('detail', 'Login failed')}")
                except requests.RequestException:
                    st.error("❌ Unable to connect to server")
    
    st.markdown('</div>', unsafe_allow_html=True)

def logout():
    try:
        headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
        requests.post(f"{API_URL}/logout", headers=headers)
    except Exception as e:
        print(f"Logout warning: {e}")
    finally:
        # Reset all session state
        for key in st.session_state.keys():
            if key in ["auth_token", "email", "messages", "chat_id", "chat_titles", "has_pdf", "pdf_filename", "upload_timestamp"]:
                st.session_state[key] = None if key not in ["messages", "chat_titles"] else []
        st.session_state.has_pdf = False
        st.rerun()

def load_chat_titles():
    headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
    try:
        res = requests.get(f"{API_URL}/list_chats", headers=headers)
        if res.status_code == 200:
            st.session_state.chat_titles = res.json().get("chats", [])
    except requests.RequestException:
        st.error("Failed to load chat history")

def load_chat_messages(chat_id):
    headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
    try:
        res = requests.get(f"{API_URL}/chat_history/{chat_id}", headers=headers)
        if res.status_code == 200:
            st.session_state.chat_id = chat_id
            st.session_state.messages = res.json().get("messages", [])
        else:
            st.error("Failed to load chat history")
    except requests.RequestException:
        st.error("Unable to connect to server")

def pdf_status_indicator():
    """Display PDF upload status with modern styling"""
    if st.session_state.has_pdf:
        st.markdown(f"""
        <div class="status-indicator pdf-active">
            📄 PDF Active: {st.session_state.pdf_filename}
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.upload_timestamp:
            upload_time = datetime.fromisoformat(st.session_state.upload_timestamp)
            st.markdown(f"*Uploaded: {upload_time.strftime('%B %d, %Y at %I:%M %p')}*")
    else:
        st.markdown("""
        <div class="status-indicator pdf-inactive">
            ⚠️ No PDF uploaded - Using general AI
        </div>
        """, unsafe_allow_html=True)

def sidebar_controls():
    st.sidebar.markdown('<div class="sidebar-title">🤖 AI Assistant</div>', unsafe_allow_html=True)
    st.sidebar.markdown(f"**👋 Welcome,** `{st.session_state.email}`")
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout()

    st.sidebar.markdown("---")
    
    # PDF Upload Section
    st.sidebar.markdown("### 📄 Document Upload")
    pdf_status_indicator()
    
    uploaded_file = st.sidebar.file_uploader(
        "Upload PDF Document", 
        type=["pdf"], 
        help="Upload a PDF to chat with your document"
    )
    
    if st.sidebar.button("📤 Upload PDF", use_container_width=True) and uploaded_file:
        with st.spinner("Processing your document..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
                res = requests.post(f"{API_URL}/upload_pdf", files=files, headers=headers)
                
                if res.status_code == 201:
                    # Update PDF status in session state
                    st.session_state.has_pdf = True
                    st.session_state.pdf_filename = uploaded_file.name
                    st.session_state.upload_timestamp = datetime.now().isoformat()
                    st.sidebar.success("✅ PDF uploaded successfully!")
                    st.rerun()
                else:
                    st.sidebar.error(f"❌ {res.json().get('detail', 'Upload failed')}")
            except requests.RequestException:
                st.sidebar.error("❌ Unable to connect to server")

    st.sidebar.markdown("---")
    
    # Chat Management
    st.sidebar.markdown("### 💬 Chat Management")
    
    if st.sidebar.button("➕ New Chat", use_container_width=True):
        st.session_state.chat_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()
    
    # Previous Chats
    if st.session_state.chat_titles:
        st.sidebar.markdown("**Previous Chats:**")
        chat_dict = {chat["title"]: chat["chat_id"] for chat in st.session_state.chat_titles}
        selected_title = st.sidebar.selectbox(
            "Select chat", 
            options=list(chat_dict.keys()),
            index=0 if chat_dict else None
        )
        
        if st.sidebar.button("📂 Load Chat", use_container_width=True):
            load_chat_messages(chat_dict[selected_title])
            st.rerun()
    
    # Clear PDF option
    if st.session_state.has_pdf:
        st.sidebar.markdown("---")
        if st.sidebar.button("🗑️ Clear PDF", use_container_width=True):
            st.session_state.has_pdf = False
            st.session_state.pdf_filename = None
            st.session_state.upload_timestamp = None
            st.sidebar.success("PDF cleared from session")
            st.rerun()

def chat_ui():
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    # Header with status
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("## 💭 Chat Assistant")
    with col2:
        pdf_status_indicator()
    
    # Chat messages
    chat_container = st.container()
    
    with chat_container:
        for i, msg in enumerate(st.session_state.messages):
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>You:</strong><br>
                    {msg["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>🤖 Assistant:</strong><br>
                    {msg["content"]}
                </div>
                """, unsafe_allow_html=True)
    
    # Chat input
    user_input = st.chat_input("💬 Ask me anything...")
    
    if user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Prepare API request with PDF status
        headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
        payload = {
            "query": user_input,
            "chat_id": st.session_state.chat_id,
            "has_pdf": st.session_state.has_pdf  # NEW: Send PDF status to backend
        }
        
        with st.spinner("🤔 Thinking..."):
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
                        reply += "\n\n*📄 Answer based on your uploaded document*"
                    elif source == "general":
                        reply += "\n\n*🌐 General AI response*"
                    
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                else:
                    error_msg = "❌ Something went wrong. Please try again."
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    
            except requests.RequestException:
                error_msg = "❌ Unable to connect to server. Please check your connection."
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    st.set_page_config(
        page_title="AI Document Assistant", 
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Load custom CSS
    load_custom_css()
    
    # Initialize session state
    initialize_session_state()
    
    if st.session_state.auth_token:
        sidebar_controls()
        chat_ui()
    else:
        st.sidebar.markdown('<div class="sidebar-title">🤖 AI Assistant</div>', unsafe_allow_html=True)
        st.sidebar.markdown("### Welcome! Please sign in to continue.")
        
        menu = st.sidebar.radio("Choose an option:", ["🔐 Login", "🚀 Register"])
        
        if menu == "🔐 Login":
            login()
        else:
            register()

if __name__ == "__main__":
    main()