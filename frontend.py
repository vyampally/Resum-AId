import streamlit as st
import requests
import io
from audio_recorder_streamlit import audio_recorder
from streamlit_webrtc import webrtc_streamer, WebRtcMode, VideoProcessorBase

import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
with open('./config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)



hashed_passwords = stauth.Hasher(['abc', 'def']).generate()

authenticator = Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

name, authentication_status, username = authenticator.login('Login', 'main')




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

# Streamlit UI
st.title("Interview Bot")

# Upload resume
st.subheader("Upload Resume")
resume_file = st.file_uploader("Choose a PDF file...", type="pdf", key="resume_uploader_unique")
if resume_file is not None:
    upload_file(resume_file, "upload_resume", "resume")

# Upload job description
st.subheader("Upload Job Description")
job_description_file = st.file_uploader("Choose a PDF file...", type="pdf", key="job_description_uploader_unique")
if job_description_file is not None:
    upload_file(job_description_file, "upload_job_description", "job_description")

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
    st.subheader("Record Your Response")
    st.write("Press the button below to start recording.")
    
    # Audio recorder component
    audio_data = audio_recorder()
    
    if audio_data:
        # Convert audio to bytes
        audio_bytes = io.BytesIO(audio_data)
        submit_response(audio_bytes.getvalue())
else:
    st.write("Click 'Start Interview' to begin recording your responses.")