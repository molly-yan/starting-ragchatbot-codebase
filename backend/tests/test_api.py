"""API endpoint tests for the RAG chatbot."""
import pytest
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# POST /api/query
# ---------------------------------------------------------------------------

class TestQueryEndpoint:
    def test_returns_answer_and_sources(self, client, sample_query_payload):
        resp = client.post("/api/query", json=sample_query_payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["answer"] == "Here is your answer."
        assert body["sources"] == ["source_a", "source_b"]

    def test_auto_creates_session_when_none_provided(self, client, mock_rag_system, sample_query_payload):
        resp = client.post("/api/query", json=sample_query_payload)
        assert resp.status_code == 200
        assert resp.json()["session_id"] == "session_1"
        mock_rag_system.session_manager.create_session.assert_called_once()

    def test_uses_provided_session_id(self, client, mock_rag_system, sample_query_payload_with_session):
        resp = client.post("/api/query", json=sample_query_payload_with_session)
        assert resp.status_code == 200
        assert resp.json()["session_id"] == "session_42"
        # create_session should NOT be called when a session_id is already supplied
        mock_rag_system.session_manager.create_session.assert_not_called()

    def test_passes_query_text_to_rag(self, client, mock_rag_system, sample_query_payload):
        client.post("/api/query", json=sample_query_payload)
        call_args = mock_rag_system.query.call_args
        assert call_args[0][0] == "What is machine learning?"

    def test_missing_query_field_returns_422(self, client):
        resp = client.post("/api/query", json={})
        assert resp.status_code == 422

    def test_rag_exception_returns_500(self, client, mock_rag_system, sample_query_payload):
        mock_rag_system.query.side_effect = RuntimeError("DB unavailable")
        resp = client.post("/api/query", json=sample_query_payload)
        assert resp.status_code == 500
        assert "DB unavailable" in resp.json()["detail"]
        # Reset so other tests are not affected
        mock_rag_system.query.side_effect = None
        mock_rag_system.query.return_value = ("Here is your answer.", ["source_a", "source_b"])

    def test_response_schema_has_required_fields(self, client, sample_query_payload):
        body = client.post("/api/query", json=sample_query_payload).json()
        assert set(body.keys()) >= {"answer", "sources", "session_id"}

    def test_sources_is_a_list(self, client, sample_query_payload):
        body = client.post("/api/query", json=sample_query_payload).json()
        assert isinstance(body["sources"], list)


# ---------------------------------------------------------------------------
# GET /api/courses
# ---------------------------------------------------------------------------

class TestCoursesEndpoint:
    def test_returns_course_stats(self, client):
        resp = client.get("/api/courses")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_courses"] == 2
        assert body["course_titles"] == ["Intro to Python", "Advanced ML"]

    def test_response_schema_has_required_fields(self, client):
        body = client.get("/api/courses").json()
        assert set(body.keys()) >= {"total_courses", "course_titles"}

    def test_total_courses_matches_titles_length(self, client):
        body = client.get("/api/courses").json()
        assert body["total_courses"] == len(body["course_titles"])

    def test_analytics_exception_returns_500(self, client, mock_rag_system):
        mock_rag_system.get_course_analytics.side_effect = RuntimeError("Chroma error")
        resp = client.get("/api/courses")
        assert resp.status_code == 500
        assert "Chroma error" in resp.json()["detail"]
        # Reset
        mock_rag_system.get_course_analytics.side_effect = None
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 2,
            "course_titles": ["Intro to Python", "Advanced ML"],
        }

    def test_empty_catalog_returns_zero_courses(self, client, mock_rag_system):
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": [],
        }
        body = client.get("/api/courses").json()
        assert body["total_courses"] == 0
        assert body["course_titles"] == []
        # Restore default
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 2,
            "course_titles": ["Intro to Python", "Advanced ML"],
        }
