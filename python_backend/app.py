import threading
from flask import Flask, url_for, redirect
from flask import request as req
from flask_cors import CORS
import helpers.helper as helper
from helpers.provider import *
from transformers import AutoTokenizer
import extensions.extensions
from utils.llms import gpt4,gpt4stream,get_providers,summaries
app = Flask(__name__)
CORS(app)
import queue
from utils.functions import allocate,clear,clear2
from extensions.codebot import Codebot
from werkzeug.utils import secure_filename
import os
from PIL import Image

app.config['UPLOAD_FOLDER'] = "static"

@app.route("/v1/chat/completions", methods=['POST'])
@app.route("/chat/completions", methods=['POST'])
def chat_completions2():
    helper.stopped=True
    streaming = req.json.get('stream', False)
    model = req.json.get('model', 'gpt-4-turbo')
    messages = req.json.get('messages')
    api_keys = req.headers.get('Authorization').replace('Bearer ', '')
    functions = req.json.get('functions')
    tools = req.json.get('tools')
    print(functions)
    if functions!=None:

        allocate(messages,helper.data, m.get_data('uploaded_image'),m.get_data('context'),api_keys,model,functions)
    elif tools!=None:
        allocate(messages,helper.data, m.get_data('uploaded_image'),m.get_data('context'),api_keys,model,tools)
    else:
        allocate(messages,helper.data, m.get_data('uploaded_image'),m.get_data('context'),api_keys,model,[])

    t = time.time()

    def stream_response(messages,model,api_keys="",functions=[],tools=[]):
        helper.q = queue.Queue() # create a queue to store the response lines

        if  helper.stopped:
            helper.stopped = False
            print("No process to kill.")
        text=""

        threading.Thread(target=gpt4stream,args=(messages,model,api_keys)).start() # start the thread
        
        started=False
        while True: # loop until the queue is empty
            try:
                if 9>time.time()-t>7 and not started and  "imageURL" in helper.data:
                    yield 'data: %s\n\n' % json.dumps(helper.streamer("> Analysing this Image🖼️"), separators=(',' ':'))
                    time.sleep(2)
                elif 15>time.time()-t>13 and not started :
                    yield 'data: %s\n\n' % json.dumps(helper.streamer("> Please wait"), separators=(',' ':'))
                    time.sleep(2)
                elif time.time()-t>15 and not started :
                    yield 'data: %s\n\n' % json.dumps(helper.streamer("."), separators=(',' ':'))
                    time.sleep(1)
                elif time.time()-t>15 and not started and  m.get_data('uploaded_image')=="":
                    yield 'data: %s\n\n' % json.dumps(helper.streamer("\n\n**Trying to contact server again**\n\n"), separators=(',' ':'))
                    time.sleep(1)
                if time.time()-t>100 and not started:
                    yield 'data: %s\n\n' % json.dumps(helper.streamer("Timed out"), separators=(',' ':'))
                    break

                line = helper.q.get(block=False)
                text=text+line
                if line == "END":
                    if functions !=None:
                        yield f'data: {json.dumps(helper.stream_func(text,"functions"))}\n\n'
                    elif tools !=None:
                        yield f'data: {json.dumps(helper.stream_func(text,"tools"))}\n\n'
                    else:
                        yield f'data: {json.dumps(helper.end())}\n\n'
                    break
                if not started:
                    started = True
                    yield 'data: %s\n\n' % json.dumps(helper.streamer("\n\n"), separators=(',' ':'))

                yield 'data: %s\n\n' % json.dumps(helper.streamer(line), separators=(',' ':'))

                helper.q.task_done() # mark the task as done


            except helper.queue.Empty: 
                pass
            except Exception as e:
                print(e)
    def contextgen(messages):
        helper.q = queue.Queue() # create a queue to store the response lines

        if  helper.stopped:
            helper.stopped = False
            print("No process to kill.")

        threading.Thread(target=summaries,args=(helper.data["message"],)).start() # start the thread
        
        started=False
        while True: # loop until the queue is empty
            try:
                if 11>time.time()-t>10 and not started :
                    yield "WAIT"
                    time.sleep(1)  
                elif 4>time.time()-t>1 and not started :
                    yield 'data: %s\n\n' % json.dumps(helper.streamer("> Please wait while your text is being processed"), separators=(',' ':'))
                    time.sleep(3)
                elif time.time()-t>9 and not started :
                    yield 'data: %s\n\n' % json.dumps(helper.streamer("."), separators=(',' ':'))
                    time.sleep(1)
                if time.time()-t>100 and not started:
                    yield 'data: %s\n\n' % json.dumps(helper.streamer("Timed out"), separators=(',' ':'))
                    break

                line = helper.q.get(block=False)
                if line == "END":
                    break
                if not started:
                    started = True
                    yield 'data: %s\n\n' % json.dumps(helper.streamer("\n\n"), separators=(',' ':'))

                yield 'data: %s\n\n' % json.dumps(helper.streamer(line), separators=(',' ':'))

                helper.q.task_done() # mark the task as done


            except helper.queue.Empty: 
                pass
            except Exception as e:
                print(e)

    def aigen(model):
        helper.code_q = queue.Queue() # create a queue to store the response lines


        threading.Thread(target=codebot.run).start() # start the thread
        
        started=False
        while True: # loop until the queue is empty
            try:
                if 11>time.time()-t>10 and not started :
                    yield "WAIT"
                    time.sleep(1)  
                if 11>time.time()-t>10 and not started :
                    yield 'data: %s\n\n' % json.dumps(helper.streamer("> Your task is being processed"), separators=(',' ':'))
                    time.sleep(2)
                elif time.time()-t>11 and not started :
                    yield 'data: %s\n\n' % json.dumps(helper.streamer("."), separators=(',' ':'))
                    time.sleep(1)
                if time.time()-t>100 and not started:
                    yield 'data: %s\n\n' % json.dumps(helper.streamer("Timed out"), separators=(',' ':'))
                    break

                line = helper.code_q.get(block=False)
                if line == "END":
                    break
                if not started:
                    started = True
                    yield 'data: %s\n\n' % json.dumps(helper.streamer("\n\n"), separators=(',' ':'))

                yield 'data: %s\n\n' % json.dumps(helper.streamer(line), separators=(',' ':'))

                helper.code_q.task_done() # mark the task as done


            except helper.queue.Empty: 
                pass
            except Exception as e:
                print(e)


    
    if "/log" in helper.data["message"] and streaming  :
        return 'data: %s\n\n' % json.dumps(helper.streamer(str(data)), separators=(',' ':'))


    elif "/gethelp" in helper.data["message"]  and streaming :
        return 'data: %s\n\n' % json.dumps(helper.streamer(helper.about), separators=(',' ':'))
    
    
    if "/getproviders" in helper.data["message"] and streaming :
        return 'data: %s\n\n' % json.dumps(helper.streamer(get_providers()), separators=(',' ':'))
    
    if "/mindmap" in helper.data["message"] or "/branchchart" in helper.data["message"] or "/timeline" in helper.data["message"] and streaming :
        return app.response_class(extensions.extensions.grapher(helper.data["message"],model), mimetype='text/event-stream')
    
    elif "/flowchart" in helper.data["message"] or "/complexchart" in helper.data["message"] or  "/linechart" in helper.data["message"] and streaming:
        print(f"----{model}--")
        if "gpt-3" in model:
            if "/flowchart" in  helper.data["message"]:
                return app.response_class(stream_response([{"role": "system", "content": f"{flowchat}"},{"role": "user", "content": f"{data['message'].replace('/flowchart','')}"}],"gpt-3"), mimetype='text/event-stream')
            if "/complexchart" in  helper.data["message"]:
                return app.response_class(stream_response([{"role": "system", "content": f"{complexchat}"},{"role": "user", "content": f"{data['message'].replace('/complexchart','')}"}],"gpt-3"), mimetype='text/event-stream')
            if "/linechart" in  helper.data["message"]:
                return app.response_class(stream_response([{"role": "system", "content": f"{linechat}"},{"role": "user", "content": f"{data['message'].replace('/linechat','')}"}],"gpt-3"), mimetype='text/event-stream')
        elif "gpt-4" in model:

            if "/flowchart" in  helper.data["message"]:
                helper.data["message"]=helper.data["message"].replace("/flowchart","")
                helper.data["systemMessage"]=mermprompt.format(instructions=flowchat)
            if "/complexchart" in  helper.data["message"]:
                helper.data["message"]=helper.data["message"].replace("/complexchart","")
                helper.data["systemMessage"]=mermprompt.format(instructions=complexchat)

            if "/linechart" in  helper.data["message"]:
                helper.data["message"]=helper.data["message"].replace("/linechart","")
                helper.data["systemMessage"]=mermprompt.format(instructions=linechat)

            return app.response_class(stream_response(messages,"gpt-4"), mimetype='text/event-stream')




    if not streaming and "AI conversation titles assistant" in messages[0]["content"]:
        print("USING GPT_3 CONVERSATION TITLE")
        k=gpt4(messages,"Bard")
        return helper.output(k)

    elif not streaming :
        if functions != None :
            k=gpt4(messages,model)
            return helper.func_output(k,"functions")
        elif tools!=None:

            k=gpt4(messages,model)
            return helper.func_output(k,"tools")

        else:

            print("USING GPT_4 NO STREAM")
            print(model)

            k=gpt4(messages,model)
            return helper.output(k)
    if streaming and "AI conversation titles assistant" in messages[0]["content"] and model!="gpt-4-LargeTextSummariser":
        return app.response_class(stream_response(messages,"Bard",api_keys), mimetype='text/event-stream')


    elif  streaming  : 
        return app.response_class(stream_response(messages,model,api_keys,functions,tools), mimetype='text/event-stream')
    elif streaming and( "/aigen" in helper.data["message"]  or messages[0]["content"] == helper.new_prompt) :
        codebot=Codebot(msg_dict=messages)
        return app.response_class(aigen(model), mimetype='text/event-stream')
    # and "/aigen" not in helper.data["message"] and  messages[0]["content"] != helper.new_prompt and model!="gpt-4-LargeTextSummariser"
    if model =="gpt-4-LargeTextSummariser" and streaming:
        return app.response_class(contextgen(messages), mimetype='text/event-stream')



@app.route('/context', methods=['POST'])
def my_form_post():
    text = req.form['text']
    try:
        helper.filen=helper.filen+[f"static/{secure_filename(req.form['filename'])}"]
    except:
        pass

    if text=="image":
        try:
            link= f"{helper.server}/static/{req.form['filename']}"
            m.update_data('uploaded_image',link)
            m.save()        
            print(link)
            return "[Image Uploaded]"
        except:
            pass
    return "[File added]"

@app.route('/context')
def my_form():
    return '''
<form method="POST">
    <textarea name="text"></textarea>
    <input type="submit">
</form>
'''

@app.route('/upload', methods=['GET','POST'])
def index():
 
    # If a post method then handle file upload
    if req.method == 'POST':
 
        if 'file' not in req.files:
            return redirect('/')
 
        file = req.files['file']
 
 
        if file :
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            if ("camera" in file.filename or "capture" in file.filename or "IMG" in file.filename or "Screenshot"  in file.filename) :
                img=Image.open(f"static/{filename}")
                img.thumbnail((512, 512),Image.Resampling.LANCZOS)

                img.save(f"static/{filename}")

            return filename
 
 
    # Get Files in the directory and create list items to be displayed to the user
    file_list = ''
    for f in os.listdir(app.config['UPLOAD_FOLDER']):
        # Create link html
        link = url_for("static", filename=f) 
        file_list = file_list + '<li><a href="%s">%s</a></li>' % (link, f)
 
    # Format return HTML - allow file upload and list all available files
    return_html = '''
    <!doctype html>
    <title>Upload File</title>
    <h1>Upload File</h1>
    <form method=post enctype=multipart/form-data>
            <input type=file name=file><br>
            <input type=submit value=Upload>
    </form>
    <hr>
    <h1>Files</h1>
    <ol>%s</ol>
    ''' % file_list
 
    return return_html



def get_embedding(input_text, token):
    huggingface_token = helper.huggingface_token
    embedding_model = 'sentence-transformers/all-mpnet-base-v2'
    max_token_length = 500

    # Load the tokenizer for the 'all-mpnet-base-v2' model
    tokenizer = AutoTokenizer.from_pretrained(embedding_model)
    # Tokenize the text and split the tokens into chunks of 500 tokens each
    tokens = tokenizer.tokenize(input_text)
    token_chunks = [tokens[i:i + max_token_length]
                    for i in range(0, len(tokens), max_token_length)]

    # Initialize an empty list
    embeddings = []

    # Create embeddings for each chunk
    for chunk in token_chunks:
        # Convert the chunk tokens back to text
        chunk_text = tokenizer.convert_tokens_to_string(chunk)

        # Use the Hugging Face API to get embeddings for the chunk
        api_url = f'https://api-inference.huggingface.co/pipeline/feature-extraction/{embedding_model}'
        headers = {'Authorization': f'Bearer {huggingface_token}'}
        chunk_text = chunk_text.replace('\n', ' ')

        # Make a POST request to get the chunk's embedding
        response = requests.post(api_url, headers=headers, json={
                                 'inputs': chunk_text, 'options': {'wait_for_model': True}})

        # Parse the response and extract the embedding
        chunk_embedding = response.json()
        # Append the embedding to the list
        embeddings.append(chunk_embedding)

    # averaging all the embeddings
    # this isn't very effective
    # someone a better idea?
    num_embeddings = len(embeddings)
    average_embedding = [sum(x) / num_embeddings for x in zip(*embeddings)]
    embedding = average_embedding
    return embedding


@app.route('/embeddings', methods=['POST'])
def embeddings():
    input_text_list = req.get_json().get('input')
    input_text      = ' '.join(map(str, input_text_list))
    token           = req.headers.get('Authorization').replace('Bearer ', '')
    embedding       = get_embedding(input_text, token)
    
    return {
        'data': [
            {
                'embedding': embedding,
                'index': 0,
                'object': 'embedding'
            }
        ],
        'model': 'text-embedding-ada-002',
        'object': 'list',
        'usage': {
            'prompt_tokens': None,
            'total_tokens': None
        }
    }

@app.route('/')
def yellow_name():
   return f'Server 1 is OK and server 2 check: {helper.server}'

@app.route('/clear_all')
def clear_all():
    m.update_data('uploaded_image', "")
    m.update_data('context', "")
    m.save() 
    return str(clear2())


@app.route("/v1/models")
def models():
    print("Models")
    return helper.model



if __name__ == '__main__':
    config = {
        'host': 'localhost',
        'port': 1331,
        'debug': True,
    }

    app.run(**config)