
from typing import Any, Dict, List, Optional
from langchain_core.prompts import SystemMessagePromptTemplate
import json

DEFAULT_SYSTEM_TEMPLATE = """You have access to the following tools:

{tools}

If using tools , You must respond with a JSON object in a JSON codeblock matching the following schema.

```json
"tool": <name of the selected tool>,
"tool_input": <parameters for the selected tool, matching the tool's JSON schema>
```
Note : Always generate a natural language response accompanied by the corresponding JSON object, if necessary.
"""  # noqa: E501

DEFAULT_RESPONSE_FUNCTION = {
    "name": "__conversational_response",
    "description": (
        "Respond conversationally if no other tools should be called for a given query."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "response": {
                "type": "string",
                "description": "Conversational response to the user.",
            },
        },
        "required": ["response"],
    },
}
def _function(**kwargs: Any,):
    functions = kwargs.get("functions", [])
    tools=kwargs.get("tools", [])


    if "type" not in tools and "function" not in tools:
        functions=tools
        functions = [
            fn for fn in functions 
        ]
        if not functions:
            raise ValueError(
                'If "function_call" is specified, you must also pass a matching \
    function in "functions".'
            )
    elif "tools" in kwargs:
        functions = [
            fn["function"] for fn in tools
        ]
        # del kwargs["function_call"]
    # elif ""
    # elif not functions:
    # functions.append(DEFAULT_RESPONSE_FUNCTION)
    system_message_prompt_template = SystemMessagePromptTemplate.from_template(
        DEFAULT_SYSTEM_TEMPLATE
    )
    system_message = system_message_prompt_template.format(
        tools=json.dumps(functions, indent=2)
    )
    if "functions" in kwargs:
        del kwargs["functions"]
    return system_message.content