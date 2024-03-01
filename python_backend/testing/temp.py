from typing import Optional, List, Mapping, Any
from langchain.llms.base import LLM
import g4f
from g4f import Provider

class EducationalLLM(LLM):
    
    @property
    def _llm_type(self) -> str:
        return "custom"

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        x=g4f.ChatCompletion.create(provider=Provider.Liaobots	, messages=[{"role": "user", "content": prompt}],model="gpt-4")
        print(x)
        return x
        

llm = EducationalLLM()
 
from langchain.prompts import PromptTemplate

prompt = PromptTemplate(
    input_variables=["product"],
    template="What is a good name for a company that makes {product}? Just tell one and only the name",
)

from langchain.chains import LLMChain
chain = LLMChain(llm=llm, prompt=prompt)

from langchain_experimental.llms.ollama_functions import OllamaFunctions
from langchain_community.chat_models import ChatOllama

model = OllamaFunctions(model="mistral")


model = model.bind(
    functions=[
        {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, " "e.g. San Francisco, CA",
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                    },
                },
                "required": ["location"],
            },
        }
    ],
    function_call={"name": "get_current_weather"},
)
from langchain.schema import HumanMessage

x=model.invoke("what is the weather in Boston?")
print(x)

{
"language": "mermaid",
"packages": [],
"system_packages": [],
"start_cmd": "",
"filename": "",
"code_filename": "",
"port": "",
}