import streamlit as st

st.title("Reading Insights")

try:
    import plotly.express as px
    import pandas as pd
    from mcp_servers.databricks.db_client import get_reading_stats, query_reading_log
    stats = get_reading_stats()
    log = query_reading_log()

    col1, col2, col3 = st.columns(3)
    col1.metric("Books Read", stats.get("read", 0))
    col2.metric("Currently Reading", stats.get("reading", 0))
    col3.metric("Want to Read", stats.get("want_to_read", 0))

    if log:
        df = pd.DataFrame(log)
        if "finished_date" in df.columns and df["finished_date"].notna().any():
            df["month"] = pd.to_datetime(df["finished_date"], errors="coerce").dt.to_period("M").astype(str)
            monthly = df.groupby("month").size().reset_index(name="books_finished")
            st.subheader("Reading Velocity")
            fig = px.bar(monthly, x="month", y="books_finished", title="Books Finished per Month")
            st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.warning(f"Could not load stats: {e}. Check Databricks connection.")
    st.info("Stats will appear here once your Databricks workspace is connected.")
