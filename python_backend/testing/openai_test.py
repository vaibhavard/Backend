import json
from openai import OpenAI
from tenacity import retry, wait_random_exponential, stop_after_attempt
from termcolor import colored  

GPT_MODEL = "gpt-4-turbo"
client = OpenAI(base_url="http://localhost:1331/v1",api_key="shuttle-qyzyg02mup3popd4q1e6")
student_1_description = "David Nguyen is a sophomore majoring in computer science at Stanford University. He is Asian American and has a 3.8 GPA. David is known for his programming skills and is an active member of the university's Robotics Club. He hopes to pursue a career in artificial intelligence after graduating."


tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        },
    }
]
student_description = [student_1_description]
for i in student_description:
    response = client.chat.completions.create(
        model = 'gpt-4-turbo',
        messages = [{"role": "user", "content": "What is the current weather like in Los Angeles California?"}],
        tools = tools,
        tool_choice = 'auto',
        stream=True
    )

    # Loading the response as a JSON object
    for resp in response:
        print(resp)
    # print(json_response)