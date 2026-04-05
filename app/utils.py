import asyncio
import concurrent.futures
from typing import Optional
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def get_agent_response(user_message: str) -> str:
    """Call the coordinator agent and return response."""
    from agents.coordinator import route_request
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(asyncio.run, route_request(user_message, mcp_tools=[]))
        return future.result()


def init_chat_history() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []


def add_message(role: str, content: str) -> None:
    st.session_state.messages.append({"role": role, "content": content})
