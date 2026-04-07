import streamlit as st
from app.utils import get_agent_response, init_chat_history, add_message

st.title("Chat with your Book Intelligence")
init_chat_history()

# Display history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Tool activity sidebar
with st.sidebar:
    st.subheader("Agent Activity")
    if st.session_state.get("last_agents_used"):
        for agent in st.session_state.last_agents_used:
            st.write(f"- {agent}")

# Input
if prompt := st.chat_input("Ask about books, your reading history, or get recommendations..."):
    add_message("user", prompt)
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = get_agent_response(prompt)
            except Exception as e:
                response = f"Sorry, I couldn't process your request right now. ({type(e).__name__}: {e})"
                st.warning(response)
        if response:
            st.write(response)
    add_message("assistant", response)
