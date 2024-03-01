"""
    This example shows how to use the streaming feature with functions.
"""

import json
import os
import sys
from collections.abc import Generator
from typing import Any, Dict, List

import openai

# ------------------------------------------------------------------------------
# # 1. CONFIGURE OPENAI LIBRARY
# Set the OpenAI API key.
# ------------------------------------------------------------------------------
openai.api_base = "http://localhost:1331/v1"

# ------------------------------------------------------------------------------
# 2. DEFINE FUNCTIONS
# Define your functions using JSON. Note that while the API will need functions
# as an array, it's easier to work with them in call_function() as a dict.
# ------------------------------------------------------------------------------
FUNCTIONS = {
    "count_string": {
        "name": "count_string",
        "description": "Counts the number of characters in a string.",
        "parameters": {
            "type": "object",
            "properties": {
                "string_to_count": {
                    "type": "string",
                    "description": "The string whose characters you want to count.",
                },
            },
            "required": ["string_to_count"],
        },
    }
}
FUNCTIONS_FOR_API = list(FUNCTIONS.values())


# ------------------------------------------------------------------------------
# 3. CREATE DEFINED FUNCTIONS
# Create the functions that you've defined in your function array. Note that
# these need to return a string.
# ------------------------------------------------------------------------------
def count_string(string_to_count: str) -> str:
    """Counts the number of characters in a string."""
    return str(len(string_to_count))


# ------------------------------------------------------------------------------
# 4. HANDLE CALLED FUNCTIONS
# Create a function to call functions upon request.
# ------------------------------------------------------------------------------
def call_function(function_name: str, function_arguments: str) -> str:
    """Calls a function and returns the result."""

    # Ensure the function is defined
    if function_name not in FUNCTIONS:
        return "Function not defined."

    # Convert the function arguments from a string to a dict
    function_arguments_dict = json.loads(function_arguments)

    # Ensure the function arguments are valid
    function_parameters = FUNCTIONS[function_name]["parameters"]["properties"]
    for argument in function_arguments_dict:
        if argument not in function_parameters:
            return f"{argument} not defined."

    # Call the function and return the result
    return globals()[function_name](**function_arguments_dict)


# ------------------------------------------------------------------------------
# 5. MANAGE OPENAI RESPONSE
# When using streaming and function calls, you need to act on the response in
# different ways. You may get text or a function call. And you don't get either
# all at once. You also need to execute the function call when streaming is
# complete. This function shows one approach to handling all of this.
# ------------------------------------------------------------------------------
def get_response(messages: List[Dict[str, Any]]) -> Generator[str, None, None]:
    """Gets the response from OpenAI, updates the messages array, yields
    content, and calls functions as needed."""

    # Get the response from OpenAI
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=messages,
            functions=list(FUNCTIONS.values()),
            stream=True,
        )
    except Exception as e:
        yield f"Sorry, there was an error: {e}"
        return

    # Define variables to hold the streaming content and function call
    streaming_content = ""
    function_call = {"name": "", "arguments": ""}

    # Loop through the response chunks
    for chunk in response:
        # Handle errors
        if not "choices" in chunk:
            messages.append(
                {
                    "role": "assistant",
                    "content": "Sorry, there was an error. Please try again.",
                }
            )
            yield "Sorry, there was an error. Please try again."
            break

        # Get the first choice
        msg = chunk["choices"][0]

        # If there's still more to output...
        if "delta" in msg:
            # If it's a function call, save it for later
            if "function_call" in msg["delta"]:
                    if "name" in msg["delta"]["function_call"]:
                        function_call["name"] += msg["delta"]["function_call"]["name"]
                    if "arguments" in msg["delta"]["function_call"]:
                        function_call["arguments"] += msg["delta"]["function_call"][
                            "arguments"
                        ]

            # If it's content, add it to the streaming content and yield it
            elif "content" in msg["delta"]:
                streaming_content += msg["delta"]["content"]
                yield msg["delta"]["content"]

        # If it's the end of the response and it's a text response, update the messages array with it
        if msg["finish_reason"] == "stop":
            messages.append({"role": "assistant", "content": streaming_content})

        # If it's the end of the response and it's a function call, call the function, update the messages array
        # and recursively call get_response() so GPT can respond to the function call output
        elif msg["finish_reason"] == "function_call":
            function_output = call_function(
                function_call["name"], function_call["arguments"]
            )
            messages.append(
                {
                    "role": "function",
                    "content": function_output,
                    "name": function_call["name"],
                }
            )
            yield from get_response(
                messages
            )  # Recursive call so GPT can respond to the function call output


# ------------------------------------------------------------------------------
# 6. USE THE GET_RESPONSE() FUNCTION
# Here's where it all comes together and you can have a conversation with
# streaming output and function calls.
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    # Define an array to hold the messages, and include the system message first
    messages = [
        {
            "role": "system",
            "content": "You are demonstrating streaming with tool calls.",
        },
    ]
    while True:
        # Get the user input
        user_content = input("You: ")

        # Add the user input to the messages array
        messages.append({"role": "user", "content": user_content})

        # Stream the assistant response (note that the get_response() function
        # will automatically append function calls, function call output, and
        # assistant messages to the messages array)
        sys.stdout.write("Assistant: ")
        for content in get_response(messages):
            sys.stdout.write(content)
            sys.stdout.flush()
        sys.stdout.write("\n")