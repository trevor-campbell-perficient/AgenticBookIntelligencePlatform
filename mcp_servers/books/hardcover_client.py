import httpx
from typing import Any

HARDCOVER_GRAPHQL_URL = "https://api.hardcover.app/v1/graphql"

SEARCH_QUERY = """
query SearchBooks($query: String!) {
  search(query: $query, query_type: "Book", per_page: 10) {
    results
  }
}
"""

GET_BOOK_QUERY = """
query GetBook($id: Int!) {
  books(where: {id: {_eq: $id}}) {
    id title description pages
    book_series { position series { name } }
    contributions { author { name } }
    ratings_count
    rating
    image { url }
    release_date
  }
}
"""

GET_REVIEWS_QUERY = """
query GetReviews($bookId: Int!, $limit: Int!) {
  user_books(where: {book_id: {_eq: $bookId}, review: {_is_null: false}}, limit: $limit) {
    rating review user { username }
  }
}
"""

GET_AUTHOR_QUERY = """
query GetAuthor($name: String!) {
  authors(where: {name: {_ilike: $name}}, limit: 1) {
    id name bio
    author_books(limit: 20) { book { id title } }
  }
}
"""


class HardcoverClient:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def _query(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    HARDCOVER_GRAPHQL_URL,
                    json={"query": query, "variables": variables},
                    headers=self.headers,
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.TimeoutException:
            return {"error": True, "errorCategory": "transient", "isRetryable": True, "message": "Hardcover API timeout"}
        except httpx.HTTPStatusError as e:
            return {"error": True, "errorCategory": "transient", "isRetryable": True, "message": f"HTTP {e.response.status_code}"}
        except Exception as e:
            return {"error": True, "errorCategory": "transient", "isRetryable": False, "message": str(e)}

    async def search_books(self, query: str) -> list[dict[str, Any]] | dict[str, Any]:
        result = await self._query(SEARCH_QUERY, {"query": query})
        if "error" in result:
            return result
        try:
            results = result["data"]["search"]["results"]
            items = results if isinstance(results, list) else []
            return [
                {
                    "id": str(r.get("id", "")),
                    "title": r.get("title", ""),
                    "author": r.get("author_names", [""])[0] if r.get("author_names") else "",
                }
                for r in items
            ]
        except (KeyError, TypeError):
            return {"error": True, "errorCategory": "transient", "isRetryable": True, "message": "Unexpected response structure"}

    async def get_book_details(self, book_id: int) -> dict[str, Any]:
        result = await self._query(GET_BOOK_QUERY, {"id": book_id})
        if "error" in result:
            return result
        try:
            books = result["data"]["books"]
            if not books:
                return {"error": True, "errorCategory": "validation", "isRetryable": False, "message": f"Book {book_id} not found"}
            return books[0]
        except (KeyError, TypeError) as e:
            return {"error": True, "errorCategory": "transient", "isRetryable": True, "message": str(e)}

    async def get_book_reviews(self, book_id: int, limit: int = 20) -> list[dict[str, Any]] | dict[str, Any]:
        result = await self._query(GET_REVIEWS_QUERY, {"bookId": book_id, "limit": limit})
        if "error" in result:
            return result
        try:
            return result["data"]["user_books"]
        except (KeyError, TypeError) as e:
            return {"error": True, "errorCategory": "transient", "isRetryable": True, "message": str(e)}

    async def get_author_details(self, author_name: str) -> dict[str, Any]:
        result = await self._query(GET_AUTHOR_QUERY, {"name": author_name})
        if "error" in result:
            return result
        try:
            authors = result["data"]["authors"]
            if not authors:
                return {"error": True, "errorCategory": "validation", "isRetryable": False, "message": f"Author '{author_name}' not found"}
            return authors[0]
        except (KeyError, TypeError) as e:
            return {"error": True, "errorCategory": "transient", "isRetryable": True, "message": str(e)}
