# local_analyzer.py - v1.1 - Rule-based email analyzer (no external API needed)

import re
from typing import Dict, List, Tuple

class LocalEmailAnalyzer:
    def __init__(self):
        # Keyword and pattern lists remain the same
        self.spam_words = [
            'free', 'guarantee', 'act now', 'limited time', 'urgent', 'act fast',
            'amazing deal', 'incredible offer', 'once in a lifetime', 'exclusive',
            'make money fast', 'get rich', 'no risk', 'risk free'
        ]
        self.professional_words = [
            'please', 'thank you', 'appreciate', 'respect', 'understand',
            'consider', 'opportunity', 'collaboration', 'partnership'
        ]
        self.value_words = [
            'save', 'increase', 'improve', 'reduce', 'optimize', 'streamline',
            'boost', 'enhance', 'grow', 'scale', 'efficiency', 'productivity'
        ]
        self.good_cta_patterns = [
            r'open to.*\?', r'interested in.*\?', r'would you.*\?',
            r'quick question', r'brief chat', r'quick call', r'thoughts on'
        ]
        self.bad_cta_patterns = [
            r'book.*demo', r'schedule.*meeting', r'sign up', r'buy now',
            r'call me', r'download.*now'
        ]

    def analyze_relevance_and_hook(self, subject: str, body: str) -> Tuple[int, str]:
        """Analyze relevance and personalization (max 45 points)"""
        score = 0
        feedback_parts = []
        
        # --- REFINED LOGIC v1.1 ---
        # 1. Check for a personalized greeting
        greeting_pattern = re.search(r'^(hi|hello)\s+([a-z]+),', body, re.IGNORECASE)
        if greeting_pattern:
            score += 15
            feedback_parts.append(f"Good start with a personalized greeting ('{greeting_pattern.group(0)}').")
        else:
            feedback_parts.append("Lacks a direct, personalized greeting like 'Hi [Name],'.")
            
        # 2. Check for research indicators
        research_indicators = [
            'noticed', 'saw', 'read', 'found', 'discovered', 'recent', 'expansion',
            'launch', 'announcement', 'news', 'article', 'post', 'comment', 'background'
        ]
        research_found = sum(1 for word in research_indicators if word.lower() in body.lower())
        
        if research_found >= 2:
            score += 20
            feedback_parts.append("Strong evidence of specific research about the recipient.")
        elif research_found == 1:
            score += 10
            feedback_parts.append("Shows some research effort.")
        else:
            feedback_parts.append("No clear signs of research beyond the name.")
            
        # 3. Penalize/reward generic praise
        generic_phrases = ['love your company', 'great company', 'amazing work', 'impressed by']
        if any(phrase in body.lower() for phrase in generic_phrases):
            score -= 5
            feedback_parts.append("Relies on generic flattery, which can feel insincere.")
        else:
            score += 10
            feedback_parts.append("Avoids generic flattery, making the personalization feel more authentic.")
        
        feedback = " ".join(feedback_parts)
        return max(0, min(45, score)), feedback

    def analyze_value_proposition(self, subject: str, body: str) -> Tuple[int, str]:
        """Analyze value proposition (max 30 points)"""
        score = 0
        feedback_parts = []
        
        # Check for value words
        value_mentions = sum(1 for word in self.value_words if word.lower() in body.lower())
        if value_mentions >= 2:
            score += 15
            feedback_parts.append("Clear value proposition with specific benefit-oriented words.")
        elif value_mentions == 1:
            score += 8
            feedback_parts.append("Some value mentioned but could be stronger and more direct.")
        else:
            feedback_parts.append("Weak or unclear value proposition. Focus on benefits like 'saving time' or 'increasing revenue'.")
            
        # Check for metrics/numbers
        if re.search(r'\d+%|\d+x|\$\d+', body):
            score += 10
            feedback_parts.append("Includes specific metrics which adds credibility.")
        else:
            feedback_parts.append("Could be strengthened by including specific metrics or numbers.")
            
        # --- REFINED LOGIC v1.1 ---
        # Penalize "I/we" focused language more intelligently
        i_we_count = len(re.findall(r'\b(i|we|our|my)\b', body.lower()))
        you_count = len(re.findall(r'\b(you|your)\b', body.lower()))
        
        if you_count >= i_we_count:
            score += 5
            feedback_parts.append("Good recipient-focused language.")
        elif i_we_count > you_count + 1: # Only penalize if significantly self-focused
            score -= 5
            feedback_parts.append("Language is too self-focused. Use 'you' and 'your' more often to center the recipient.")
            
        feedback = " ".join(feedback_parts)
        return max(0, min(30, score)), feedback

    def analyze_call_to_action(self, subject: str, body: str) -> Tuple[int, str]:
        """Analyze call to action (max 15 points)"""
        # This function's logic is solid, no changes needed
        score = 0
        feedback_parts = []
        
        good_cta_found = any(re.search(pattern, body.lower()) for pattern in self.good_cta_patterns)
        if good_cta_found:
            score += 10
            feedback_parts.append("Uses a low-friction, interest-gauging approach.")
        
        bad_cta_found = any(re.search(pattern, body.lower()) for pattern in self.bad_cta_patterns)
        if bad_cta_found:
            score -= 5
            feedback_parts.append("Contains high-friction demands, which can scare prospects away.")
        
        question_count = body.count('?')
        if question_count >= 1:
            score += 5
            feedback_parts.append("Includes engaging questions.")
        else:
            feedback_parts.append("Could benefit from an engaging question to prompt a reply.")
            
        if not good_cta_found and not bad_cta_found:
            feedback_parts.append("No clear call to action was identified.")
            
        feedback = " ".join(feedback_parts)
        return max(0, min(15, score)), feedback

    def analyze_professionalism(self, subject: str, body: str) -> Tuple[int, str]:
        """Analyze professionalism and clarity (max 10 points)"""
        # This function's logic is solid, no changes needed
        score = 10
        feedback_parts = []
        
        spam_found = sum(1 for word in self.spam_words if word.lower() in body.lower())
        if spam_found > 0:
            score -= spam_found * 2
            feedback_parts.append(f"Contains {spam_found} spam-like words.")
        else:
            feedback_parts.append("Avoids spam-like language.")
            
        professional_found = sum(1 for word in self.professional_words if word.lower() in body.lower())
        if professional_found >= 1:
            feedback_parts.append("Uses courteous language.")
        else:
            score -= 2
            feedback_parts.append("Tone could be improved with more courteous language (e.g., 'thank you', 'appreciate').")
            
        word_count = len(body.split())
        if 50 <= word_count <= 150:
            feedback_parts.append("Good length for a cold email.")
        elif word_count < 50:
            score -= 2
            feedback_parts.append("Email might be too brief to convey value.")
        else:
            score -= 2
            feedback_parts.append("Email is lengthy and could be more concise.")
            
        feedback = " ".join(feedback_parts)
        return max(0, min(10, score)), feedback

    def get_verdict(self, overall_score: int) -> str:
        """Generate verdict based on overall score"""
        # This function's logic is solid, no changes needed
        if overall_score >= 85:
            return "Excellent - This email is highly likely to get responses"
        elif overall_score >= 70:
            return "Good - Strong email with minor improvements needed"
        elif overall_score >= 50:
            return "Fair - Decent foundation but needs significant improvements"
        elif overall_score >= 30:
            return "Poor - Major issues that will hurt response rates"
        else:
            return "Very Poor - This email needs a complete rewrite"

    def analyze_email(self, subject: str, body: str) -> Dict:
        """Main analysis function"""
        # This function's logic is solid, no changes needed
        relevance_score, relevance_feedback = self.analyze_relevance_and_hook(subject, body)
        value_score, value_feedback = self.analyze_value_proposition(subject, body)
        cta_score, cta_feedback = self.analyze_call_to_action(subject, body)
        prof_score, prof_feedback = self.analyze_professionalism(subject, body)
        
        overall_score = relevance_score + value_score + cta_score + prof_score
        verdict = self.get_verdict(overall_score)
        
        return {
            "overallScore": overall_score,
            "verdict": verdict,
            "breakdown": [
                {"name": "Relevance & Hook", "score": relevance_score, "maxScore": 45, "feedback": relevance_feedback},
                {"name": "Value Proposition", "score": value_score, "maxScore": 30, "feedback": value_feedback},
                {"name": "Call to Action (CTA)", "score": cta_score, "maxScore": 15, "feedback": cta_feedback},
                {"name": "Professionalism", "score": prof_score, "maxScore": 10, "feedback": prof_feedback},
            ]
        }