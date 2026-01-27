from typing import TypedDict


class SearchResult(TypedDict):
    title: str
    type: str
    episodes: int
    status: str
    score: float
    poster: str
    session: str
