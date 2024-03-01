from helpers.config  import *
from helpers.prompts import *
from helpers.provider import *
from helpers.models import model
import re,ast

def streamer(tok):
        completion_timestamp = int(time.time())
        completion_id = ''.join(random.choices(
            'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=28))
        completion_tokens = num_tokens_from_string(tok)

        completion_data = {
            'id': f'chatcmpl-{completion_id}',
            'object': 'chat.completion.chunk',
            'created': completion_timestamp,
            'model': 'gpt-4',
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": completion_tokens,
                "total_tokens": completion_tokens,
            },
            'choices': [
                {
                    'delta': {
                        'role':"assistant",
                        'content':tok
                    },
                    'index': 0,
                    'finish_reason': None
                }
            ]
        }
        return completion_data

def end():
    completion_timestamp = int(time.time())
    completion_id = ''.join(random.choices(
        'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=28))

    end_completion_data = {
        'id': f'chatcmpl-{completion_id}',
        'object': 'chat.completion.chunk',
        'created': completion_timestamp,
        'model': model,
        'provider': g4f.get_last_provider(True),
        'choices': [
            {
                'index': 0,
                'delta': {},
                'finish_reason': 'stop',
            }
        ],
    }
    return end_completion_data


def output(tok):
        completion_timestamp = int(time.time())
        completion_id = ''.join(random.choices(
            'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=28))
        completion_tokens = num_tokens_from_string(tok)

        return {
            'id': 'chatcmpl-%s' % completion_id,
            'object': 'chat.completion',
            'created': completion_timestamp,
            'model': "gpt-4.5-turbo",
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": completion_tokens,
                "total_tokens": completion_tokens,
            },
            'choices': [{
                'message': {
                    'role': 'assistant',
                    'content': tok
                },
                'finish_reason': 'stop',
                'index': 0
            }]
        }

def stream_func(tok,type_tool):
        print("-"*500)
        print(f"streaming {type_tool}")
        completion_timestamp = int(time.time())
        completion_id = ''.join(random.choices(
            'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=28))
        completion_tokens = num_tokens_from_string(tok)
        tool_calls=[]
        regex = r'```json\n(.*?)\n```'
        matches = re.findall(regex, tok, re.DOTALL)
        info_blocks = [match for match in matches]

        for info_block in info_blocks:
            tok=tok.replace(f"```json\n{info_block}\n```",'')

            tool_data=ast.literal_eval(info_block)
            to_add={"arguments":json.dumps(tool_data["tool_input"]),"name":tool_data["tool"]}
            tool_calls.append(to_add)
        if "tools" in type_tool and tool_calls !=[]:
            completion_data = {
                'id': f'chatcmpl-{completion_id}',
                'object': 'chat.completion.chunk',
                'created': completion_timestamp,
                'model': 'gpt-4',
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": completion_tokens,
                    "total_tokens": completion_tokens,
                },
                'choices': [
                    {
                        'delta': {
                            'role':"assistant",
                            'content':None,
                            "tool_calls":tool_calls,
                        },
                        'index': 0,
                        'finish_reason': ""
                    }
                ]
            }
        elif "functions" in type_tool and tool_calls !=[]:
            completion_data = {
                'id': f'chatcmpl-{completion_id}',
                'object': 'chat.completion.chunk',
                'created': completion_timestamp,
                'model': 'gpt-4',
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": completion_tokens,
                    "total_tokens": completion_tokens,
                },
                'choices': [
                    {
                        'delta': {
                            'role':"assistant",
                            'content':"DONE.",
                            "function_call":tool_calls[0],
                        },
                        'index': 0,
                        'finish_reason': "function_call"
                    }
                ]
            }
            print(completion_data)
        else:
            completion_data = {
                'id': f'chatcmpl-{completion_id}',
                'object': 'chat.completion.chunk',
                'created': completion_timestamp,
                'model': model,
                'provider': "gpt-4-0125-preview",
                'choices': [
                    {
                        'index': 0,
                        'delta': {},
                        'finish_reason': 'stop',
                    }
                ],
            }             
        return completion_data
def func_output(tok,type_tool):
        completion_timestamp = int(time.time())
        completion_id = ''.join(random.choices(
            'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=28))
        completion_tokens = num_tokens_from_string(tok)
        tool_calls=[]

        regex = r'```json\n(.*?)\n```'
        matches = re.findall(regex, tok, re.DOTALL)
        info_blocks = [match for match in matches]

        if "tools" in type_tool:
            for info_block in info_blocks:
                tok=tok.replace(f"```json\n{info_block}\n```",'')

                tool_data=ast.literal_eval(info_block)
                to_add={"function":{"arguments":json.dumps(tool_data["tool_input"]),"name":tool_data["tool"]},"id":f"call_3GjyYbPEskNsP67fkjyXj{random.randint(100,999)}","type":"function"}
                tool_calls.append(to_add)
                print(tool_calls)

            return {
                'id': 'chatcmpl-%s' % completion_id,
                'object': 'chat.completion',
                'created': completion_timestamp,
                'model': "gpt-4.5-turbo",
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": completion_tokens,
                    "total_tokens": completion_tokens,
                },
                'choices': [{
                    'message': {
                        'role': 'assistant',
                        'content': tok,
                        "tool_calls":tool_calls
                    },
                    'finish_reason': '',
                    'index': 0
                }]
            }
        elif "functions" in type_tool:
            for info_block in info_blocks:
                # tok=tok.replace(f"```json\n{info_block}\n```",'')

                tool_data=ast.literal_eval(info_block)
                to_add={"name":tool_data["tool"],"arguments":json.dumps(tool_data["tool_input"])}
                tool_calls.append(to_add)
                print(tool_calls)
            return {
                'id': 'chatcmpl-%s' % completion_id,
                'object': 'chat.completion',
                'created': completion_timestamp,
                'model': "gpt-4.5-turbo",
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": completion_tokens,
                    "total_tokens": completion_tokens,
                },
                'choices': [{
                    'message': {
                        'role': 'assistant',
                        'content': tok,
                        "function_call":tool_calls[0]
                    },
                    'finish_reason': 'function_call',
                    'index': 0
                }]
            }
      
               

        # return {
        #     'id': 'chatcmpl-%s' % completion_id,
        #     'object': 'chat.completion',
        #     'created': completion_timestamp,
        #     'model': "gpt-4.5-turbo",
        #     "usage": {
        #         "prompt_tokens": 0,
        #         "completion_tokens": completion_tokens,
        #         "total_tokens": completion_tokens,
        #     },
        #     'choices': [{
        #         'message': {
        #             'role': 'assistant',
        #             'content': tok
        #         },
        #         'finish_reason': 'stop',
        #         'index': 0
        #     }]
        # }       

