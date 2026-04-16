import streamlit as st

def apply_custom_css():
    st.markdown(
        """
        <style>
        /* Dark Mode Theme optimized for LexiGuard AI */
        :root {
            --primary-bg: #0E1117;
            --secondary-bg: #1A1C23;
            --text-color: #FAFAFA;
            --accent-color: #B8860B; /* Dark Goldenrod for legal feel */
            --border-color: #333333;
        }

        .stApp {
            background-color: var(--primary-bg);
            color: var(--text-color);
        }

        /* Sidebar Styling (Glassmorphism) */
        section[data-testid="stSidebar"] {
            background-color: rgba(26, 28, 35, 0.6);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }

        .sidebar-header {
            font-size: 24px;
            font-weight: bold;
            color: var(--accent-color);
            margin-bottom: 20px;
            text-align: center;
        }

        h1, h2, h3 {
            color: var(--accent-color) !important;
            font-family: 'Georgia', serif;
        }

        /* Chat Message Styling */
        .stChatMessage {
            background-color: var(--secondary-bg) !important;
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
        }

        /* Chat Input Glassmorphism */
        div[data-testid="stChatInput"] {
            background-color: rgba(26, 28, 35, 0.6) !important;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(184, 134, 11, 0.3) !important; /* using accent color slightly */
            border-radius: 10px;
        }
        div[data-testid="stChatInput"] textarea {
            background-color: transparent !important;
        }

        div[data-testid="stChatMessageAvatar"] {
            background-color: var(--accent-color);
        }

        /* Button Styling */
        .stButton>button {
            background-color: transparent !important;
            border: 1px solid var(--accent-color) !important;
            color: var(--accent-color) !important;
            border-radius: 5px;
            transition: all 0.3s ease;
        }

        .stButton>button:hover {
            background-color: var(--accent-color) !important;
            color: #121212 !important;
        }

        /* Tooltip and warnings styling */
        .stAlert {
            background-color: rgba(184, 134, 11, 0.1) !important;
            border-left: 5px solid var(--accent-color) !important;
            color: #FAFAFA !important;
        }

        /* File Uploader styling */
        .stFileUploader > div > div {
            background-color: var(--secondary-bg) !important;
            border: 1px dashed var(--accent-color) !important;
        }

        /* Clean wide mode adjustment */
        .main .block-container {
            max-width: 1000px;
            padding-top: 3rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
