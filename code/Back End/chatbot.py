import json
import os
import uuid
from typing import List, TypedDict
from langchain_groq import ChatGroq
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langchain_core.documents import Document
from langchain_chroma import Chroma

# Set environment variables
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Initialize components
print("\n=== Initializing System ===")
embed_model = FastEmbedEmbeddings(model_name="BAAI/bge-base-en-v1.5")
llm = ChatGroq(
    temperature=0.2,
    model_name="Llama3-70b-8192",
    api_key=os.environ.get("GROQ_API_KEY"),
    max_tokens=1000,
)
os.environ['TAVILY_API_KEY'] = os.environ.get("TAVILY_API_KEY")
web_search_tool = TavilySearchResults(k=3)

class GraphState(TypedDict):
    question: str
    logs: List[Document]
    web_results: str
    analysis: str
    retry_count: int
    question_type: str

def load_json_file(file_path: str):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data
    except Exception as e:
        print(f"Error loading JSON file: {str(e)}")
        return None

def initialize_vectorstore(json_data: dict):
    texts = []
    metadatas = []
    
    try:
        for key, entry in json_data.items():
            if isinstance(entry['information'], dict):
                text = (
                    f"Log Entry ID: {key}\n"
                    f"Date: {entry['date']}\n"
                    f"Time: {entry['timestamp']}\n"
                    f"Status: {entry['status']}\n"
                    f"Information: {entry['information']['info']}"
                )
                metadata = {"type": "diagnostic", "status": entry['status']}
            else:
                text = (
                    f"Log Entry ID: {key}\n"
                    f"Date: {entry['date']}\n"
                    f"Time: {entry['timestamp']}\n"
                    f"Status: {entry['status']}\n"
                    f"Information: {entry['information']}"
                )
                metadata = {"type": "regular", "status": entry['status']}
            
            texts.append(text)
            metadatas.append(metadata)
        
        vectorstore = Chroma(embedding_function=embed_model)
        vectorstore.add_texts(
            texts=texts,
            metadatas=metadatas,
            ids=[str(uuid.uuid4()) for _ in texts]
        )
        return vectorstore.as_retriever()
    except Exception as e:
        print(f"Error creating vector store: {str(e)}")
        return None

def determine_question_type(logs: List[Document], question: str) -> str:
    router_prompt = """You are an expert at analyzing questions.
    Determine if this question requires log analysis or is a general knowledge question.
    
    Question: {question}
    
    Respond with ONLY ONE of these words:
    - "logs" - if asking about system logs, errors, issues, or specific events in the logs
    - "general" - if asking about general knowledge, definitions, or concepts not requiring log analysis
    """
    
    try:
        messages = [
            SystemMessage(content=router_prompt),
            HumanMessage(content=router_prompt.format(question=question))
        ]
        
        response = llm.invoke(messages).content.strip().lower()
        return response
    except Exception as e:
        return "general"

def process_general_query(question: str, web_results: str) -> str:
    general_query_prompt = """You are a knowledgeable expert.
    Provide a clear and concise answer to the question using the web search results.
    
    Question: {question}
    
    Web Search Results:
    1.The question is not related to the given file but here is the result produced from the web search(inlcude this line in the answer).
    {web_results}
    
    Provide your response in a single, well-formatted paragraph.
    If the question is very basic (like asking for a definition or full form),
    provide just the direct answer without unnecessary elaboration."""
    
    messages = [
        SystemMessage(content=general_query_prompt),
        HumanMessage(content=general_query_prompt.format(
            question=question,
            web_results=web_results
        ))
    ]
    
    return llm.invoke(messages).content

def analyze_logs(logs: List[Document], question: str) -> str:
    log_analysis_prompt = """You are an expert at analyzing transportation management system logs.
    
    
    Question: {question}
    
    Log Entries:
    {logs}
    
    Provide a concise analysis including:
    1. Answer for the {question}.
    2.{log_type} log file.
    
    Format your response as a clear, well-structured paragraph."""
    
    # Add this line to check the metadata of first log entry
    log_type = logs[0].metadata.get('type', 'regular') if logs else 'regular'
    
    log_content = "\n".join([doc.page_content for doc in logs])
    
    messages = [
        SystemMessage(content=log_analysis_prompt),
        HumanMessage(content=log_analysis_prompt.format(
            question=question,
            logs=log_content,
            log_type=log_type  # Add this parameter
        ))
    ]
    return llm.invoke(messages).content

def retrieve_logs(state: GraphState) -> GraphState:
    try:
        documents = retriever.invoke(state["question"])
        state["logs"] = documents
        state["question_type"] = determine_question_type(documents, state["question"])
    except Exception as e:
        state["logs"] = []
        state["question_type"] = "general"
    return state

def perform_web_search(state: GraphState) -> GraphState:
    if state["question_type"] == "general":
        try:
            results = web_search_tool.invoke({"query": state["question"]})
            state["web_results"] = "\n".join(result["content"] for result in results)
        except Exception as e:
            state["web_results"] = ""
    return state

def analyze_data(state: GraphState) -> GraphState:
    try:
        if state["question_type"] == "logs":
            state["analysis"] = analyze_logs(state["logs"], state["question"])
        else:
            state["analysis"] = process_general_query(state["question"], state["web_results"])
        
    except Exception as e:
        state["analysis"] = f"Error generating analysis: {str(e)}"
        state["retry_count"] += 1
    
    return state

def validate_response(state: GraphState) -> str:
    if state["analysis"].startswith("Error generating analysis") and state["retry_count"] < 2:
        return "retry"
    return "end"

def create_workflow():
    workflow = StateGraph(GraphState)
    
    workflow.add_node("retrieve", retrieve_logs)
    workflow.add_node("websearch", perform_web_search)
    workflow.add_node("analyze", analyze_data)
    
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "websearch")
    workflow.add_edge("websearch", "analyze")
    
    workflow.add_conditional_edges(
        "analyze",
        validate_response,
        {
            "retry": "analyze",
            "end": END
        }
    )
    
    return workflow.compile()

def main():
    print("=== Log Analysis System ===")
    
    json_file = "chatbot_format.json"
    json_data = load_json_file(json_file)
    
    if not json_data:
        print("Failed to load JSON data. Exiting...")
        return
    
    global retriever
    retriever = initialize_vectorstore(json_data)
    if not retriever:
        print("Failed to initialize system. Exiting...")
        return
    
    app = create_workflow()
    print("\nSystem Ready - Type 'quit' to exit")
    
    while True:
        try:
            question = input("\nQuestion: ")
            if question.lower() == 'quit':
                break
            
            initial_state = {
                "question": question,
                "logs": [],
                "web_results": "",
                "analysis": "",
                "retry_count": 0,
                "question_type": "unknown"
            }
            
            result = app.invoke(initial_state)
            
            print("\nAnswer:")
            if result["analysis"] and not result["analysis"].startswith("Error"):
                print(result["analysis"])
            else:
                print("Unable to generate an answer. Please try again.")
            print()
            
        except Exception as e:
            print(f"Error: {str(e)}\n")

if __name__ == "__main__":
    main()