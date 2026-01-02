from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import requests

# Load keys
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

app = FastAPI()

# 🔒 SECURITY UPDATE
origins = [
    "http://localhost:5173",                      # Keep this for local testing
    "https://gomicrolearn.vercel.app/"  # <-- PASTE YOUR VERCEL URL HERE (No trailing slash)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- THE LIBRARIAN (AI) ---
def generate_syllabus(topic: str):
    """
    Asks the LLM to break a topic into 3-5 sub-modules.
    Returns a strict JSON structure.
    """
    print(f"Librarian is thinking about: {topic}...")
    
    prompt = f"""
    Create a micro-learning curriculum for: '{topic}'.
    Return ONLY valid JSON. No markdown. No intro text.
    Structure:
    {{
        "topic": "{topic}",
        "modules": [
            {{ "id": 1, "title": "Short Title", "description": "One sentence summary", "search_term": "Optimized YouTube Shorts query" }}
        ]
    }}
    Limit to 3-5 modules. Make it beginner friendly.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Or gpt-3.5-turbo
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        content = response.choices[0].message.content
        # Clean potential markdown code blocks
        if "```json" in content:
            content = content.replace("```json", "").replace("```", "")
        return json.loads(content)
    except Exception as e:
        print(f"AI Error: {e}")
        return None

# --- THE CURATOR (YouTube) ---
def get_videos_for_module(search_term):
    if not YOUTUBE_API_KEY:
        return ["N20k-rV-iXQ", "G2fqAlgmoPo"] # Backup IDs

    params = {
        "part": "id",
        "q": f"{search_term} #shorts",
        "type": "video",
        "videoDuration": "short",
        "maxResults": 3,
        "key": YOUTUBE_API_KEY
    }
    try:
        res = requests.get(YOUTUBE_SEARCH_URL, params=params)
        data = res.json()
        ids = [item["id"]["videoId"] for item in data.get("items", []) if "id" in item and "videoId" in item["id"]]
        return ids if ids else ["N20k-rV-iXQ"] # Fallback if empty
    except:
        return ["N20k-rV-iXQ"]

@app.get("/generate_course")
def generate_course(topic: str):
    # 1. Ask AI for Syllabus
    syllabus = generate_syllabus(topic)
    
    if not syllabus:
        raise HTTPException(status_code=500, detail="AI Librarian failed.")

    # 2. Fill Syllabus with Videos
    for module in syllabus["modules"]:
        print(f"Curating videos for: {module['title']}...")
        module["videos"] = get_videos_for_module(module["search_term"])

    return syllabus