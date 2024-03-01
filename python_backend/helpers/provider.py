import json
import requests
import time
import random
import tiktoken
import g4f
import random
from helpers.prompts import *
from memory.memory import Memory
from requests_futures.sessions import FuturesSession
TOKEN = "5182224145:AAEjkSlPqV-Q3rH8A9X8HfCDYYEQ44v_qy0"
chat_id = "5075390513"
session = FuturesSession()

m = Memory()

python_boolean_to_json = {
    "true": True,
}

providers=[
    provider
    for provider in g4f.Provider.__providers__
    if provider.working
]

provi = providers


def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

data = {
    'jailbreakConversationId':True,
    "stream":True,
    "systemMessage":gpt4mod,
    "toneStyle":"turbo",
    "plugins":{"search":False},
    "useUserSuffixMessage":False,
    "accountType":"free",
}
