import json
from openai import OpenAI
from typing import List, Optional, Dict, Any

class AIGenerator:
    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """You are an AI assistant specialized in course materials and educational content with access to two tools for course information.

Available Tools:
- **search_course_content**: Search for specific course content, explanations, or detailed educational materials. Use for questions like "what does lesson 3 cover?" or "explain the MCP architecture from the course."
- **get_course_outline**: Retrieve the complete outline of a course — its title, link, and full numbered lesson list. Use for questions like "what lessons are in this course?", "show me the course structure", "give me the syllabus", or "what topics does this course cover?"

Tool Usage Rules:
- **Up to two sequential tool calls are allowed per query** — use a second call only when the first result is insufficient or a follow-up lookup is clearly needed. Each round uses one tool.
- Use **search_course_content** for content/material questions
- Use **get_course_outline** for structure/outline/lesson-list questions
- If a tool yields no results, state this clearly without offering alternatives
- Synthesize tool results into accurate, fact-based responses

When responding to an outline query, present:
1. The course title
2. The course link (if available)
3. Each lesson as: Lesson N: <lesson title>

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without searching
- **Course-specific questions**: Use the appropriate tool first, then answer
- **No meta-commentary**: Provide direct answers only — no reasoning process, tool explanations, or question-type analysis
- Do not mention "based on the search results" or "based on the tool output"

All responses must be:
1. **Brief, concise and focused** — get to the point quickly
2. **Educational** — maintain instructional value
3. **Clear** — use accessible language
4. **Example-supported** — include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""
    
    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.base_params = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 800
        }

    def generate_response(self, query, conversation_history=None, tools=None, tool_manager=None):
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history
            else self.SYSTEM_PROMPT
        )

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": query}
        ]

        api_params = {**self.base_params, "messages": messages}
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = "auto"

        response = self.client.chat.completions.create(**api_params)

        for round_num in range(2):
            choice = response.choices[0]

            if choice.finish_reason != "tool_calls" or not tool_manager:
                return choice.message.content

            messages.append(choice.message)
            error_occurred = False

            for tool_call in choice.message.tool_calls:
                try:
                    args = json.loads(tool_call.function.arguments)
                    result = tool_manager.execute_tool(tool_call.function.name, **args)
                except Exception as e:
                    result = f"Tool error: {e}"
                    error_occurred = True
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

            is_last_round = (round_num == 1) or error_occurred
            next_params = {**self.base_params, "messages": messages}
            if not is_last_round and tools:
                next_params["tools"] = tools
                next_params["tool_choice"] = "auto"

            response = self.client.chat.completions.create(**next_params)

            if is_last_round:
                return response.choices[0].message.content

        return response.choices[0].message.content