#importing part
import json
from datetime import datetime
from openai import OpenAI
import os
from groq import Groq
from langchain.agents import Tool, create_react_agent
from langchain.prompts import PromptTemplate
import os
from flask import Flask

#output format
output = {}
output['process_id'] = "No error found. If not satisfied contact my chat bot"
output['date'] = "No error found. If not satisfied contact my chat bot"
output['timestamp'] = "No error found. If not satisfied contact my chat bot"
output['content'] = "No error found. If not satisfied contact my chat bot"


#class groc
class GroqLLM:
    def __init__(self, client):
        self.client = client

    def __call__(self, messages, model="llama3-8b-8192"):
        response = self.client.chat.completions.create(
            messages=messages,
            model=model
        )
        return response.choices[0].message.content.strip()
    
    def bind(self, stop=None):
        return self
    

#word searching algorithm
def badCharHeuristic(string, size):
    NO_OF_CHARS = 256
    badChar = [-1]*NO_OF_CHARS
    for i in range(size):
        badChar[ord(string[i])] = i
    return badChar

def search(txt, pat):
    m = len(pat)
    n = len(txt)
    badChar = badCharHeuristic(pat, m)
    s = 0
    while(s <= n-m):
        j = m-1
        while j >= 0 and pat[j] == txt[s+j]:
            j -= 1
        if j < 0:
            return True
        else:
            s += max(1, j-badChar[ord(txt[s+j])])
    return False


#converting to JSON
def logToJson(file_path,parent_child_tree):
    log_entries = {}
    l =0

    with open(file_path) as fh:
        headers =['date', 'timestamp', 'project_id', 'status','information']
        for line in fh:
            description = list( line.strip().split(None, 4))
            if description==[]:
                continue
            if (l>0):
                txt_str = description[0]
                format = "%Y-%m-%d"
                try:
                    res = bool(datetime.strptime(txt_str, format))
                except ValueError:
                    if (isinstance(log_entries['log'+str(l-1)]['information'], dict)):
                            log_entries['log'+str(l-1)]['information']['info'] = log_entries['log'+str(l-1)]['information']['info']+line
                    else:
                        log_entries['log'+str(l-1)]['information'] = log_entries['log'+str(l-1)]['information']+line
                    continue
            log_entry = {}
            log_entry['date']=description[0]
            log_entry['timestamp']=description[1]
            log_entry['project_id']=description[2]
            log_entry['status']=description[3]
            if (search(description[4], "Diag")): #To check whether its a Diag log file!
                content_1 = list(description[4].strip().split('\t'))[1]
                content_2 = list( content_1.split('|'))
                log_entry['information'] = {}
                log_entry['information']['child']=content_2[0]
                log_entry['information']['parent']=content_2[1]
                #start of construction of tree
                if log_entry['information']['child'] not in parent_child_tree:
                    parent_child_tree[log_entry['information']['child']] = []
                    parent_child_tree[log_entry['information']['child']].append('log'+str(l))
                else:
                    parent_child_tree[log_entry['information']['child']].append('log'+str(l))
                #end of construction of tree
                log_entry['information']['info']=content_2[2]
                if (len(content_2)>3):
                    log_entry['information']['info']=log_entry['information']['info'] + " | "+content_2[3]
            else:
                log_entry['information']=description[4]

            sno ='log'+str(l)
            log_entries[sno]=log_entry
            l=l+1

    out_file = open("required_format.json", "w")
    json.dump(log_entries, out_file, indent = 5)
    out_file.close()
    return log_entries


#log entry json it text
def jsonToText(log_id,all_entries,parent_child_tree):
    text = " "
    if 'date' in all_entries[log_id]:
        text+="Date :"
        text+=all_entries[log_id]['date']
        text+=','

    if 'timestamp' in all_entries[log_id]:
        text+="Timestamp :"
        text+=all_entries[log_id]['timestamp']
        text+=','
            
    if 'project_id' in all_entries[log_id]:
        text+="Process_id :"
        text+=all_entries[log_id]['project_id']
        text+=','
            
    if 'status' in all_entries[log_id]:
        text+="Status :"
        text+=all_entries[log_id]['status']
        text+=','

    if (parent_child_tree=={}):
        if 'information' in all_entries[log_id]:
            text+="Project Information :"
            text+=all_entries[log_id]['information']

    else:
        text+="Project Information :"
        text+=all_entries[log_id]['information']['info']

    text+= ";"
    return text


#extract previous twenty
def extract20entries(error_number,all_entries,parent_child_tree):
    prompt = ""
    if (error_number<20):
        print("error occured in the beginning of the file!")
    else:
        for error_no in range(error_number-19,error_number):
            prompt+=jsonToText('log'+str(error_no),all_entries,parent_child_tree)
    return prompt


#to find the status of warning or error and then extracting the required text
def extractingByStatus(json_path,parent_child_tree):
    error_entries = {}
    error_no = 0

    with open(json_path, 'r') as file:
        all_entries = json.load(file)

    for key in all_entries:
        if 'status' in all_entries[key]:
            if (all_entries[key]['status']=='Warning' or all_entries[key]['status']=='Error'):
                error_log = key
                #log_no = int(error_log[4:])
                error_entries['Issue'+str(error_no)] = {}
                error_entries['Issue'+str(error_no)]['log_no'] = key
                error_entries['Issue'+str(error_no)]['type'] = all_entries[key]['status']
                error_entries['Issue'+str(error_no)]['info'] = jsonToText(error_log,all_entries,parent_child_tree)
                if (parent_child_tree=={}):
                    error_number = int(error_log[3:])
                    error_entries['Issue'+str(error_no)]['previous_info'] = extract20entries(error_number,all_entries,parent_child_tree) 
                    error_no+=1
                else:
                    error_entries['Issue'+str(error_no)]['child_process_info'] = " "
                    for log_key in parent_child_tree[all_entries[key]['information']['child']]:
                        error_entries['Issue'+str(error_no)]['child_process_info']+=jsonToText(log_key,all_entries,parent_child_tree)
                    error_entries['Issue'+str(error_no)]['parent_process_info'] = " "
                    for log_key in parent_child_tree[all_entries[key]['information']['parent']]:
                        error_entries['Issue'+str(error_no)]['parent_process_info']+=jsonToText(log_key,all_entries,parent_child_tree)

    out_file = open("error_format.json", "w")
    json.dump(error_entries, out_file, indent = 5)
    out_file.close()
    return error_entries


#analysing log
def analyze_log(all_logs,error_logs,parent_child_tree):
    full_log = error_logs['Issue0']
    log_entry = full_log['info']
    type = full_log['type']
    print("Log response")
    print("Log error was caused on : "+all_logs[full_log['log_no']]['date'])
    output['date'] = all_logs[full_log['log_no']]['date']
    print("Log error was caused at : "+all_logs[full_log['log_no']]['timestamp'])
    output['timestamp'] = all_logs[full_log['log_no']]['timestamp']
    print("Process_id error was caused at : "+all_logs[full_log['log_no']]['project_id'])
    output['process_id'] = all_logs[full_log['log_no']]['project_id']
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    groq_llm = GroqLLM(client)
    tools = [
    Tool(
        name="Log Analyzer",
        func=analyze_log,
        description="Analyzes a log entry for errors or warnings."
    )
    ]

    if (parent_child_tree=={}): #no diag file
        previous_log_entry = full_log['previous_info']
        prompt_template = PromptTemplate(
        input_variables=["log_entry", "agent_scratchpad", "tools", "tool_names"],
        template=(
            '''Your task is to analyze the given log text, which usually contains a date, time, process_id, and details related to transportation management.
            The log entry contains {type} in it. Use the log entry and previous log entries provided below and then analyse the error, give the root cause. 
            Also try to give the possible solution to solve the {type}
            Log Entry:{log_entry}
            Previous Log Entries:{previous_log_entry}
            Available tools: {tools}
            Tool names: {tool_names}
            Please summarize your findings clearly without any additional notes.
            Current scratchpad: {agent_scratchpad}

            Provide a concise analysis including:
            1. Analysis of the log file.
            2. Analysis of the {type} caused.
            3. Root cause of the {type}.
            3. Probable solution for the {type}.
            
            Format your response as a clear, well-structured paragraph.
            '''
        )
        )
        prompt = prompt_template.format(
            log_entry=log_entry,
            previous_log_entry = previous_log_entry,
            type = type,
            agent_scratchpad="",  
            tools=", ".join([tool.name for tool in tools]), 
            tool_names=", ".join([tool.name for tool in tools])  
        )
    
    else:   #diag log file
        parent_log_entry = full_log['parent_process_info']
        child_log_entry = full_log['child_process_info']
        prompt_template = PromptTemplate(
        input_variables=["log_entry", "agent_scratchpad", "tools", "tool_names"],
        template=(
            '''Your task is to analyze the given log text, which usually contains a date, time, process_id, and details related to transportation management.
            The log entry contains {type} in it. Use the log entry , parent log entries, sibling log entries provided below and then analyse the error, give the root cause. 
            Also try to give the possible solution to solve the {type}.
            Log Entry:{log_entry}
            Parent Log Entries:{parent_log_entry}
            Sibling Log Entries:{child_log_entry}
            Available tools: {tools}
            Tool names: {tool_names}
            Please summarize your findings clearly without any additional notes.
            Current scratchpad: {agent_scratchpad}
            '''
        )
        )
        prompt = prompt_template.format(
            log_entry=log_entry,
            parent_log_entry = parent_log_entry,
            child_log_entry = child_log_entry,
            type = type,
            agent_scratchpad="",  
            tools=", ".join([tool.name for tool in tools]), 
            tool_names=", ".join([tool.name for tool in tools])  
        )

    agent = create_react_agent(
    llm=groq_llm, 
    prompt=prompt_template,
    tools=tools
    )
    response = groq_llm(messages=[{"role": "user", "content": prompt}])
    return response  


#extracting error where status Warning or Error is not found
def extractingSemiErrors(all_logs,parent_child_tree):
    if (parent_child_tree == {}):
        for key in all_logs:
            if (search(all_logs[key]['information'],"Num Of Order Movements Failed To Plan =") and not(search(all_logs[key]['information'],"Num Of Order Movements Failed To Plan = 0"))):
                error_log = {}
                error_log['Issue0'] = {}
                error_log['Issue0']['log_no'] = key
                error_log['Issue0']['type'] = "Failure"
                error_log['Issue0']['info'] = jsonToText(key,all_logs,parent_child_tree)
                error_number = int(error_log[3:])
                error_log['Issue0']['info'] = extract20entries(error_number,all_logs,parent_child_tree)
                return analyze_log(all_logs,error_log,parent_child_tree)
        
    else:
        for key in all_logs:
            if (search(all_logs[key]['information']['info'],"STATUS=") and not(search(all_logs[key]['information']['info'],"STATUS=1"))):
                error_log = {}
                error_log['Issue0'] = {}
                error_log['Issue0']['log_no'] = key
                error_log['Issue0']['type'] = "Failure"
                error_log['Issue0']['info'] = jsonToText(key,all_logs,parent_child_tree)
                error_log['Issue0']['child_process_info'] = " "
                for log_key in parent_child_tree[all_logs[key]['information']['child']]:
                    error_log['Issue0']['child_process_info']+=jsonToText(log_key,all_logs,parent_child_tree)
                error_log['Issue0']['parent_process_info'] = " "
                for log_key in parent_child_tree[all_logs[key]['information']['parent']]:
                    error_log['Issue0']['parent_process_info']+=jsonToText(log_key,all_logs,parent_child_tree)
                return analyze_log(all_logs,error_log,parent_child_tree)
            
    return "No error found. If not satisfied contact my chat bot"


#main function
def main():
    parent_child_tree =  {} #Also helps in checking type of the file
    file_path = "logFiles/skully.log.bak.2"
    all_logs = logToJson(file_path,parent_child_tree)
    json_path = "required_format.json"
    error_logs = extractingByStatus(json_path,parent_child_tree)  

    if (error_logs!={}):    #log file with status error or debug       
        response = analyze_log(all_logs,error_logs,parent_child_tree)
    else:     
        response = extractingSemiErrors(all_logs,parent_child_tree)
    output['content'] =response

    #print(output)
    print(response)
    #print(parent_child_tree)

    bot = input("What chatbot?")
    if (bot=="Yes"):
        if (error_logs=={}):
            no_of_entries = len(all_logs)
            chatbot_logs = {}
            for i in range(no_of_entries-50,no_of_entries):
                chatbot_logs["log"+str(i)] = all_logs["log"+str(i)]
            out_file = open("chatbot_format.json", "w")
            json.dump(chatbot_logs, out_file, indent = 5)
            out_file.close()
            #shashank function

        else:
            error_num = len(error_logs)-1
            entries = error_logs['Issue'+str(error_num)]['log_no']
            no_of_entries = int(entries[3:])
            if (no_of_entries<51):
                print("Thank you!")
            chatbot_logs = {}
            for i in range(no_of_entries-50,no_of_entries):
                chatbot_logs["log"+str(i)] = all_logs["log"+str(i)]
            out_file = open("chatbot_format.json", "w")
            json.dump(chatbot_logs, out_file, indent = 5)
            out_file.close()
            #shashank function
            os.system("python3 chatbot.py")

        os.system("python3 chatbot.py")


    else:
        print("Thank you!")
        
main()

