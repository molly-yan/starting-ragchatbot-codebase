import json
import sys
import os
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ai_generator import AIGenerator


def make_mock_response(finish_reason, content=None, tool_calls=None):
    response = MagicMock()
    choice = MagicMock()
    choice.finish_reason = finish_reason
    choice.message.content = content
    choice.message.tool_calls = tool_calls if tool_calls is not None else []
    response.choices = [choice]
    return response


def make_tool_call(call_id, name, arguments):
    tc = MagicMock()
    tc.id = call_id
    tc.function.name = name
    tc.function.arguments = json.dumps(arguments)
    return tc


@pytest.fixture
def mock_client():
    return MagicMock()


@pytest.fixture
def gen(mock_client):
    with patch("ai_generator.OpenAI") as MockOpenAI:
        MockOpenAI.return_value = mock_client
        yield AIGenerator("key", "url", "model")


@pytest.fixture
def tools():
    return [{"type": "function", "function": {"name": "search_course_content"}}]


@pytest.fixture
def tool_manager():
    tm = MagicMock()
    tm.execute_tool.return_value = "tool result"
    return tm


def test_no_tool_call(gen, mock_client):
    mock_client.chat.completions.create.return_value = make_mock_response(
        "stop", content="Direct answer"
    )

    result = gen.generate_response("What is Python?")

    assert mock_client.chat.completions.create.call_count == 1
    assert result == "Direct answer"


def test_single_tool_round(gen, mock_client, tools, tool_manager):
    tc = make_tool_call("c1", "search_course_content", {"query": "MCP"})
    mock_client.chat.completions.create.side_effect = [
        make_mock_response("tool_calls", tool_calls=[tc]),
        make_mock_response("stop", content="Final answer"),
    ]

    result = gen.generate_response("Find MCP info", tools=tools, tool_manager=tool_manager)

    assert mock_client.chat.completions.create.call_count == 2
    assert tool_manager.execute_tool.call_count == 1
    assert result == "Final answer"


def test_two_sequential_tool_rounds(gen, mock_client, tools, tool_manager):
    tc1 = make_tool_call("c1", "get_course_outline", {"course_name": "MCP Course"})
    tc2 = make_tool_call("c2", "search_course_content", {"query": "lesson 1 topic"})
    tool_manager.execute_tool.side_effect = ["outline result", "search result"]
    mock_client.chat.completions.create.side_effect = [
        make_mock_response("tool_calls", tool_calls=[tc1]),
        make_mock_response("tool_calls", tool_calls=[tc2]),
        make_mock_response("stop", content="Complete answer"),
    ]

    result = gen.generate_response("Multi-step query", tools=tools, tool_manager=tool_manager)

    assert mock_client.chat.completions.create.call_count == 3
    assert tool_manager.execute_tool.call_count == 2
    third_call_kwargs = mock_client.chat.completions.create.call_args_list[2].kwargs
    assert "tools" not in third_call_kwargs
    assert result == "Complete answer"


def test_tool_exception_handled_gracefully(gen, mock_client, tools, tool_manager):
    tc = make_tool_call("c1", "search_course_content", {"query": "test"})
    tool_manager.execute_tool.side_effect = RuntimeError("VectorStore failure")
    mock_client.chat.completions.create.side_effect = [
        make_mock_response("tool_calls", tool_calls=[tc]),
        make_mock_response("stop", content="Error-aware answer"),
    ]

    result = gen.generate_response("Query", tools=tools, tool_manager=tool_manager)

    assert mock_client.chat.completions.create.call_count == 2
    assert result == "Error-aware answer"


def test_no_tools_arg_excludes_tools_from_api_params(gen, mock_client):
    mock_client.chat.completions.create.return_value = make_mock_response(
        "stop", content="Answer"
    )

    gen.generate_response("General question")

    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert "tools" not in call_kwargs
    assert mock_client.chat.completions.create.call_count == 1
