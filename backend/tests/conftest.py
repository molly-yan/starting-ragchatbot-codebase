import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Shared mock factories
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_rag_system():
    """RAGSystem with all heavy dependencies mocked out."""
    rag = MagicMock()
    rag.session_manager.create_session.return_value = "session_1"
    rag.query.return_value = ("Here is your answer.", ["source_a", "source_b"])
    rag.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Intro to Python", "Advanced ML"],
    }
    return rag


@pytest.fixture()
def test_app(mock_rag_system):
    """
    Minimal FastAPI app built from the same route handlers as app.py but
    without the static-file mount that requires ../frontend to exist.
    """
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from typing import List, Optional
    from pydantic import BaseModel

    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class QueryRequest(BaseModel):
        query: str
        session_id: Optional[str] = None

    class QueryResponse(BaseModel):
        answer: str
        sources: List[str]
        session_id: str

    class CourseStats(BaseModel):
        total_courses: int
        course_titles: List[str]

    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        try:
            session_id = request.session_id or mock_rag_system.session_manager.create_session()
            answer, sources = mock_rag_system.query(request.query, session_id)
            return QueryResponse(answer=answer, sources=sources, session_id=session_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        try:
            analytics = mock_rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"],
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app


@pytest.fixture()
def client(test_app):
    """Synchronous TestClient wrapping the test app."""
    return TestClient(test_app)


# ---------------------------------------------------------------------------
# Reusable test-data helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_query_payload():
    return {"query": "What is machine learning?"}


@pytest.fixture()
def sample_query_payload_with_session():
    return {"query": "Tell me more.", "session_id": "session_42"}
