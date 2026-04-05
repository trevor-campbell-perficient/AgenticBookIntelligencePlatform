# Databricks DLT pipeline — deploy as a notebook in Databricks workspace
# dlt and spark are provided by the Databricks runtime environment
# This file should NOT be run directly — deploy via Databricks Workflows UI

try:
    import dlt
    from pyspark.sql.functions import col
    _DLT_AVAILABLE = True
except ImportError:
    _DLT_AVAILABLE = False


if _DLT_AVAILABLE:
    @dlt.table(comment="Books pending AI enrichment")
    def enrichment_queue():
        return spark.table("abip.books.enrichment_queue").filter(col("status") == "pending")

    @dlt.table(comment="AI-generated reading briefs")
    def reading_briefs():
        pending = dlt.read("enrichment_queue")
        # In production: call enrichment agent via Databricks SDK for each row
        # Current implementation reads book_ids for agent processing
        return pending.select("book_id")
