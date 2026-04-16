import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv

from utils.styles import apply_custom_css
from core.ingestor import DocumentIngestor
from core.agent import LegalAgent

# Load environment variables
load_dotenv()

# Page config must be first
st.set_page_config(
    page_title="LexiGuard AI | Legal Tech Platform",
    page_icon="⚖️",
    layout="wide"
)

# Apply Custom CSS Theme
apply_custom_css()

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "disclaimer_accepted" not in st.session_state:
    st.session_state.disclaimer_accepted = False
if "agent" not in st.session_state:
    # We will initialize it after checking API key or we can initialize it directly 
    # relying on the env variable HF_TOKEN
    try:
        st.session_state.agent = LegalAgent()
    except Exception as e:
        st.session_state.agent = None
        st.session_state.init_error = str(e)
if "ingestor" not in st.session_state:
    st.session_state.ingestor = DocumentIngestor()

# --- Disclaimer Popup Dialog ---
@st.dialog("⚖️ Legal Disclaimer")
def show_disclaimer():
    st.warning(
        """
        **Welcome to LexiGuard AI.**
        
        The insights provided by this AI agent are automatically generated 
        for informational purposes only. They do NOT constitute formal legal advice, 
        and no attorney-client relationship is formed.

        Please consult with a qualified attorney before taking any legal action.
        """
    )
    if st.button("I Agree & Understand"):
        st.session_state.disclaimer_accepted = True
        st.rerun()

if not st.session_state.disclaimer_accepted:
    show_disclaimer()
    st.stop()  # Stop rendering the rest of the app until accepted

# --- Sidebar: Document Management ---
with st.sidebar:
    st.markdown('<div class="sidebar-header">LexiGuard AI ⚖️</div>', unsafe_allow_html=True)
    st.markdown("### 📄 Document Source")
    st.info("Upload a document or provide a URL to begin analysis.")
    
    upload_option = st.radio("Choose Input Method:", ["Upload File", "PDF URL"])
    
    if upload_option == "Upload File":
        uploaded_file = st.file_uploader("Upload Legal Document", type=["pdf", "docx"])
        if st.button("Process Document"):
            if uploaded_file:
                with st.spinner("Analyzing Document..."):
                    try:
                        st.session_state.ingestor.ingest(uploaded_file, is_url=False)
                        # Re-init agent to catch the new Chroma data if it wasn't there
                        st.session_state.agent = LegalAgent()
                        st.success("Document analyzed successfully!")
                    except Exception as e:
                        st.error(f"Error processing document: {e}")
            else:
                st.warning("Please upload a file first.")
                
    elif upload_option == "PDF URL":
        pdf_url = st.text_input("Enter PDF URL:")
        if st.button("Process URL"):
            if pdf_url:
                with st.spinner("Fetching and Analyzing..."):
                    try:
                        st.session_state.ingestor.ingest(pdf_url, is_url=True)
                        # Re-init agent to catch new Chroma data
                        st.session_state.agent = LegalAgent()
                        st.success("URL content analyzed successfully!")
                    except Exception as e:
                        st.error(f"Error processing URL: {e}")
            else:
                st.warning("Please enter a URL first.")

# --- Main Area: Chat Interface ---
st.title("⚖️ LexiGuard AI Legal Advisor")

if getattr(st.session_state, 'init_error', None):
    st.error(f"Agent Initialization Error: {st.session_state.init_error}. Did you set the HF_TOKEN?")

# Display chat messages from history
for message in st.session_state.messages:
    if isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.markdown(message.content)
    elif isinstance(message, AIMessage):
        with st.chat_message("assistant", avatar="⚖️"):
            st.markdown(message.content)

# Chat input
if prompt := st.chat_input("Ask a legal question about your documents..."):
    # Add human message to state
    st.session_state.messages.append(HumanMessage(content=prompt))
    with st.chat_message("user"):
        st.markdown(prompt)

    if not st.session_state.agent:
        st.error("Agent not initialized properly. Please check your HuggingFace HF_TOKEN.")
        st.stop()

    with st.chat_message("assistant", avatar="⚖️"):
        try:
            latest_response = None
            with st.status("Thinking...", expanded=True) as status:
                st.write("🔍 Initializing Analysis...")
                
                # Stream the langgraph steps
                for event in st.session_state.agent.graph.stream({"messages": st.session_state.messages}):
                    for node, state in event.items():
                        if node == "search":
                            st.write("📖 Reading the Document Context...")
                        elif node == "analyze":
                            st.write("🧠 Analyzing Legal Clauses...")
                        elif node == "verify":
                            st.write("⚖️ Verifying Legal Soundness & Citations...")
                        elif node == "respond":
                            st.write("✍️ Preparing Final Response...")
                            latest_response = state["messages"][-1]
                
                status.update(label="Analysis Complete", state="complete", expanded=False)
            
            if latest_response:
                # Simulated typing for st.write_stream
                def stream_response(text):
                    import time
                    # We stream word by word to create a typing effect
                    words = text.split(" ")
                    for i, word in enumerate(words):
                        yield word + (" " if i < len(words) - 1 else "")
                        time.sleep(0.02)

                # Display streamed text
                st.write_stream(stream_response(latest_response.content))
                
                # Append to actual message history
                st.session_state.messages.append(latest_response)

        except Exception as e:
            st.error(f"Error yielding response: {str(e)}")
