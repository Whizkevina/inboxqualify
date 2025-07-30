# main.py - FINAL VERSION

# 1. Import necessary libraries
import os
import sys
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from local_analyzer import LocalEmailAnalyzer
from huggingface_analyzer import HuggingFaceAnalyzer

# Load environment variables from .env file
load_dotenv()

# --- API KEY CONFIGURATION ---
# Load API keys from environment variables
try:
    # Try Hugging Face first (our new primary AI)
    hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not hf_api_key:
        print("Warning: HUGGINGFACE_API_KEY not set. Will use local analyzer only.")
    else:
        print("Hugging Face API key loaded successfully!")
    
except Exception as e:
    print(f"Error loading API keys: {e}")
    print("Will use local analyzer as fallback.")

# --- App Setup & CORS ---
origins = ["*"] # Allows all origins for local development
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Data Models ---
class EmailInput(BaseModel):
    subject: str
    email_body: str

class CategoryResult(BaseModel):
    name: str
    score: int
    maxScore: int
    feedback: str

class AnalysisResult(BaseModel):
    overallScore: int
    verdict: str
    breakdown: list[CategoryResult]


# --- AI Analysis Function ---

async def analyze_with_ai(subject: str, body: str) -> AnalysisResult:
    # Try Hugging Face first
    hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
    
    if hf_api_key:
        try:
            print("Using Hugging Face AI for analysis...")
            hf_analyzer = HuggingFaceAnalyzer(hf_api_key)
            result_data = hf_analyzer.analyze_email_with_ai(subject, body)
            return AnalysisResult(**result_data)
        except Exception as e:
            print(f"Hugging Face analysis failed: {e}")
            print("Falling back to local analyzer...")
    
    # Fallback to local analyzer
    print("Using local rule-based analyzer...")
    local_analyzer = LocalEmailAnalyzer()
    result_data = local_analyzer.analyze_email(subject, body)
    
    # Add note that this is from local analysis
    result_data["verdict"] += " (Local Analysis)"
    
    return AnalysisResult(**result_data)


# --- API Endpoint ---
@app.post("/qualify", response_model=AnalysisResult)
async def qualify_email(email_input: EmailInput):
    return await analyze_with_ai(email_input.subject, email_input.email_body)

@app.get("/")
def read_root():
    return {"status": "inboxqualify API is running!"}