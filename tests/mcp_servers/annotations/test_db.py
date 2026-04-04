import pytest
import os

@pytest.fixture
def db(tmp_path):
    from mcp_servers.annotations.db import AnnotationsDB
    db_path = str(tmp_path / "test.db")
    db = AnnotationsDB(db_path)
    db.init_schema()
    return db

def test_add_and_retrieve_annotation(db):
    ann_id = db.add_annotation(
        book_id="book1", book_title="Dune",
        annotation_type="highlight", content="I must not fear."
    )
    results = db.get_annotations(book_id="book1")
    assert len(results) == 1
    assert results[0]["content"] == "I must not fear."
    assert results[0]["id"] == ann_id

def test_get_annotations_returns_all_when_no_book_id(db):
    db.add_annotation(book_id="b1", book_title="Dune", annotation_type="note", content="Note 1")
    db.add_annotation(book_id="b2", book_title="Foundation", annotation_type="note", content="Note 2")
    results = db.get_annotations()
    assert len(results) == 2

def test_search_annotations_finds_by_keyword(db):
    db.add_annotation(book_id="b1", book_title="Dune", annotation_type="note", content="Fear is the mind killer")
    db.add_annotation(book_id="b2", book_title="Foundation", annotation_type="note", content="The fall of the empire")
    results = db.search_annotations("fear")
    assert len(results) == 1
    assert "Dune" in results[0]["book_title"]

def test_search_annotations_is_case_insensitive(db):
    db.add_annotation(book_id="b1", book_title="Dune", annotation_type="note", content="FEAR is the mind killer")
    results = db.search_annotations("fear")
    assert len(results) == 1

def test_add_and_retrieve_journal_entry(db):
    entry_id = db.add_journal_entry(
        book_id="book1", book_title="Dune",
        session_date="2026-04-04", content="Great session today",
        mood="focused", pages_read=50
    )
    results = db.get_journal_entries(book_id="book1")
    assert len(results) == 1
    assert results[0]["content"] == "Great session today"
    assert results[0]["pages_read"] == 50
    assert results[0]["id"] == entry_id

def test_init_schema_is_idempotent(db):
    # Calling init_schema twice should not raise
    db.init_schema()
    db.init_schema()
    # Should still work fine
    db.add_annotation(book_id="b1", book_title="Test", annotation_type="note", content="ok")
    assert len(db.get_annotations()) == 1

def test_annotation_with_page_number(db):
    db.add_annotation(
        book_id="b1", book_title="Dune",
        annotation_type="highlight", content="Quote here", page_number=142
    )
    results = db.get_annotations(book_id="b1")
    assert results[0]["page_number"] == 142
