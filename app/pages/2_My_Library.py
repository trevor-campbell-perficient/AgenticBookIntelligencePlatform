import streamlit as st

st.title("My Library")

try:
    from mcp_servers.databricks.db_client import query_reading_log
    books = query_reading_log()

    status_filter = st.selectbox("Filter by status", ["all", "read", "reading", "want_to_read"])
    if status_filter != "all":
        books = [b for b in books if b.get("status") == status_filter]

    if books:
        for book in books:
            with st.expander(f"{book.get('title', 'Unknown')} — {book.get('status', '')}"):
                st.write(f"**Author:** {book.get('author', 'Unknown')}")
                if book.get("rating"):
                    st.write(f"**Rating:** {book['rating']}/5")
                if book.get("finished_date"):
                    st.write(f"**Finished:** {book['finished_date']}")
    else:
        st.info("No books in your library yet. Add some in Chat!")
except Exception as e:
    st.warning(f"Could not load library: {e}. Check Databricks connection.")
    st.info("Your library will appear here once your Databricks workspace is connected.")
