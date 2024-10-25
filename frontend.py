import streamlit as st
import requests
import os
import json

# Set page configuration as the first Streamlit command
st.set_page_config(page_title="Log File Processor with Chatbot", page_icon=":file_folder:")

# Custom CSS for background color and input field
def add_custom_css():
    st.markdown(
        """
        <style>
        body {
            background-color: #F5F5F5;
        }
        .stApp {
            background-color: #F5F5F5;
        }
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Helvetica', sans-serif;
            color: black;
        }
        .css-18ni7ap.e8zbici2 {
            text-align: center;
            color: black; /* File uploader text color */
        }
        .uploadedFileName {
            color: black !important; /* File name color after uploading */
        }
        .stTextInput input {
            font-size: 16px;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ddd;
            width: 100%;
            background-color: #ffffff;
            color: #333;
        }
        .stButton>button {
            font-size: 16px;
            padding: 10px;
            border-radius: 5px;
            width: 100%;
            background-color: #000000; /* Black color for process button */
            color: white;
            border: none;
        }
        .user-message {
            background-color: #E8E8E8;
            color: #333;
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 5px;
            text-align: left;
            display: flex;
            align-items: center;
            justify-content: flex-start;
        }
        .bot-message {
            background-color: #D3D3D3;
            color: #000000; /* Black color for bot response content */
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 5px;
            text-align: left;
            display: flex;
            align-items: center;
            justify-content: flex-start.
        }
        .message-text {
            text-align: justify;
            color: #000000; /* Black color for response content */
        }
        .message-icon {
            width: 30px;
            height: 30px;
            margin-right: 10px;
        }
        .bot-container, .user-container {
            display: flex;
            justify-content: flex-start;
        }
        .summary-label {
            color: black !important; /* Label color in black */
            font-weight: bold;        /* Make labels bold */
        }
        .summary-content {
            text-align: justify;
            color: black !important;  /* Summary content color in black */
        }
        </style>
        """, unsafe_allow_html=True
    )

# Function to send the file to the backend
def upload_file_to_backend(file, file_type):
    temp_file_path = os.path.join("/Users/sminamda/hackathon-team7/logFiles", file.name)
    with open(temp_file_path, "wb") as f:
        f.write(file.getbuffer())

    files = {'file': open(temp_file_path, 'rb')}
    data = {'file_type': file_type}
    
    backend_url = "http://localhost:5000/process-file"  # Adjust based on your setup
    response = requests.post(backend_url, files=files, data=data)
    
    if response.status_code == 200:
        try:
            result = response.json()  # Parse response as JSON
            return result
        except json.JSONDecodeError:
            st.error("Error parsing JSON response from backend.")
            return None
    else:
        st.error(f"Error: {response.status_code}")
        return None

# Function to send messages to the chatbot in the backend
def send_message_to_chatbot(message_text):
    backend_url = "http://localhost:5000/chatbot"  # Adjust the endpoint based on your Flask setup
    response = requests.post(backend_url, json={'message': message_text})
    
    if response.status_code == 200:
        try:
            result = response.json()  # Parse response as JSON
            return result.get('response', "Error: No response from chatbot.")
        except json.JSONDecodeError:
            st.error("Error parsing JSON response from chatbot.")
            return None
    else:
        st.error(f"Error: {response.status_code}")
        return None

# Streamlit app layout
def main():
    add_custom_css()

    st.header("InsightLog")
    st.markdown("<h4 style='color: black; text-align: left; font-family:lato;'>'Empower your decision making'</h4>", unsafe_allow_html=True)
    if 'file_processed' not in st.session_state:
        st.session_state.file_processed = False

    uploaded_file = st.file_uploader("Upload your log file here", type=['log'])
    
    # Display the file name in black above the "Process" button if a file is uploaded
    if uploaded_file:
        st.markdown(f"<p class='uploadedFileName'><b>Uploaded File:</b> {uploaded_file.name}</p>", unsafe_allow_html=True)
    
    if uploaded_file and st.button("Process"):
        with st.spinner("Processing..."):
            result = upload_file_to_backend(uploaded_file, "Log")
            if result:
                if isinstance(result, dict):  # Ensure result is a dictionary
                    st.subheader("Analysis Result:")
                    st.session_state.file_processed = True
                else:
                    st.error("Unexpected response format from backend. Expected a dictionary.")

    st.markdown("---")

    if st.session_state.file_processed:
        with st.spinner("Processing..."):
            result = upload_file_to_backend(uploaded_file, "Log")
            
            if result:
                if isinstance(result, dict):  # Ensure result is a dictionary
                    st.markdown(f"<span class='summary-label'>**Date:**</span> <span class='summary-content'>{result.get('date', 'N/A')}</span>", unsafe_allow_html=True)
                    st.markdown(f"<span class='summary-label'>**Timestamp:**</span> <span class='summary-content'>{result.get('timestamp', 'N/A')}</span>", unsafe_allow_html=True)
                    st.markdown(f"<span class='summary-label'>**Process-ID:**</span> <span class='summary-content'>{result.get('process_id', 'N/A')}</span>", unsafe_allow_html=True)
                    st.markdown(f"<div class='summary-content'>{result.get('content', 'No content available')}</div>", unsafe_allow_html=True)
                    
                    st.session_state.file_processed = True
                else:
                    st.error("Unexpected response format from backend. Expected a dictionary.")

        st.markdown("---")
        st.header("Ask a question to Chatbot :robot_face:")
        
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        user_input = st.text_input("You: ", key="input_box")
        if user_input:
            bot_response = send_message_to_chatbot(user_input)
            if bot_response:
                st.session_state.chat_history.append({"user": user_input, "bot": bot_response})

        # Display chat history
        if st.session_state.chat_history:
            for chat in st.session_state.chat_history:
                st.markdown(f"""
                <div class="user-container">
                    <img src="https://img.icons8.com/ios-glyphs/30/000000/user.png" class="message-icon"/>
                    <div class="user-message">
                        <p class="message-text">{chat['user']}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="bot-container">
                    <img src="https://img.icons8.com/ios-glyphs/30/000000/chatbot.png" class="message-icon"/>
                    <div class="bot-message">
                        <p class="message-text">{chat['bot']}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
