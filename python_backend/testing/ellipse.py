x=[{'role': 'system', 'content': 'You are demonstrating streaming with tool calls.'}, {'role': 'user', 'content': 'Count the number of character in this string : HI! how are you?'}, {'role': 'function', 'content': '16', 'name': 'count_string'}]
if "function" in x[-1]["role"]:
    print(x[-1]["role"])