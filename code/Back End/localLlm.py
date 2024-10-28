from openai import OpenAI
from langchain.agents import Tool, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.schema import SystemMessage
from langchain_openai import OpenAI




prompt_template = PromptTemplate(
input_variables=["log_entry", "agent_scratchpad", "tools", "tool_names"],
template=(
    '''Your task is to analyze the given log text, which contains details related to errors or warnings in a transportation management system. 
    Focus on identifying any error messages, warnings, timeouts, or exceptions. Summarize the key issues from the log, specifying the exact type of error or warning if present. 
    If the log mentions a timeout, explain the possible causes.

    Log Entry:
    {log_entry}

    Available tools: {tools}

    Tool names: {tool_names}

    Current scratchpad: {agent_scratchpad}
    '''
  )
)


#log analyser
def analyze_log(log_entry):
 
  prompt = prompt_template.format(
      log_entry=log_entry,
      agent_scratchpad="",  # Placeholder for the scratchpad
      tools=tools,  # Joining tool names for the prompt
      tool_names=", ".join([tool.name for tool in tools])  # Joining tool names for the prompt
  )
    
    
  calling_llm(message=[
      {"role": "system", "content": "Always answer technically."},
      {"role": "user", "content": prompt}
    ])




agent_scratchpad = ""
tools = [
  Tool(
      name="Log Analyzer",
      func=analyze_log,
      description="Analyzes a log entry for errors or warnings."
  )
]


# Initialize the LLM client
llm = OpenAI(
    model="TheBloke/Mistral-7B-Instruct-v0.1-GGUF",
    base_url="http://localhost:1234/v1", 
    api_key="lm-studio"
)

# Create the agent with the actual LLM instance
agent = create_react_agent(
    llm=llm,
    prompt=prompt_template,
    tools=tools
)


# to call llm
def calling_llm(message):
  completion = llm.generate(
      model="TheBloke/Mistral-7B-Instruct-v0.1-GGUF",
      prompts=message,
      temperature=0,
  )
  print("HIIIII")
  print(completion)
  print("HIIIII")

analyze_log("what is the evaporation")

