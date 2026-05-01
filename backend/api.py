from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from openai import OpenAI
import httpx
import os
import json

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    prolific_id: str
    student_response_1: str
    student_response_2: str = ""


def load_prompt():
    with open("prompts/feedback_prompt.txt", "r", encoding="utf-8") as f:
        return f.read()


def clean_feedback_output(raw_output: str) -> str:
    try:
        parsed = json.loads(raw_output)

        if isinstance(parsed, dict):
            feedback = (
                parsed.get("feedback")
                or parsed.get("Feedback")
                or parsed.get("feedback_text")
                or parsed.get("message")
                or raw_output
            )
        else:
            feedback = raw_output

    except json.JSONDecodeError:
        feedback = raw_output
        feedback = feedback.replace('"level": 1,', "")
        feedback = feedback.replace('"level": "1",', "")
        feedback = feedback.replace("'level': 1,", "")
        feedback = feedback.replace("'level': '1',", "")
        feedback = feedback.replace('"feedback":', "")
        feedback = feedback.replace("'feedback':", "")
        feedback = feedback.replace("{", "")
        feedback = feedback.replace("}", "")
        feedback = feedback.replace('"', "")
        feedback = feedback.replace("'", "")
        feedback = feedback.strip()

    return feedback.replace("undefined", "").strip()


async def save_to_supabase(
    prolific_id: str,
    student_response_1: str,
    student_response_2: str,
    feedback_text: str
):
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(
            status_code=500,
            detail="Supabase environment variables are missing."
        )

    url = f"{SUPABASE_URL}/rest/v1/student_data"

    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    payload = {
        "prolific_id": prolific_id,
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


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    print("PROLIFIC ID:", req.prolific_id)
    print("TEXTBOX 1:", req.student_response_1)
    print("TEXTBOX 2:", req.student_response_2)

    prompt_template = load_prompt()

    prompt = prompt_template.replace(
        "{{student_response_1}}", req.student_response_1
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
You are a science tutor giving personalized feedback.

You must evaluate ONLY the student's Text Box 1 answer.
Do NOT evaluate Text Box 2.
Do NOT give the same feedback for every student.
Your feedback must directly mention the student's exact idea or mistake.

Return ONLY the feedback text.
Do NOT return JSON.
Do NOT include keys like level, feedback, score, or label.
"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.8
    )

    raw_output = response.choices[0].message.content.strip()
    feedback = clean_feedback_output(raw_output)

    await save_to_supabase(
        prolific_id=req.prolific_id,
        student_response_1=req.student_response_1,
        student_response_2=req.student_response_2,
        feedback_text=feedback
    )

    return {
        "feedback": feedback
    }