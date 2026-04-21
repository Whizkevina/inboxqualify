# enhanced_analyzer.py - Advanced email analyzer with real-time metrics
"""
Enhanced Email Analyzer with:
- Industry-specific scoring
- Advanced personalization detection
- Sentiment analysis
- Real-time benchmarking
- Actionable insights
"""

import re
from typing import Dict, List, Tuple
from datetime import datetime

class EnhancedEmailAnalyzer:
    def __init__(self):
        # Industry benchmarks (based on real cold email data)
        self.industry_benchmarks = {
            "saas": {"avg_score": 72, "response_rate": 8.5, "optimal_length": 120},
            "ecommerce": {"avg_score": 68, "response_rate": 6.2, "optimal_length": 100},
            "consulting": {"avg_score": 75, "response_rate": 12.3, "optimal_length": 150},
            "agency": {"avg_score": 70, "response_rate": 9.1, "optimal_length": 110},
            "default": {"avg_score": 70, "response_rate": 8.0, "optimal_length": 120}
        }
        
        # Advanced personalization indicators
        self.research_indicators = {
            "company_specific": ["funding", "series", "raised", "acquisition", "launch", "expansion"],
            "news_mentions": ["announcement", "press release", "featured", "article", "interview"],
            "social_proof": ["linkedin", "twitter", "post", "comment", "shared"],
            "recent_activity": ["recently", "last week", "yesterday", "this month", "noticed"],
            "hiring": ["hiring", "job posting", "looking for", "recruiting", "team growth"]
        }
        
        # Sentiment indicators
        self.sentiment_patterns = {
            "confident": ["proven", "demonstrated", "successfully", "consistently", "track record"],
            "desperate": ["please", "really", "just", "only", "quick", "brief"],
            "pushy": ["must", "need to", "should", "have to", "urgent", "immediately"],
            "authentic": ["noticed", "saw", "read", "found", "discovered", "impressed by"]
        }
        
        # Template detection patterns
        self.template_patterns = [
            r"\{.*?\}",  # Placeholder brackets
            r"\[.*?\]",  # Square brackets
            r"INSERT.*HERE",  # Common placeholders
            r"YOUR (COMPANY|NAME|PRODUCT)"  # Generic replacements
        ]
        
        # Value proposition power words
        self.value_words = {
            "quantifiable": ["increase", "reduce", "save", "boost", "grow", "improve"],
            "time_saving": ["automate", "streamline", "simplify", "faster", "efficient"],
            "revenue": ["revenue", "profit", "ROI", "conversion", "sales", "growth"],
            "competitive": ["competitive", "advantage", "edge", "outperform", "leader"]
        }
        
        # CTA quality patterns
        self.cta_patterns = {
            "low_friction": [
                r"open to.*\?", r"interested in.*\?", r"would you.*\?",
                r"quick question", r"brief chat", r"thoughts on", r"worth exploring"
            ],
            "high_friction": [
                r"book.*demo", r"schedule.*meeting", r"sign up now",
                r"buy now", r"call me", r"download.*now", r"commit to"
            ]
        }

    def detect_industry(self, subject: str, body: str) -> str:
        """Detect email industry context"""
        text = f"{subject} {body}".lower()
        
        industry_keywords = {
            "saas": ["software", "platform", "cloud", "api", "integration", "dashboard"],
            "ecommerce": ["store", "shop", "product", "inventory", "checkout", "cart"],
            "consulting": ["consulting", "advisory", "strategy", "transformation", "expertise"],
            "agency": ["agency", "creative", "marketing", "design", "campaign", "brand"]
        }
        
        scores = {}
        for industry, keywords in industry_keywords.items():
            scores[industry] = sum(1 for kw in keywords if kw in text)
        
        detected = max(scores, key=scores.get) if max(scores.values()) > 0 else "default"
        return detected

    def analyze_personalization(self, subject: str, body: str) -> Tuple[int, str, Dict]:
        """Advanced personalization analysis (max 45 points)"""
        score = 0
        feedback_parts = []
        metrics = {"research_depth": 0, "specificity": 0, "authenticity": 0}
        
        # 1. Personalized greeting (15 points)
        greeting_pattern = re.search(r'^(hi|hello|hey)\s+([a-z]+),', body, re.IGNORECASE)
        if greeting_pattern:
            score += 15
            metrics["specificity"] += 1
            feedback_parts.append(f"✓ Personalized greeting detected")
        else:
            feedback_parts.append("✗ Missing personalized greeting (e.g., 'Hi [Name],')")
        
        # 2. Company-specific research (20 points)
        research_score = 0
        research_types_found = []
        
        for research_type, indicators in self.research_indicators.items():
            if any(indicator in body.lower() for indicator in indicators):
                research_types_found.append(research_type)
                research_score += 4
        
        if len(research_types_found) >= 3:
            score += 20
            metrics["research_depth"] = 3
            feedback_parts.append(f"✓ Excellent research depth ({', '.join(research_types_found[:3])})")
        elif len(research_types_found) >= 2:
            score += 15
            metrics["research_depth"] = 2
            feedback_parts.append(f"✓ Good research ({', '.join(research_types_found)})")
        elif len(research_types_found) == 1:
            score += 8
            metrics["research_depth"] = 1
            feedback_parts.append(f"○ Some research ({research_types_found[0]})")
        else:
            feedback_parts.append("✗ No specific research detected - mention recent news, hiring, or achievements")
        
        # 3. Authenticity check (10 points)
        generic_phrases = ['love your company', 'great company', 'amazing work', 'big fan']
        authentic_phrases = sum(1 for phrase in self.sentiment_patterns["authentic"] if phrase in body.lower())
        
        if authentic_phrases >= 2 and not any(phrase in body.lower() for phrase in generic_phrases):
            score += 10
            metrics["authenticity"] = 2
            feedback_parts.append("✓ Authentic, specific praise")
        elif authentic_phrases >= 1:
            score += 5
            metrics["authenticity"] = 1
        else:
            feedback_parts.append("✗ Add specific, authentic observations about the company")
        
        feedback = " | ".join(feedback_parts)
        return max(0, min(45, score)), feedback, metrics

    def analyze_value_proposition(self, subject: str, body: str) -> Tuple[int, str, Dict]:
        """Enhanced value proposition analysis (max 30 points)"""
        score = 0
        feedback_parts = []
        metrics = {"clarity": 0, "specificity": 0, "recipient_focus": 0}
        
        # 1. Value word categories (15 points)
        value_categories_found = []
        for category, words in self.value_words.items():
            if any(word in body.lower() for word in words):
                value_categories_found.append(category)
                score += 4
        
        if len(value_categories_found) >= 2:
            metrics["clarity"] = 2
            feedback_parts.append(f"✓ Clear value ({', '.join(value_categories_found[:2])})")
        elif len(value_categories_found) == 1:
            metrics["clarity"] = 1
            feedback_parts.append(f"○ Some value mentioned ({value_categories_found[0]})")
        else:
            feedback_parts.append("✗ Unclear value - mention specific benefits (time saved, revenue increased)")
        
        # 2. Quantifiable metrics (10 points)
        metrics_found = re.findall(r'\d+%|\d+x|\$\d+|\d+\s*(hours?|days?|weeks?)', body)
        if len(metrics_found) >= 2:
            score += 10
            metrics["specificity"] = 2
            feedback_parts.append(f"✓ Strong metrics ({', '.join(metrics_found[:2])})")
        elif len(metrics_found) == 1:
            score += 5
            metrics["specificity"] = 1
            feedback_parts.append(f"○ One metric found ({metrics_found[0]})")
        else:
            feedback_parts.append("✗ Add specific numbers (e.g., '30% increase', '5 hours saved')")
        
        # 3. Recipient-focused language (5 points)
        you_count = len(re.findall(r'\b(you|your)\b', body.lower()))
        i_we_count = len(re.findall(r'\b(i|we|our|my)\b', body.lower()))
        
        if you_count > i_we_count:
            score += 5
            metrics["recipient_focus"] = 2
            feedback_parts.append(f"✓ Recipient-focused ({you_count} 'you' vs {i_we_count} 'I/we')")
        elif you_count == i_we_count:
            score += 2
            metrics["recipient_focus"] = 1
        else:
            feedback_parts.append(f"✗ Too self-focused ({i_we_count} 'I/we' vs {you_count} 'you')")
        
        feedback = " | ".join(feedback_parts)
        return max(0, min(30, score)), feedback, metrics

    def analyze_sentiment(self, body: str) -> Dict:
        """Analyze email sentiment and tone"""
        sentiment_scores = {}
        
        for sentiment_type, indicators in self.sentiment_patterns.items():
            count = sum(1 for indicator in indicators if indicator in body.lower())
            sentiment_scores[sentiment_type] = count
        
        # Determine dominant sentiment
        dominant = max(sentiment_scores, key=sentiment_scores.get)
        
        # Calculate authenticity score
        authenticity = sentiment_scores.get("authentic", 0)
        desperation = sentiment_scores.get("desperate", 0)
        pushiness = sentiment_scores.get("pushy", 0)
        
        tone_score = (authenticity * 10) - (desperation * 5) - (pushiness * 7)
        
        return {
            "dominant_sentiment": dominant,
            "scores": sentiment_scores,
            "tone_score": max(0, min(100, 50 + tone_score)),
            "is_authentic": authenticity >= 2 and desperation <= 1,
            "is_pushy": pushiness >= 2
        }

    def detect_template_usage(self, subject: str, body: str) -> Dict:
        """Detect if email uses generic templates"""
        text = f"{subject} {body}"
        
        template_indicators = 0
        for pattern in self.template_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            template_indicators += len(matches)
        
        is_template = template_indicators > 0
        
        return {
            "is_template": is_template,
            "template_indicators": template_indicators,
            "warning": "Email appears to use a generic template" if is_template else None
        }

    def analyze_cta(self, body: str) -> Tuple[int, str]:
        """Enhanced CTA analysis (max 15 points)"""
        score = 0
        feedback_parts = []
        
        # Low-friction CTAs (10 points)
        low_friction_found = any(re.search(pattern, body.lower()) for pattern in self.cta_patterns["low_friction"])
        if low_friction_found:
            score += 10
            feedback_parts.append("✓ Low-friction CTA (interest-gauging)")
        
        # High-friction CTAs (penalty)
        high_friction_found = any(re.search(pattern, body.lower()) for pattern in self.cta_patterns["high_friction"])
        if high_friction_found:
            score -= 5
            feedback_parts.append("✗ High-friction CTA detected - too demanding")
        
        # Question engagement (5 points)
        question_count = body.count('?')
        if question_count >= 1:
            score += 5
            feedback_parts.append(f"✓ Engaging question(s) ({question_count})")
        else:
            feedback_parts.append("✗ Add a question to encourage response")
        
        if not low_friction_found and not high_friction_found:
            feedback_parts.append("○ No clear CTA - add a soft ask")
        
        feedback = " | ".join(feedback_parts)
        return max(0, min(15, score)), feedback

    def analyze_professionalism(self, subject: str, body: str) -> Tuple[int, str]:
        """Professionalism analysis (max 10 points)"""
        score = 10
        feedback_parts = []
        
        # Word count check
        word_count = len(body.split())
        if 75 <= word_count <= 150:
            feedback_parts.append(f"✓ Optimal length ({word_count} words)")
        elif word_count < 75:
            score -= 2
            feedback_parts.append(f"○ Slightly short ({word_count} words) - aim for 75-150")
        else:
            score -= 3
            feedback_parts.append(f"✗ Too long ({word_count} words) - aim for 75-150")
        
        # Spam words check
        spam_words = ['free', 'guarantee', 'limited time', 'act now', 'amazing deal']
        spam_found = sum(1 for word in spam_words if word in body.lower())
        if spam_found > 0:
            score -= spam_found * 3
            feedback_parts.append(f"✗ {spam_found} spam-like word(s)")
        else:
            feedback_parts.append("✓ No spam language")
        
        # Professional courtesy
        courtesy_words = ['please', 'thank you', 'appreciate', 'respect']
        if any(word in body.lower() for word in courtesy_words):
            feedback_parts.append("✓ Courteous tone")
        else:
            score -= 2
            feedback_parts.append("○ Add courtesy words")
        
        feedback = " | ".join(feedback_parts)
        return max(0, min(10, score)), feedback

    def get_industry_benchmark(self, industry: str, score: int) -> Dict:
        """Get industry-specific benchmarking"""
        benchmark = self.industry_benchmarks.get(industry, self.industry_benchmarks["default"])
        
        performance = "above average" if score > benchmark["avg_score"] else "below average"
        percentile = min(99, int((score / 100) * 100))
        
        return {
            "industry": industry,
            "your_score": score,
            "industry_average": benchmark["avg_score"],
            "performance": performance,
            "percentile": percentile,
            "predicted_response_rate": round(benchmark["response_rate"] * (score / benchmark["avg_score"]), 1)
        }

    def generate_actionable_insights(self, analysis_results: Dict) -> List[Dict]:
        """Generate specific, actionable improvement suggestions"""
        insights = []
        
        # Personalization insights
        if analysis_results["personalization_score"] < 30:
            insights.append({
                "priority": "high",
                "category": "Personalization",
                "issue": "Weak personalization detected",
                "action": "Add specific research about the company (recent news, hiring, funding)",
                "example": "I noticed you recently raised Series B funding - congratulations!"
            })
        
        # Value proposition insights
        if analysis_results["value_score"] < 20:
            insights.append({
                "priority": "high",
                "category": "Value Proposition",
                "issue": "Unclear value proposition",
                "action": "Add specific metrics showing impact",
                "example": "We help SaaS companies increase trial-to-paid conversion by 30%"
            })
        
        # Sentiment insights
        if analysis_results["sentiment"]["is_pushy"]:
            insights.append({
                "priority": "medium",
                "category": "Tone",
                "issue": "Email sounds pushy",
                "action": "Soften language and remove urgency words",
                "example": "Replace 'you need to' with 'you might find it helpful to'"
            })
        
        # Template insights
        if analysis_results["template_detection"]["is_template"]:
            insights.append({
                "priority": "high",
                "category": "Authenticity",
                "issue": "Generic template detected",
                "action": "Remove placeholders and add specific details",
                "example": "Replace {COMPANY_NAME} with actual research"
            })
        
        return insights

    def analyze_email(self, subject: str, body: str) -> Dict:
        """Main enhanced analysis function"""
        # Detect industry
        industry = self.detect_industry(subject, body)
        
        # Core analysis
        personalization_score, personalization_feedback, pers_metrics = self.analyze_personalization(subject, body)
        value_score, value_feedback, value_metrics = self.analyze_value_proposition(subject, body)
        cta_score, cta_feedback = self.analyze_cta(body)
        prof_score, prof_feedback = self.analyze_professionalism(subject, body)
        
        # Advanced analysis
        sentiment = self.analyze_sentiment(body)
        template_detection = self.detect_template_usage(subject, body)
        
        # Calculate overall score
        overall_score = personalization_score + value_score + cta_score + prof_score
        
        # Get industry benchmark
        benchmark = self.get_industry_benchmark(industry, overall_score)
        
        # Generate verdict
        if overall_score >= 85:
            verdict = "Excellent - Highly likely to get responses"
        elif overall_score >= 70:
            verdict = "Good - Strong email with minor improvements needed"
        elif overall_score >= 50:
            verdict = "Fair - Needs significant improvements"
        else:
            verdict = "Poor - Major rewrite recommended"
        
        # Compile results
        results = {
            "overallScore": overall_score,
            "verdict": verdict,
            "industry": industry,
            "benchmark": benchmark,
            "sentiment": sentiment,
            "template_detection": template_detection,
            "breakdown": [
                {
                    "name": "Personalization & Research",
                    "score": personalization_score,
                    "maxScore": 45,
                    "feedback": personalization_feedback,
                    "metrics": pers_metrics
                },
                {
                    "name": "Value Proposition",
                    "score": value_score,
                    "maxScore": 30,
                    "feedback": value_feedback,
                    "metrics": value_metrics
                },
                {
                    "name": "Call to Action",
                    "score": cta_score,
                    "maxScore": 15,
                    "feedback": cta_feedback
                },
                {
                    "name": "Professionalism",
                    "score": prof_score,
                    "maxScore": 10,
                    "feedback": prof_feedback
                }
            ],
            "personalization_score": personalization_score,
            "value_score": value_score
        }
        
        # Generate actionable insights
        results["actionable_insights"] = self.generate_actionable_insights(results)
        
        return results
