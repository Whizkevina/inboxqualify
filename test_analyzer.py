#!/usr/bin/env python3

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from API.huggingface_analyzer import HuggingFaceAnalyzer

load_dotenv()

api_key = os.getenv("HUGGINGFACE_API_KEY")
if not api_key:
    print("No API key found!")
    exit(1)

print("Testing HuggingFaceAnalyzer directly...")
analyzer = HuggingFaceAnalyzer(api_key)

print(f"Primary model: {analyzer.sentiment_model}")

result = analyzer.analyze_email_with_ai(
    "Great opportunity", 
    "Hi there, this is amazing!"
)

print(f"Result: {result}")
