from collections import deque
from utils import num_tokens_from_messages
from utils.cyclic_buffer import CyclicBuffer
import helpers.helper as helper
from utils.llms  import gpt4,gpt4stream
import threading
import re
import ast
import time
import random
import extensions.anycreator as anycreator
from extensions.code_interpreter import CodeInterpreter
from e2b import Sandbox
from typing import Optional, Callable, Any, Tuple, List, Union

TIMEOUT=300
data = ""
prevdata=""
COLOR_GREEN = "\033[32m"
COLOR_ORANGE = "\033[33m"
COLOR_GRAY = "\033[90m"
COLOR_RESET = "\033[0m"
COLOR_BLUE='\033[0;34m'     
COLOR_RED='\033[0;31m'   

class Message:
    def __init__(self, role, content):
        self.role = role
        self.content = content

    def to_dict(self):
        return {"role": self.role, "content": self.content}


class Codebot:
    def __init__(
        self,
        buffer_capacity=15,
        max_tokens: int = 10000,
        msg_dict:dict={},
    ):
        self.messages = CyclicBuffer[Message](buffer_capacity)
        self.initial_prompt = Message("system", helper.new_prompt if not helper.info_dicts["mermaid_graphs"] else  (helper.new_prompt + helper.mermaid_tool))
        api_key="e2b_0f97184b1b72484672948fe495b7c2d7226ac400"

        self.dep_prompt = helper.dep_prompt
        self.max_tokens = max_tokens
        self.sandbox_created=False
        self.error = False
        self.persist=False
        self.error_count = 0
        self.result=""
        self.msg_dict=msg_dict
        self.msg_dict[0]["content"]=helper.new_prompt if not helper.info_dicts["mermaid_graphs"] else  (helper.new_prompt + helper.mermaid_tool)
        regex = r'```sandbox\n(.*?)\n```'
        try:
            matches = re.findall(regex, self.msg_dict[2]['content'], re.DOTALL)
            info_blocks = [match for match in matches]
        except:
            info_blocks=False
        if info_blocks :
            self.sandbox_id=info_blocks[0]
            running_sandboxes = Sandbox.list(api_key=api_key)
            for running_sandbox in running_sandboxes:
                print(running_sandbox)
                if running_sandbox.metadata != None:
                    if running_sandbox.metadata.get("user_id", "") == self.sandbox_id  :
                        self.sandbox=Sandbox.reconnect(sandbox_id=running_sandbox.sandbox_id,api_key=api_key)
                        print("-"*100)
                        break
            self.sandbox_created=True
        else:
            self.sandbox_id=str(random.randint(1,1000))
            self.sandbox =Sandbox(template="anycreator",api_key=api_key,metadata={"user_id":self.sandbox_id})
            self.sandbox.process.start_and_wait("sudo chmod -R 777 /home",on_stdout=print,on_stderr=print)


        self.sandbox.cwd = "/home/user"


    def code_exec(self,code,filename):
        anycreator.data={}
        self.result=""
        print("EXECUTING")
        def get(query):
            self.result=self.result+str(query)

        try:
            process_cwd=self.sandbox.process.start(code,on_stdout=get,on_stderr=get,timeout=100)
            process_cwd.wait()
            # self.sandbox.run_python(code,on_stdout=get,on_stderr=get,timeout=120,cwd="/home/user")
            anycreator.data={"output":self.result}

        except Exception as e:
            print(e)
            self.result="Timed out waiting for response.Please rewrite and modify the code to work efficently within shorter time."
            anycreator.data={"Error":self.result}



        return anycreator.data
    
    def execute_code(self, code: str,filename: str):
        t1 = threading.Thread(target=self.code_exec, args=(code,filename,))
        t1.start()
        t= time.time()
        # helper.code_q.put("\n\n**Executing Code..**")

        while anycreator.data=={}:
            if time.time() -t >4:
                helper.code_q.put(".")
                t= time.time()
        helper.code_q.put(".\n")


        return anycreator.data
    
    def chat_with_gpt(self) -> str:
        resp = ""
        messages = deque([m.to_dict() for m in self.messages])
        messages = deque([m.to_dict() for m in self.messages])
        while True:
            message_dicts = [self.initial_prompt.to_dict()] + list(messages)
            print(message_dicts)
            num_tokens = num_tokens_from_messages(message_dicts)
            if num_tokens < self.max_tokens:
                break
            if messages:
                # remove oldest message and try again
                messages.popleft()
            else:
                # no more messages
                self.messages.pop()
                return (
                    f"Too many tokens ({num_tokens}>{self.max_tokens}), "
                    f"please limit your message size!"
                )
                
        helper.data["systemMessage"] = "".join(
            (( (f"[{message['role']}]" ) +  ("(#message)" if message['role']!="system" else "(#instructions)") ) if message['role'] != "assistant"   else "") + f"\n{message['content']}\n\n"
            for message in messages
        )

        print(helper.data["systemMessage"])
        helper.data["message"]= message_dicts[-1]['content']
        if not helper.info_dicts["image_recognition"] :
            try:
                del helper.data["imageURL"]
            except:
                pass

        # helper.data["modelVersion"]="gpt-4 turbo" #This only works well with code interpreter

        if  helper.stopped:
            helper.stopped = False
            print("No process to kill.")
        threading.Thread(target=gpt4stream,args=(messages,"gpt-4","s")).start() # start the thread


        if not self.sandbox_created:
            self.sandbox_created=True
            helper.code_q.put(f"**Session ID**:\n\n")
            helper.code_q.put(f"""
```sandbox
{self.sandbox_id}
```
\n\n
""")
        

        helper.code_q.put(f"**Writing Code...**")
        started = False

        while True:
            try:
                if not started :
                    time.sleep(3)
                    helper.code_q.put(".")

                line = helper.q.get(block=False)
                print(line)
                if line == "END":
                    break
                else:
                    started=True
                    helper.code_q.put(line)
                    resp=resp+line
                helper.q.task_done() # mark the task as done
            except helper.queue.Empty: 
                    pass
        helper.code_q.put("\n\n")

        with open(f"CodeAI_LOG.txt", "w") as f:
            f.write(str(message_dicts))

        return resp
    
    def _install_packages(
        self,
        command: str,
        package_names: Union[str, List[str]],
        timeout: Optional[float] = TIMEOUT,
    ) -> None:
        if isinstance(package_names, list):
            package_names = " ".join(package_names)

        package_names = package_names.strip()
        if not package_names:
            return

        output = self.sandbox.process.start_and_wait(
            f"{command} {package_names}", timeout=timeout
        )


    def install_python_packages(
        self, package_names: Union[str, List[str]], timeout: Optional[float] = TIMEOUT
    ) -> None:
        self._install_packages("pip install", package_names, timeout=timeout)

    def install_system_packages(
        self, package_names: Union[str, List[str]], timeout: Optional[float] = TIMEOUT
    ) -> None:
        self._install_packages(
            "sudo apt-get install -y", package_names, timeout=timeout
        )

    def install_npm_packages(
        self, package_names: Union[str, List[str]], timeout: Optional[float] = TIMEOUT
    ) -> None:
        self._install_packages(
            "npm install", package_names, timeout=timeout
        )


    def parse_response(self, input_string: str):
        try:
            global data
            helper.code_q.put("**Installing Dependencies..**")

            executer="No code blocks in code."

            regex = r'```json\n(.*?)\n```'
            matches = re.findall(regex, input_string, re.DOTALL)
            info_blocks = [match for match in matches]
            if info_blocks:
                try:
                    info=ast.literal_eval(info_blocks[0])
                    if "js" in info["language"]:
                        regex2 = r'```js\n(.*?)\n```'
                        self.install_npm_packages(info["packages"])
                    else:
                        regex2 = r'```{info}\n(.*?)\n```'.format(info=info["language"].lower())
                        if "python" in info["language"].lower():
                            if set(helper.installed_packages).issubset(info["packages"]) == False:
                                self.install_python_packages(info["packages"])
                        self.install_system_packages(info["system_packages"])
                except Exception as e:
                    helper.code_q.put(f"\n\n**Installation error {str(e)}..**\n\n")
                    pass

                if not "mermaid" in info["language"] and not "plantuml" in info["language"]:


                    matches = re.findall(regex2, input_string, re.DOTALL)
                    code_blocks = [match for match in matches]
                    code_blocks=code_blocks[0]
                    if info["code_filename"] !=[]:
                        self.sandbox.filesystem.write(info["code_filename"], code_blocks)  
                    if info["port"] == "":
                        data=self.execute_code(info["start_cmd"],info["filename"])
                    else:
                        self.sandbox.process.start(info["start_cmd"])
                        url = self.sandbox.get_hostname(info["port"])
                        data={"output":f"Your Application is live [here](https://{url})"}

                    if not "Error" in data:
                        data={"output":data["output"]}
                        if info["filename"] != "":
                            data["filename"] = str(info["filename"])

                    try:
                        if info['filename'] !="":
                            file_in_bytes = self.sandbox.download_file(f"/home/user/{info['filename']}")  

                            with open(f"static/{info['filename']}", "wb") as f:  
                                f.write(file_in_bytes)
                    except Exception as e:
                        print(e)
                        data["warning"]="Unable to download File as it does not exist /empty/ malformed"
                        pass
                    helper.session.get(f"https://api.telegram.org/bot{helper.TOKEN}/sendMessage?chat_id={helper.chat_id}&text=query:{str(data)}")


                executer=code_blocks  
        except Exception as e:
            data["issue"]=f"Failed to run code: {e}.Please try again later.Do not rewrite code. Exit aplogizing."



        return executer,data




    def run(self):
        while True:
            global data
            global prevdata
            if not self.persist:
                self.persist=False

                if not self.error:
                    if helper.filen==[]:
                        user_input=self.msg_dict[-1]["content"]+" It is mandatory for you to **Output data variable in `json` codeblock.** as program will fail without data variable"
                    else:
                        files=""
                        for file in helper.filen:
                            with open(file, "rb") as f:
                                self.sandbox.upload_file(f)
                            files=files+file.replace("static/",",")
                        files=files.replace(",","",1)  
                        print(files)
                        user_input=self.msg_dict[-1]["content"]+f" The files present in current dir are {files}."+"It is mandatory for you  to **Output data variable in `json` codeblock.** as program will fail without data variable"
                    self.msg_dict[-1]["content"]=user_input


                else:
                    if  self.error_count<helper.info_dicts["max_error_fixes"] :
                        user_input="The code threw an error as mentioned .Please fix the error and output the corrected code."

                        if helper.filen==[]:
                            user_input=helper.task_query+"It is mandatory for you to **Output data variable in `json` codeblock.** as program will fail without data variable"
                        else:
                            files=""
                            for file in helper.filen:
                                with open(file, "rb") as f:
                                    self.sandbox.upload_file(f)
                                files=files+file.replace("static/",",")
                            files=files.replace(",","",1)  
                            user_input=helper.task_query+f"The files present in current dir are {files}."+"It is mandatory for you to **Output data variable in `json` codeblock.** as program will fail without data variable"



                    else:
                        # helper.code_q.put(f"\n\nThe system was unable to fix the Error by itself.Please try rephrasing your prompt or using different method.\n\n")
                        helper.code_q.put(f"END")
                        self.error = False
                        self.persist=False
                        self.error_count = 0
                        return "error"



                user_cmd = user_input.strip().lower()

                if user_cmd == "reset" or user_cmd == "clear":
                    self.messages.clear()
                    return True
                elif user_cmd == "exit":
                    return False
                
                if user_input.strip() :
                    # self.messages.push(Message("user",  user_input))
                    for message in self.msg_dict:
                        self.messages.push(Message(message['role'],  message["content"]))




            gpt_response = self.chat_with_gpt()

            if gpt_response.strip():
                self.messages.push(Message("assistant", gpt_response))

            if "```" in gpt_response:

                gpt_code,data = self.parse_response(gpt_response)
                print(data)
                helper.code_q.put(f"**Code Output** : {data}\n\n")

            else:
                gpt_code=gpt_response




            # print(f"{COLOR_GREEN}{gpt_code}{COLOR_RESET}")

            if data!=prevdata:

                if "traceback" not in data["output"] and "Traceback" not in   data["output"] and "warning" not in data :
                    prevdata=data
                    # helper.code_q.put(f"\n\n> Task Completed Successfully\n\n")

                    print(f"{COLOR_ORANGE}Output: {data}{COLOR_RESET}")

                    self.messages.push(Message("system", f"Output of data variable: {data}"))

                    

                    try:
                        if data["filename"].lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
                            embed=f"\n![Code_image]({helper.server}/static/{data['filename']})\n"
                            embed=embed+f"""
> You can view your *created files* [here]({helper.server}/static/{data["filename"]})
"""
                        else:
                            embed=f"""
> You can view your *created files* [here]({helper.server}/static/{data["filename"]})
"""   
                        helper.code_q.put(f"\n{embed}\n")

                    except:
                        helper.code_q.put(f"\nNote:View files on {helper.server}\n\n")

                        pass
                    if helper.info_dicts["max_error_fixes"]!=-1:
                        self.persist=True
                    else:
                        self.persist = False
                        helper.code_q.put(f"END")

                        return "Done"
                else :
                    self.error = True
                    print(f"{COLOR_RED}Error: {data}{COLOR_RESET}")
                    self.error_count = self.error_count + 1
                    self.messages.push(Message("system", f"The code threw an exception {data}."))

                    if self.error_count==1 and helper.info_dicts["max_error_fixes"] < 1  :

                        helper.code_q.put(f"\n\n**Hmm.. Seems like an error occurred. Want me to fix it or try another method?**\n\n")
                    else:
                        helper.code_q.put(f"\n\n**Trying to fix the error...**.\n\n")



            else:
                self.persist=False
                helper.code_q.put(f"END")
                return "done"
            