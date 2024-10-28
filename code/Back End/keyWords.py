import json
import re
import requests
import huggingface_hub
from transformers import AutoTokenizer, AutoModel
import torch
import numpy
# # Function to use Hugging Face Inference API with LLaMA
# def query_llama(input_text, api_key):
#     headers = {
#         "Authorization": f"Bearer {api_key}",
#         "Content-Type": "application/json"
#     }
#     response = requests.post(
#         'https://api-inference.huggingface.co/models/meta-llama/LLaMA-2-7b-chat',
#         headers=headers,
#         json={"inputs": input_text}
#     )
#     return response.json()
# # Path to the log file
filename = '/Users/vmhegde/Documents/Oracle/GenAIHackaothon/test/APP01/skully.log'
api_key = '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'  # Replace with your Hugging Face API key
# # Resultant dictionary to store log entries
log_entries = []
entry_count = 0
# # Regular expression to match the timestamp (adjust based on your timestamp format)
log_entry_pattern = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}')
# # Keywords to search for
# # List to hold all the lines from the current log entry
current_entry_lines = []
# Process the log file and extract log entries
with open(filename) as fh:
    for line in fh:
        # Check if the line starts with a timestamp (new log entry)
        if log_entry_pattern.match(line):
            # If we already have lines from the previous log entry, save them first
            if current_entry_lines:
                # Join the multiline entry
                log_entry_text = " ".join(current_entry_lines).strip()
                
                # Split the saved text into fields (date, timestamp, and rest of the values)
                description = log_entry_text.split(None, 5)  # Split by 5 to capture the rest as 'info'
                
                if len(description) >= 6:  # Ensure we have enough fields
                    log_entry = { 
                        'date': description[0], 
                        'timestamp': description[1], 
                        'project_id': description[2], 
                        'status': description[3], 
                        'project': description[4], 
                        'info': description[5]
                    }
                    # Add the entry to the log list
                    log_entries.append(log_entry)
                    entry_count += 1
            # Start collecting lines for the new log entry
            current_entry_lines = [line.strip()]
        else:
            # If it's a continuation of the previous log entry, add it to the list
            current_entry_lines.append(line.strip())
    # Don't forget to add the last log entry if there are remaining lines
    if current_entry_lines:
        log_entry_text = " ".join(current_entry_lines).strip()
        description = log_entry_text.split(None, 5)
        
        if len(description) >= 6:  # Ensure we have enough fields
            log_entry = { 
                'date': description[0], 
                'timestamp': description[1], 
                'project_id': description[2], 
                'status': description[3], 
                'project': description[4], 
                'info': description[5]
            }
            log_entries.append(log_entry)
# Now, let's find all logs with the keywords and capture the preceding logs
# suspicious_logs = []
# for i, log_entry in enumerate(log_entries):
#     # Check if the 'info' field contains any of the keywords
#     if any(keyword in log_entry['info'].lower() for keyword in keywords):
#         # Collect the previous 15 logs if they exist
#         start_index = max(i - 15, 0)
#         preceding_logs = log_entries[start_index:i]  # Exclude the current log with the keyword
        
#         # Store the trigger log and the preceding logs
#         suspicious_logs.append({
#             'trigger_log': log_entry,  # The log that initiated the suspicious event
#             'preceding_logs': preceding_logs
#         })
# print(suspicious_logs)
# # # Prepare to write responses to a file
# with open("test2.txt", "w") as response_file:
# #     # Process suspicious logs for root cause analysis
#     for suspicious_log in suspicious_logs:
#         trigger_log = suspicious_log['trigger_log']
#         preceding_logs = suspicious_log['preceding_logs']
        
#         # Prepare the input for the model
#         input_text = "Given the following log that triggered a failure:\n"
#         input_text += json.dumps(trigger_log, indent=4)
#         input_text += "\n\nAnd the following preceding logs:\n"
        
        # for log in preceding_logs:
        #     input_text += json.dumps(log, indent=4) + "\n"
        
#         # Query the LLaMA model
#         response = query_llama(input_text, api_key)
        
#         # Write the response from the model to the file
#         response_file.write(f"Trigger Log Entry:\n{json.dumps(trigger_log, indent=4)}\n")
#         response_file.write("Preceding Logs:\n")
#         for log in preceding_logs:
#             response_file.write(f"{json.dumps(log, indent=4)}\n")
#         response_file.write("LLaMA-2 Response:\n")
#         response_file.write(json.dumps(response, indent=6))
#         response_file.write("\n\n")
# Creating JSON file for all log entries
suspicious_logs = []
keywords = ['fail', 'error', 'warning']  # Make sure keywords are lowercase
# Collect trigger logs and preceding 20 logs
for i, log_entry in enumerate(log_entries):
    # Check if the 'info' field contains any of the keywords (case insensitive)
    if any(keyword in log_entry['info'].lower() for keyword in keywords):
        # Collect the previous 20 logs if they exist
        start_index = max(i - 20, 0)
        preceding_logs = log_entries[start_index:i]  # Exclude the current log with the keyword
        
        # Store the trigger log and the preceding logs
        suspicious_logs.append({
            'trigger_log': log_entry,  # The log that initiated the suspicious event
            'preceding_logs': preceding_logs
        })
# Now write the suspicious logs and preceding logs to a text file
with open("test2.txt", "w") as response_file:
    # Process suspicious logs for root cause analysis
    for suspicious_log in suspicious_logs:
        trigger_log = suspicious_log['trigger_log']
        preceding_logs = suspicious_log['preceding_logs']
        
        # Write the trigger log
        response_file.write("Trigger Log:\n")
        response_file.write(json.dumps(trigger_log, indent=4))  # Write trigger log in JSON format
        response_file.write("\n\nPreceding Logs (20 or fewer):\n")
        
        # Write preceding logs
        for preceding_log in preceding_logs:
            response_file.write(json.dumps(preceding_log, indent=4))  # Write each preceding log in JSON format
            response_file.write("\n")  # Add a newline for readability between logs
        
        response_file.write("\n" + "-"*50 + "\n\n")  # Separator between suspicious log blocks
print("Logs successfully written to test2.txt")
with open("log_entries.json", "w") as out_file:
    json.dump(log_entries, out_file, indent=6)
print(f"Found {len(suspicious_logs)} suspicious log entries with preceding logs.")
filepath = "test2.txt"

import torch
from transformers import AutoModel, AutoTokenizer
# # Load a pre-trained model and tokenizer
# model_name = "sentence-transformers/all-MiniLM-L6-v2"
# model = AutoModel.from_pretrained(model_name)
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# # Create a function to convert log entries to embeddings
def log_entry_to_embedding(log_entry):
    input_text = json.dumps(log_entry, indent=4)
    inputs = tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)
    outputs = model(**inputs)
    embeddings = outputs.last_hidden_state[:, 0, :]  # Extract the embedding from the last hidden state
    return embeddings.detach().numpy()
# # Convert log entries to embeddings and store them in a list
# embeddings = []
# for log_entry in log_entries:
#     embedding = log_entry_to_embedding(log_entry)
#     embeddings.append(embedding)
    
# import faiss
# # Create a faiss index
# index = faiss.IndexFlatL2(embeddings[0].shape[0])  # Use L2 distance for similarity search
# # Add the embeddings to the index
# index.add(np.array(embeddings))
# from flask import Flask, request, jsonify
# app = Flask(__name__)
# @app.route("/find_root_cause", methods=["POST"])
# def find_root_cause():
#     prompt = request.json["prompt"]
#     # Query the vector storage to find similar log entries
#     distances, indices = index.search(np.array([log_entry_to_embedding(prompt)]), k=10)
#     similar_log_entries = [log_entries[i] for i in indices[0]]
#     # Use the similar log entries to generate a response
#     response = generate_response(similar_log_entries)
#     return jsonify({"response": response})
# def generate_response(similar_log_entries):
#     # Implement a function to generate a response based on the similar log entries
#     # This could involve calling the LLaMA model or using a simpler approach
#     pass
# if __name__ == "__main__":
#     app.run(debug=True)
# Load the tokenizer and model from Hugging Face
model_name = "distilbert-base-uncased"  # You can choose a different model if needed
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)
# Function to load and process logs from test2.txt
def load_logs(filepath):
   with open(filepath, 'r') as file:
       log_data = file.read()  # Read the entire content of test2.txt
       return log_data
# Function to convert text to embeddings using Hugging Face
def get_embeddings(text):
    inputs = tokenizer(text, return_tensors='pt', padding=True, truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)
    # Use the mean of the last hidden states as the embedding
    embeddings = outputs.last_hidden_state.mean(dim=1).squeeze().tolist()
    return embeddings
def save_embeddings(embeddings, output_file):
   with open(output_file, 'w') as json_file:
       json.dump(embeddings, json_file, indent=4)
       print(f"Embeddings saved to {output_file}")