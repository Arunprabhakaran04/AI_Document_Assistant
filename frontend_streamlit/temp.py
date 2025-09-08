import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

# Session state init
for key in ["auth_token", "email", "messages"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "messages" else []

# ---------- Auth UI ---------- #
def register():
    st.markdown("### Register")
    email = st.text_input("Email", key="reg_user")
    password = st.text_input("Password", type="password", key="reg_pass")
    if st.button("Register"):
        res = requests.post(f"{API_URL}/register", json={"email": email, "password": password})
        if res.status_code == 201:
            st.success("Registration successful. Please login.")
        else:
            st.error(res.json().get("detail", "Registration failed."))

def login():
    st.markdown("### Login")
    email = st.text_input("Email", key="log_user")
    password = st.text_input("Password", type="password", key="log_pass")
    if st.button("Login"):
        res = requests.post(f"{API_URL}/login", json={"email": email, "password": password})
        if res.status_code == 200:
            st.session_state.auth_token = res.json()["access_token"]
            st.session_state.email = email
            st.success("Login successful.")
            st.rerun()
        else:
            st.error(res.json().get("detail", "Login failed."))

def logout():
    try:
        headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
        requests.post(f"{API_URL}/logout", headers=headers)
    except Exception as e:
        print(f"Logout warning: {e}")
    finally:
        for key in ["auth_token", "email", "messages"]:
            st.session_state[key] = None if key != "messages" else []
        st.rerun()

# ---------- PDF Upload ---------- #
def sidebar_controls():
    st.sidebar.markdown(f"**Logged in as:** `{st.session_state.email}`")
    if st.sidebar.button("Logout"):
        logout()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📄 Upload a PDF")
    uploaded_file = st.sidebar.file_uploader("Choose PDF", type=["pdf"])
    if st.sidebar.button("Upload PDF") and uploaded_file:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
        res = requests.post(f"{API_URL}/upload_pdf", files=files, headers=headers)
        if res.status_code == 201:
            st.sidebar.success("PDF uploaded and embedded.")
        else:
            st.sidebar.error(res.json().get("detail", "Upload failed."))

# ---------- Chat UI ---------- #
def chat_ui():
    st.subheader("Chat with AI")
    
    # Display previous messages
    for msg in st.session_state.messages:
        role = msg["role"]
        content = msg["content"]
        with st.chat_message(role):
            st.markdown(content)

    user_input = st.chat_input("Ask something...")
    if user_input:
        # Display user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Send user input to backend
        headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
        payload = {"query": user_input}
        response = requests.post(f"{API_URL}/chat", json=payload, headers=headers)

        if response.status_code == 200:
            result = response.json()
            reply = result.get("response", "")
            source = result.get("source", "unknown")

            # If response is a dict, attempt to extract text content
            if isinstance(reply, dict):
                reply = reply.get("result") or next((v for v in reply.values() if isinstance(v, str)), "[No response]")

            # Add a small indicator of the source
            if source == "rag":
                reply += "\n\n*📄 Answer based on your uploaded document*"
            elif source == "general":
                reply += "\n\n*🤖 General AI response*"
        else:
            print(response.status_code)
            reply = "Something went wrong."

        # Display assistant message
        st.session_state.messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)


# ---------- Main ---------- #
def main():
    st.set_page_config(page_title="Multilingual RAG Chatbot", layout="wide")
    if st.session_state.auth_token:
        sidebar_controls()
        chat_ui()
    else:
        st.sidebar.title("Welcome")
        menu = st.sidebar.radio("Menu", ["Login", "Register"])
        login() if menu == "Login" else register()

if __name__ == "__main__":
    main()
