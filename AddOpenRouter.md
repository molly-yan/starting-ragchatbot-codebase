⏺ Now I have a complete picture. Here are the 5 files you need to update and exactly what to change in each:

  ---
  Step 1 — pyproject.toml

  Replace the anthropic dependency with openai:

  "openai>=1.0.0",

  Remove: "anthropic==0.58.2",

  Then run:
  uv sync

  ---
  Step 2 — .env

  Replace your key name:
  OPENROUTER_API_KEY=sk-or-v1-...
  
  Remove the ANTHROPIC_API_KEY line.

  ---
  Step 3 — backend/config.py

  Replace the Anthropic fields with OpenRouter fields:

  OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
  OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
  OPENROUTER_MODEL: str = "anthropic/claude-sonnet-4-5"

  Remove: ANTHROPIC_API_KEY and ANTHROPIC_MODEL.

  ---
  Step 4 — backend/search_tools.py
  
  OpenRouter uses the OpenAI tool format, not Anthropic's. In CourseSearchTool.get_tool_definition(), change the returned dict:

  def get_tool_definition(self) -> Dict[str, Any]:
      return {
          "type": "function",
          "function": {
              "name": "search_course_content",
              "description": "Search course materials with smart course name matching and lesson filtering",
              "parameters": {
                  "type": "object",
                  "properties": {
                      "query": {
                          "type": "string",
                          "description": "What to search for in the course content"
                      },
                      "course_name": {
                          "type": "string",
                          "description": "Course title (partial matches work, e.g. 'MCP', 'Introduction')"
                      },
                      "lesson_number": {
                          "type": "integer",
                          "description": "Specific lesson number to search within (e.g. 1, 2, 3)"
                      }
                  },
                  "required": ["query"]
              }
          }
      }

  Key changes: wrap everything under "type": "function" + "function": {...}, and rename input_schema → parameters.

  Also update ToolManager.execute_tool — it currently reads tool_name from tool_def.get("name") but now the name is nested. Fix register_tool:

  def register_tool(self, tool: Tool):
      tool_def = tool.get_tool_definition()
      tool_name = tool_def["function"]["name"]   # was: tool_def.get("name")
      self.tools[tool_name] = tool

  ---
  Step 5 — backend/ai_generator.py

  This is the biggest change. The OpenAI SDK has a different response structure. Replace the entire file:

  import json
  from openai import OpenAI
  from typing import List, Optional, Dict, Any

  class AIGenerator:
      SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials..."""  # keep as-is

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

  Key differences from the Anthropic version:
  - system is now a message in the messages list, not a separate param
  - response.choices[0].finish_reason == "tool_calls" replaces response.stop_reason == "tool_use"
  - Tool args come as a JSON string (json.loads(tool_call.function.arguments)) not a dict
  - Tool results are individual {"role": "tool", ...} messages, not a batched tool_result block

  ---
  Step 6 — backend/rag_system.py
  
  Update the AIGenerator constructor call (line 19) to pass the new params:

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

  Key differences from the Anthropic version:
  - system is now a message in the messages list, not a separate param
  - response.choices[0].finish_reason == "tool_calls" replaces response.stop_reason == "tool_use"
  - Tool args come as a JSON string (json.loads(tool_call.function.arguments)) not a dict
  - Tool results are individual {"role": "tool", ...} messages, not a batched tool_result block

  ---
  Step 6 — backend/rag_system.py

  Update the AIGenerator constructor call (line 19) to pass the new params:

  self.ai_generator = AIGenerator(
      config.OPENROUTER_API_KEY,
      config.OPENROUTER_BASE_URL,
      config.OPENROUTER_MODEL
  )

  ---
  That covers all the changes. The model string anthropic/claude-sonnet-4-5 is OpenRouter's ID for Claude Sonnet — you can browse openrouter.ai/models to pick a different one
  if needed.