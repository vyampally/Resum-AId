import streamlit as st
import requests
import io
from audio_recorder_streamlit import audio_recorder
from streamlit_webrtc import webrtc_streamer, WebRtcMode, VideoProcessorBase

# Constants
API_URL = "http://localhost:8000"  # URL of your FastAPI server

# Function to upload a file to the backend
def upload_file(file, endpoint, field_name):
    files = {field_name: file}
    response = requests.post(f"{API_URL}/{endpoint}", files=files)
    if response.status_code == 200:
        st.success(response.json().get("message"))
    else:
        st.error(f"Error uploading file: {response.text}")

# Function to choose question type
def choose_question_type(type):
    response = requests.post(f"{API_URL}/choose_question_type", data={"question_type": type})
    if response.status_code == 200:
        st.success(response.json().get("message"))
    else:
        st.error(f"Error choosing question type: {response.text}")

# Function to start an interview
def start_interview():
    response = requests.post(f"{API_URL}/interview")
    if response.status_code == 200:
        audio = response.content
        st.audio(io.BytesIO(audio), format='audio/mpeg')
        st.session_state.current_question_index = 0
        st.session_state.recording = True
        st.session_state.questions_asked = 1
    else:
        st.error(f"Error starting interview: {response.text}")

# Function to submit an audio response
def submit_response(audio_bytes):
    response = requests.post(f"{API_URL}/submit_response", files={"audio": audio_bytes})
    if response.status_code == 200:
        audio = response.content
        st.audio(io.BytesIO(audio), format='audio/mpeg')
        st.session_state.questions_asked += 1
        if st.session_state.questions_asked >= 3:
            st.session_state.recording = False
        else:
            st.session_state.recording = True
    else:
        st.error(f"Error submitting response: {response.text}")

# Custom CSS for styling
st.markdown("""
    <style>
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 24px;
            margin: 10px 0;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: background-color 0.3s, transform 0.3s;
        }
        .stButton>button:hover {
            background-color: #45a049;
            transform: translateY(-2px);
        }
        .stButton>button:active {
            transform: translateY(1px);
        }
        .stFileUploader {
            margin-bottom: 20px;
        }
        .stFileUploader>label {
            font-size: 1.1em;
            color: #333;
        }
    </style>
""", unsafe_allow_html=True)

# Streamlit UI
st.title("ResumAId")
st.write("Welcome to the interactive interview bot. Please follow the steps below to proceed.")

# Upload resume
st.subheader("1. Upload Resume")
resume_uploaded = False
resume_file = st.file_uploader("Choose a PDF file...", type="pdf", key="resume_uploader_unique")
if resume_file is not None:
    upload_file(resume_file, "upload_resume", "resume")
    resume_uploaded = True

# Upload job description
st.subheader("2. Upload Job Description")
job_description_uploaded = False
job_description_file = st.file_uploader("Choose a PDF file...", type="pdf", key="job_description_uploader_unique")
if job_description_file is not None:
    upload_file(job_description_file, "upload_job_description", "job_description")
    job_description_uploaded = True

# Select question type only after both files are uploaded
if resume_uploaded and job_description_uploaded:
    st.subheader("3. Select Question Type")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Behavioral Questions"):
            choose_question_type("behavioral")
    with col2:
        if st.button("Technical Questions"):
            choose_question_type("technical")
    
    # Start interview button
    if st.button("Start Interview"):
        start_interview()

# Initialize session state variables
if "recording" not in st.session_state:
    st.session_state.recording = False
if "questions_asked" not in st.session_state:
    st.session_state.questions_asked = 0
if "video_enabled" not in st.session_state:
    st.session_state.video_enabled = False

# Video streaming functionality
class VideoTransformer(VideoProcessorBase):
    def __init__(self):
        self.type = "original"

    def recv(self, frame):
        return frame

if not st.session_state.video_enabled:
    if st.button("Enable Video"):
        st.session_state.video_enabled = True

if st.session_state.video_enabled:
    webrtc_streamer(
        key="video_stream",
        mode=WebRtcMode.SENDONLY,
        media_stream_constraints={
            "video": True,
            "audio": False,
        },
        video_processor_factory=VideoTransformer,
        async_processing=True,
    )

# Audio recording functionality
if st.session_state.recording:
    st.subheader("4. Record Your Response")
    st.write("Press the button below to start recording.")
    
    # Audio recorder component
    audio_data = audio_recorder()
    
    if audio_data:
        # Convert audio to bytes
        audio_bytes = io.BytesIO(audio_data)
        submit_response(audio_bytes.getvalue())
else:
    st.write("Click 'Start Interview' to begin recording your responses.")