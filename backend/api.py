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
    try:
        prompt_template = load_prompt()

        prompt = prompt_template.replace(
            "{{student_response_1}}", req.student_response_1
        ).replace(
            "{{student_response_2}}", req.student_response_2 or ""
        )

        # OpenAI call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful educational feedback assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3
        )

        feedback_text = response.choices[0].message.content

        # Save to Supabase
        saved_row = await save_to_supabase(
            req.student_name,
            req.student_response_1,
            req.student_response_2,
            feedback_text
        )

        return {
            "feedback": feedback_text,
            "saved": True,
            "supabase_row": saved_row
        }

    except Exception as e:
        print("ERROR IN /analyze:", str(e))
        raise HTTPException(status_code=500, detail=str(e))