from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from openai import OpenAI
import httpx
import os

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# FastAPI app
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request schema
class AnalyzeRequest(BaseModel):
    student_name: str
    student_response_1: str
    student_response_2: str = ""  # optional


# Load prompt
def load_prompt():
    with open("prompts/feedback_prompt.txt", "r", encoding="utf-8") as f:
        return f.read()


# Save to Supabase
async def save_to_supabase(student_name: str, student_response_1: str, student_response_2: str, feedback_text: str):
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(
            status_code=500,
            detail="Supabase environment variables are missing."
        )

    # IMPORTANT: use correct table name
    url = f"{SUPABASE_URL}/rest/v1/student_data"

    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    payload = {
        "student_name": student_name,
        "student_response_1": student_response_1,
        "student_response_2": student_response_2,
        "feedback_text": feedback_text,
    }

    async with httpx.AsyncClient() as http_client:
        response = await http_client.post(url, headers=headers, json=payload)

    if response.status_code not in [200, 201]:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save to Supabase: {response.text}"
        )

    return response.json()


# Health check
@app.get("/health")
def health():
    return {"status": "ok"}


# Main endpoint
@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    print("TEXTBOX 1:", req.student_response_1)
    print("TEXTBOX 2:", req.student_response_2)

    prompt_template = load_prompt()

    prompt = prompt_template.replace("{response}", req.student_response_1)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
You are a science tutor giving personalized formative feedback.
Evaluate ONLY the student's Text Box 1 answer.
Do NOT evaluate Text Box 2.
Follow the rubric and feedback guidelines exactly.
Return only the JSON requested by the prompt.
"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3
    )

    raw_output = response.choices[0].message.content.strip()

    return {
        "feedback": raw_output
    }