import streamlit as st

st.title("Discover Books")

query = st.text_input("Search for books, authors, or topics", placeholder="e.g. 'hard sci-fi', 'Ursula Le Guin'")

if query:
    with st.spinner("Searching..."):
        try:
            from mcp_servers.books.hardcover_client import HardcoverClient
            import asyncio
            import os
            client = HardcoverClient(api_key=os.environ.get("HARDCOVER_API_KEY", ""))
            results = asyncio.run(client.search_books(query))
            if isinstance(results, list) and results:
                for book in results[:10]:
                    with st.expander(book.get("title", "Unknown")):
                        st.write(f"**Author:** {book.get('author', 'Unknown')}")
                        if book.get("description"):
                            st.write(book["description"][:300] + "..." if len(book.get("description", "")) > 300 else book["description"])
            else:
                st.info("No results found. Try a different search term.")
        except Exception as e:
            st.warning(f"Search unavailable: {e}")
            st.info("Book search requires a Hardcover API key.")
