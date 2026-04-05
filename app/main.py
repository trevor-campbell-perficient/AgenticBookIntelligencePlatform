import streamlit as st

st.set_page_config(
    page_title="Agentic Book Intelligence Platform",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Agentic Book Intelligence Platform")
st.write(
    "Welcome! Use the sidebar to navigate between Chat, Library, Discover, Insights, and Annotations."
)
st.info(
    "Ask anything in Chat — 'What should I read next?', "
    "'How many books did I finish this year?', 'Tell me about the Mistborn series'"
)
