message = "List all the specs of the os"
from interpreter import interpreter
interpreter.llm.model="openai/gpt-4-0125-preview"
interpreter.auto_run = True
interpreter.llm.supports_functions=True
interpreter.llm.api_base="https://opengpt-4ik5.onrender.com/v1"
# interpreter.verbose=True
interpreter.system_message += """
[Important]:Always Write **all code** using tools and not directly.
"""
interpreter.chat()
