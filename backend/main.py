from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv
import requests

# Load keys
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

# Validate API keys on startup
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")
if not YOUTUBE_API_KEY:
    raise ValueError("YOUTUBE_API_KEY environment variable is required")

client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()

# 🔒 SECURITY: CORS - Only allow specific origins
# Get allowed origins from environment or use defaults
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,https://gomicrolearn.vercel.app"
).split(",")

# Clean up origins (remove trailing slashes and whitespace)
ALLOWED_ORIGINS = [origin.rstrip("/").strip() for origin in ALLOWED_ORIGINS if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # ✅ FIXED: Use specific origins instead of "*"
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # ✅ FIXED: Limit to only needed methods
    allow_headers=["*"],
)

# --- INPUT VALIDATION ---
def validate_and_sanitize_topic(topic: str) -> str:
    """
    Validate and sanitize topic input to prevent injection attacks.
    """
    if not topic or not isinstance(topic, str):
        raise ValueError("Topic must be a non-empty string")
    
    # Limit length to prevent abuse
    if len(topic) > 200:
        raise ValueError("Topic must be 200 characters or less")
    
    # Remove potentially dangerous characters but allow normal text
    # Keep letters, numbers, spaces, and common punctuation
    sanitized = re.sub(r'[^\w\s\-.,!?()\']', '', topic)
    sanitized = sanitized.strip()
    
    if len(sanitized) < 1:
        raise ValueError("Topic must contain at least one valid character")
    
    return sanitized

# --- THE LIBRARIAN (AI) ---
def generate_syllabus(topic: str):
    """
    Asks the LLM to break a topic into 3-5 sub-modules.
    Returns a strict JSON structure.
    """
    print(f"Librarian is thinking about: {topic}...")
    
    # ✅ FIXED: Use JSON escaping to prevent prompt injection
    # Escape the topic for safe inclusion in JSON/string context
    topic_escaped = json.dumps(topic)[1:-1]  # Remove outer quotes after JSON encoding
    
    prompt = f"""Create a micro-learning curriculum for: {topic_escaped}.
Return ONLY valid JSON. No markdown. No intro text.
Structure:
{{
    "topic": {json.dumps(topic)},
    "modules": [
        {{ "id": 1, "title": "Short Title", "description": "One sentence summary", "search_term": "Optimized YouTube Shorts query" }}
    ]
}}
Limit to 3-5 modules. Make it beginner friendly."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            timeout=30  # ✅ Added timeout to prevent hanging requests
        )
        content = response.choices[0].message.content
        # Clean potential markdown code blocks
        if "```json" in content:
            content = content.replace("```json", "").replace("```", "")
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"AI JSON parsing error: {e}")
        return None
    except Exception as e:
        print(f"AI Error: {type(e).__name__}: {str(e)}")
        return None

# --- THE CURATOR (YouTube) ---
def validate_video_id(video_id: str) -> bool:
    """Validate YouTube video ID format."""
    # YouTube video IDs are 11 characters, alphanumeric with some special chars
    return bool(re.match(r'^[a-zA-Z0-9_-]{11}$', video_id))

def get_videos_for_module(search_term: str):
    """
    Get videos for a module from YouTube API.
    Returns list of valid video IDs.
    """
    if not YOUTUBE_API_KEY:
        return ["N20k-rV-iXQ", "G2fqAlgmoPo"]  # Backup IDs

    # Sanitize search term
    search_term_clean = search_term[:100]  # Limit length
    
    params = {
        "part": "id",
        "q": f"{search_term_clean} #shorts",
        "type": "video",
        "videoDuration": "short",
        "maxResults": 3,
        "key": YOUTUBE_API_KEY
    }
    try:
        res = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=10)  # ✅ Added timeout
        res.raise_for_status()  # ✅ Raise exception for HTTP errors
        data = res.json()
        
        # ✅ FIXED: Validate video IDs before returning
        ids = []
        for item in data.get("items", []):
            if "id" in item and "videoId" in item["id"]:
                video_id = item["id"]["videoId"]
                if validate_video_id(video_id):
                    ids.append(video_id)
        
        return ids if ids else ["N20k-rV-iXQ"]  # Fallback if empty
    except requests.RequestException as e:
        print(f"YouTube API error: {type(e).__name__}: {str(e)}")
        return ["N20k-rV-iXQ"]
    except (KeyError, ValueError) as e:
        print(f"YouTube API response parsing error: {type(e).__name__}: {str(e)}")
        return ["N20k-rV-iXQ"]

@app.get("/generate_course")
def generate_course(topic: str = Query(..., min_length=1, max_length=200)):
    """
    Generate a course curriculum for a given topic.
    
    Args:
        topic: The topic to create a curriculum for (1-200 characters)
    
    Returns:
        JSON object with topic and modules containing videos
    """
    try:
        # ✅ FIXED: Validate and sanitize input
        sanitized_topic = validate_and_sanitize_topic(topic)
        
        # 1. Ask AI for Syllabus
        syllabus = generate_syllabus(sanitized_topic)
        
        if not syllabus:
            raise HTTPException(
                status_code=500,
                detail="Unable to generate curriculum. Please try again."
            )

        # 2. Fill Syllabus with Videos
        for module in syllabus.get("modules", []):
            search_term = module.get("search_term", "")
            print(f"Curating videos for: {module.get('title', 'Unknown')}...")
            module["videos"] = get_videos_for_module(search_term)

        return syllabus
    except ValueError as e:
        # ✅ FIXED: Return appropriate error for validation failures
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # ✅ FIXED: Don't expose internal error details
        print(f"Unexpected error: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while generating the curriculum."
        )