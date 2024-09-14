from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import openai
import os
import requests
import fitz  # PyMuPDF
import io
from gtts import gTTS
from pydub import AudioSegment


#load env variables
load_dotenv()

#create 
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#use open api key
openai.api_key = os.getenv("OPENAI_API_KEY")

#interview parameters
interview_env = {
    "user_resume": "",
    "job_description_text": "",
    "questions": [],
    "current_question_index": 0,
    "user_responses": []
}

#upload resume method
@app.post("/upload_resume")
async def upload_resume(resume: UploadFile = File(...)):
    try:
        #parse through
        resume_content = await resume.read()
        #make sure pdf, else throw exception
        user_resume = extract_text_from_pdf(resume_content)
        interview_env["user_resume"] = user_resume
        return {"message": "Resume uploaded successfully"}
    except Exception as e:
        #wrong format
        raise HTTPException(status_code=500, detail=f"Error processing resume: {e}")

#upload job description method
@app.post("/upload_job_description")
async def upload_job_description(job_description: UploadFile = File(...)):
    try:
        #parse
        job_description_content = await job_description.read()
        #make sure pdf
        job_description_text = extract_text_from_pdf(job_description_content)
        interview_env["job_description_text"] = job_description_text
        return {"message": "Job description uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing job description: {e}")

#choose either technical or behavioral
@app.post("/choose_question_type")
async def choose_question_type(question_type: str = Form(...)):
    #check if valid
    if question_type not in ["behavioral", "technical"]:
        raise HTTPException(status_code=400, detail="Invalid question type")
    
    #generate questions based on type
    interview_env["question_type"] = question_type
    return {"message": f"{question_type.capitalize()} questions selected"}

#user response
@app.post("/submit_response")
async def submit_response(audio: UploadFile = File(...)):
    try:
        #listen to user read from tts
        audio_content = await audio.read()
        interview_env["user_responses"].append(audio_content)
        
        #ask question if less than total number of questions
        if interview_env["current_question_index"] < len(interview_env["questions"]):
            next_question = interview_env["questions"][interview_env["current_question_index"]]
            interview_env["current_question_index"] += 1
            response_text = next_question
        else:
            #once question array is over
            response_text = "Great job completing the interview!"
            
            #reset interview context and array
            interview_env["questions"] = []
            interview_env["current_question_index"] = 0
            interview_env["user_responses"] = []

        audio_output = text_to_speech(response_text)
        return StreamingResponse(io.BytesIO(audio_output), media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during audio response submission: {e}")


@app.post("/interview")
async def interview_response():
    try:
        #look at resume and description
        user_resume = interview_env["user_resume"]
        job_description_text = interview_env["job_description_text"]
        question_type = interview_env.get("question_type", "behavioral")  # Default to behavioral if not set

        #generate fitting questions based on the question type
        interview_env["questions"] = generate_interview_questions(user_resume, job_description_text, question_type)
        interview_env["current_question_index"] = 0

        #set user response array
        interview_env["user_responses"] = []
        
        #if there are questions, then go through them
        if interview_env["questions"]:
            next_question = interview_env["questions"][interview_env["current_question_index"]]
            interview_env["current_question_index"] += 1
            response_text = next_question
        else:
            #no questions generated
            response_text = "No questions were generated. Please check the resume and job description."
        
        audio_output = text_to_speech(response_text)
        return StreamingResponse(io.BytesIO(audio_output), media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating interview questions: {e}")

# text to pdf
def extract_text_from_pdf(pdf_content):
    try:
        text = ""
        #open pdf
        pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
        #iterate through each page
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
        return text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading PDF file: {e}")


#generate questions with OpenAI
def generate_interview_questions(user_resume, job_description_text, question_type):
    messages = [
        #giving role to the AI
        {"role": "system", "content": "You are an assistant for an interviewer generating questions based on a resume and job description."},
        {"role": "user", "content": f"Generate three {question_type} interview questions based on the following resume and job description:\n\nResume:\n{user_resume}\n\nJob Description:\n{job_description_text}"}
    ]
    #generate response from gpt 3.5 turbo
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    #return questions from api response
    questions = response.choices[0].message.content
    return questions.split('\n\n')


def text_to_speech(text):
    try:
        #convert text to audio for machine
        tts = gTTS(text=text, lang='en')
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        #convert audio to mp3 with pydub
        audio = AudioSegment.from_file(audio_buffer, format="mp3")
        output_buffer = io.BytesIO()
        audio.export(output_buffer, format="mp3")
        output_buffer.seek(0)
        
        return output_buffer.read()
    
    except Exception as e:
        print(f"Text-to-speech conversion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Text-to-speech conversion failed: {e}")

# Ensure ffmpeg is installed for pydub
AudioSegment.ffmpeg = "/usr/local/bin/ffmpeg"

#running main
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)