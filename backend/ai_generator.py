import json
from openai import OpenAI
from typing import List, Optional, Dict, Any

class AIGenerator:
    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to a comprehensive search tool for course information.

Search Tool Usage:
- Use the search tool **only** for questions about specific course content or detailed educational materials
- **One search per query maximum**
- Synthesize search results into accurate, fact-based responses
- If search yields no results, state this clearly without offering alternatives

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without searching
- **Course-specific questions**: Search first, then answer
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, search explanations, or question-type analysis
 - Do not mention "based on the search results"


All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
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
        choice = response.choices[0]

        if choice.finish_reason == "tool_calls" and tool_manager:
            return self._handle_tool_execution(choice.message, messages, tool_manager)

        return choice.message.content

    def _handle_tool_execution(self, assistant_message, messages, tool_manager):
        messages.append(assistant_message)  # add assistant's tool_calls message

        for tool_call in assistant_message.tool_calls:
            args = json.loads(tool_call.function.arguments)
            result = tool_manager.execute_tool(tool_call.function.name, **args)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })

        final_params = {**self.base_params, "messages": messages}
        final_response = self.client.chat.completions.create(**final_params)
        return final_response.choices[0].message.content