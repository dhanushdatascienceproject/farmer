import streamlit as st
import requests

# Streamlit UI
st.title("Financial Scoring App")
st.write("Upload your family financial data to get a financial score and recommendations.")

# File uploader - any file type
uploaded_file = st.file_uploader("Upload File", type=["xlsx", "csv", "json", "txt"])

if uploaded_file:
    st.write(f"File name: {uploaded_file.name}")  # Display file name

    # Prepare the file to send to FastAPI
    files = {'file': (uploaded_file.name, uploaded_file, uploaded_file.type)}

    # Send file to FastAPI endpoint
    response = requests.post("http://127.0.0.1:8000/process/", files=files)

    if response.status_code == 200:
        result = response.json()
        st.write("Financial Scores and Recommendations:")
        st.write(result)
    else:
        st.write("Error processing the file.")
