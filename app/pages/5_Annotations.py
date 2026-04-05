import streamlit as st

st.title("Annotations & Journal")

tab1, tab2 = st.tabs(["Annotations", "Reading Journal"])

with tab1:
    try:
        from mcp_servers.annotations.db import AnnotationsDB
        import os
        db = AnnotationsDB(os.environ.get("ANNOTATIONS_DB_PATH", "data/annotations.db"))
        db.init_schema()

        search_term = st.text_input("Search annotations", placeholder="e.g. 'fear', 'Dune'")

        if search_term:
            annotations = db.search_annotations(search_term)
        else:
            annotations = db.get_annotations()

        if annotations:
            for ann in annotations:
                with st.expander(f"{ann.get('book_title', 'Unknown')} — {ann.get('annotation_type', '')}"):
                    st.write(ann.get("content", ""))
                    if ann.get("page_number"):
                        st.caption(f"Page {ann['page_number']}")
        else:
            st.info("No annotations yet. Highlights and notes will appear here.")
    except Exception as e:
        st.warning(f"Could not load annotations: {e}")

with tab2:
    try:
        from mcp_servers.annotations.db import AnnotationsDB
        import os
        db = AnnotationsDB(os.environ.get("ANNOTATIONS_DB_PATH", "data/annotations.db"))
        db.init_schema()
        entries = db.get_journal_entries()

        if entries:
            for entry in entries:
                with st.expander(f"{entry.get('book_title', 'Unknown')} — {entry.get('session_date', '')}"):
                    st.write(entry.get("content", ""))
                    cols = st.columns(3)
                    if entry.get("mood"):
                        cols[0].write(f"Mood: {entry['mood']}")
                    if entry.get("pages_read"):
                        cols[1].write(f"Pages: {entry['pages_read']}")
        else:
            st.info("No journal entries yet. Start logging your reading sessions!")
    except Exception as e:
        st.warning(f"Could not load journal: {e}")
