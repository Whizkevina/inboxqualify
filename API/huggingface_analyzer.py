# huggingface_analyzer.py - Hugging Face AI integration for email analysis

import requests
import json
import re
from typing import Dict
import time

class HuggingFaceAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api-inference.huggingface.co/models/"
        
        # Use the working model we confirmed
        self.sentiment_model = "nlptown/bert-base-multilingual-uncased-sentiment"
        
        # Fallback models if primary fails
        self.fallback_models = [
            "cardiffnlp/twitter-roberta-base-sentiment-latest",
            "distilbert-base-uncased-finetuned-sst-2-english",
            "cardiffnlp/twitter-roberta-base-sentiment"
        ]
        
    def analyze_email_with_ai(self, subject: str, body: str) -> Dict:
        """Use Hugging Face for sentiment analysis + local rules for structure"""
        
        # Get sentiment analysis from Hugging Face
        sentiment_data = self._get_sentiment_analysis(subject + " " + body)
        
        # Use our local analyzer for the structured analysis
        from local_analyzer import LocalEmailAnalyzer
        local_analyzer = LocalEmailAnalyzer()
        base_result = local_analyzer.analyze_email(subject, body)
        
        # Enhance with AI sentiment insights
        if sentiment_data:
            # Adjust scores based on sentiment
            sentiment_score = sentiment_data.get('sentiment_score', 0)
            
            # Enhance professionalism score based on sentiment
            for category in base_result["breakdown"]:
                if category["name"] == "Professionalism":
                    if sentiment_score > 0.5:  # Positive sentiment
                        category["score"] = min(10, category["score"] + 2)
                        category["feedback"] += f" AI detected positive tone (confidence: {sentiment_score:.2f})."
                    elif sentiment_score < -0.3:  # Negative sentiment
                        category["score"] = max(0, category["score"] - 3)
                        category["feedback"] += f" AI detected negative tone (confidence: {abs(sentiment_score):.2f})."
                    else:
                        category["feedback"] += " AI detected neutral tone."
        
        # Recalculate overall score
        base_result["overallScore"] = sum(cat["score"] for cat in base_result["breakdown"])
        base_result["verdict"] = self._get_verdict(base_result["overallScore"]) + " (AI Enhanced)"
        
        return base_result
    
    def _get_sentiment_analysis(self, text: str) -> Dict:
        """Get sentiment analysis from Hugging Face"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {"inputs": text}
        
        try:
            url = f"{self.base_url}{self.sentiment_model}"
            print(f"Calling Hugging Face API: {url}", flush=True)
            
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=15
            )
            
            print(f"Response status: {response.status_code}", flush=True)
            
            if response.status_code == 200:
                result = response.json()
                print(f"Sentiment analysis successful!", flush=True)
                return self._process_sentiment_response(result)
            elif response.status_code == 404:
                print(f"Model not found (404). Trying alternative model...", flush=True)
                # Try alternative model
                return self._try_alternative_model(text, headers)
            elif response.status_code == 503:
                print("Sentiment model loading, skipping AI enhancement...", flush=True)
                return {'sentiment_score': 0, 'positive_confidence': 0, 'negative_confidence': 0}
            else:
                print(f"Sentiment API error: {response.status_code}", flush=True)
                print(f"Response: {response.text}", flush=True)
                return {'sentiment_score': 0, 'positive_confidence': 0, 'negative_confidence': 0}
                
        except Exception as e:
            print(f"Sentiment analysis failed: {e}", flush=True)
            return {'sentiment_score': 0, 'positive_confidence': 0, 'negative_confidence': 0}
    
    def _try_alternative_model(self, text: str, headers: Dict) -> Dict:
        """Try alternative sentiment analysis models"""
        alternative_models = [
            "cardiffnlp/twitter-roberta-base-sentiment-latest",
            "nlptown/bert-base-multilingual-uncased-sentiment",
            "cardiffnlp/twitter-roberta-base-sentiment"
        ]
        
        for model in alternative_models:
            try:
                print(f"Trying alternative model: {model}", flush=True)
                response = requests.post(
                    f"{self.base_url}{model}",
                    headers=headers,
                    json={"inputs": text},
                    timeout=15
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"Alternative model {model} succeeded!", flush=True)
                    return self._process_sentiment_response(result)
                else:
                    print(f"Alternative model {model} failed: {response.status_code}", flush=True)
                    
            except Exception as e:
                print(f"Alternative model {model} error: {e}", flush=True)
                continue
        
        print("All alternative models failed, using local analysis only", flush=True)
        return {'sentiment_score': 0, 'positive_confidence': 0, 'negative_confidence': 0}
    
    def _process_sentiment_response(self, response) -> Dict:
        """Process sentiment response from Hugging Face"""
        try:
            if isinstance(response, list) and len(response) > 0:
                sentiments = response[0]
                
                # Handle different model response formats
                positive_score = 0
                negative_score = 0
                
                for sentiment in sentiments:
                    label = sentiment.get('label', '').upper()
                    score = sentiment.get('score', 0)
                    
                    # Handle star rating format (1-5 stars)
                    if '5 STARS' in label or '4 STARS' in label:
                        positive_score += score
                    elif '1 STAR' in label or '2 STARS' in label:
                        negative_score += score
                    elif '3 STARS' in label:
                        # 3 stars is neutral, add small positive bias
                        positive_score += score * 0.2
                    
                    # Handle positive/negative format
                    elif 'POSITIVE' in label or 'POS' in label or label.startswith('LABEL_2'):
                        positive_score = score
                    elif 'NEGATIVE' in label or 'NEG' in label or label.startswith('LABEL_0'):
                        negative_score = score
                    elif 'NEUTRAL' in label or label.startswith('LABEL_1'):
                        # Neutral is considered slightly positive for email analysis
                        positive_score = max(positive_score, score * 0.3)
                
                # Calculate overall sentiment score (-1 to 1)
                sentiment_score = positive_score - negative_score
                
                print(f"Processed sentiment - Positive: {positive_score:.2f}, Negative: {negative_score:.2f}, Overall: {sentiment_score:.2f}", flush=True)
                
                return {
                    'sentiment_score': sentiment_score,
                    'positive_confidence': positive_score,
                    'negative_confidence': negative_score
                }
            
        except Exception as e:
            print(f"Error processing sentiment: {e}", flush=True)
            
        return {
            'sentiment_score': 0,
            'positive_confidence': 0,
            'negative_confidence': 0
        }
    
    def _get_verdict(self, overall_score: int) -> str:
        """Generate verdict based on overall score"""
        if overall_score >= 80:
            return "Excellent - This email is likely to get responses"
        elif overall_score >= 65:
            return "Good - Strong email with minor improvements needed"
        elif overall_score >= 45:
            return "Fair - Decent foundation but needs significant improvements"
        elif overall_score >= 25:
            return "Poor - Major issues that will hurt response rates"
        else:
            return "Very Poor - This email needs a complete rewrite"

# Usage example:
# hf_analyzer = HuggingFaceAnalyzer("your_hf_api_key")
# result = hf_analyzer.analyze_email_with_ai(subject, body)
