import json
import os
import re
from pathlib import Path

from google import genai
from google.genai import types
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent.parent
PROMPTS_PATH = BASE_DIR / "prompts.json"
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

load_dotenv(BASE_DIR / ".env")
api_key = os.getenv("GOOGLE_API_KEY", "").strip("'\"")
if not api_key:
    raise RuntimeError("GOOGLE_API_KEY not found in .env file")

client = genai.Client(api_key=api_key)

with PROMPTS_PATH.open("r", encoding="utf-8") as file:
    PROMPTS = json.load(file)

app = FastAPI(title="AI Detection Hub API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


DEEPFAKE_DEFAULT = {
    "verdict": "UNCERTAIN",
    "confidence": 50,
    "risk_level": "MEDIUM",
    "summary": "",
    "indicators": [],
    "forensic_notes": "",
}

HANDWRITING_DEFAULT = {
    "verdict": "UNCERTAIN",
    "confidence": 50,
    "is_ai_origin": False,
    "summary": "",
    "indicators": [],
    "legibility_score": 50,
    "style_notes": "",
}

FAKE_NEWS_DEFAULT = {
    "extracted_claim": "",
    "verdict": "UNVERIFIED",
    "confidence": 40,
    "summary": "",
    "key_findings": [],
    "red_flags": [],
    "recommendation": "Verify with multiple credible sources.",
    "credibility_score": 40,
}


def parse_verdict(text: str) -> dict:
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return {}
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return {}


def run_model(prompt_key: str, image_bytes: bytes, mime_type: str) -> str:
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            PROMPTS[prompt_key],
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        ],
    )
    return (response.text or "").strip()


def normalize_mime(file: UploadFile) -> str:
    if file.content_type and file.content_type.startswith("image/"):
        return file.content_type
    filename = (file.filename or "").lower()
    ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
    mime_map = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "bmp": "image/bmp",
        "tiff": "image/tiff",
    }
    return mime_map.get(ext, "image/jpeg")


@app.get("/api/health")
def health_check() -> dict:
    return {"status": "ok"}


@app.post("/api/analyze/deepfake")
async def analyze_deepfake(image: UploadFile = File(...)) -> dict:
    try:
        image_bytes = await image.read()
        raw = run_model("deepfake", image_bytes, normalize_mime(image))
        data = parse_verdict(raw)
        if not data:
            data = {**DEEPFAKE_DEFAULT, "summary": raw}
        return data
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc


@app.post("/api/analyze/handwriting")
async def analyze_handwriting(image: UploadFile = File(...)) -> dict:
    try:
        image_bytes = await image.read()
        raw = run_model("handwriting", image_bytes, normalize_mime(image))
        data = parse_verdict(raw)
        if not data:
            data = {**HANDWRITING_DEFAULT, "summary": raw}
        return data
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc


@app.post("/api/analyze/fake-news")
async def analyze_fake_news(image: UploadFile = File(...)) -> dict:
    try:
        image_bytes = await image.read()
        raw = run_model("fake_news", image_bytes, normalize_mime(image))
        data = parse_verdict(raw)
        if not data:
            data = {**FAKE_NEWS_DEFAULT, "summary": raw}
        return data
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Fact-check failed: {exc}") from exc
