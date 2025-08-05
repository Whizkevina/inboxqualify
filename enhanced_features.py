# enhanced_features.py - Additional features you could add

"""
🚀 FEATURE IDEAS FOR INBOXQUALIFY:

1. EMAIL TEMPLATES & SUGGESTIONS
   - Provide rewrite suggestions for poor emails
   - Template library for different industries
   - A/B testing recommendations

2. BATCH ANALYSIS
   - Upload CSV of emails for bulk analysis
   - Export results to spreadsheet
   - Campaign performance tracking

3. INTEGRATION FEATURES
   - Gmail/Outlook plugin
   - CRM integration (HubSpot, Salesforce)
   - Email automation platform connections

4. ADVANCED ANALYTICS
   - Industry-specific scoring
   - Sentiment analysis
   - Readability scoring
   - Subject line optimization

5. USER FEATURES
   - User accounts and history
   - Personal improvement tracking
   - Team collaboration features

6. AI ENHANCEMENTS
   - Multiple AI providers (OpenAI, Claude, etc.)
   - Custom training on your best emails
   - Real-time suggestions as you type

7. MOBILE APP
   - React Native or Flutter app
   - Push notifications for analysis
   - Offline analysis capability
"""

# Enhanced Email Template Generator with Suggestions
class EmailTemplateGenerator:
    def __init__(self):
        self.templates = {
            "saas": {
                "name": "SaaS Cold Outreach",
                "subject": "Quick question about {company}'s {pain_point}",
                "body": """Hi {name},

I noticed {specific_research_detail} about {company}.

I help {company_type} companies like yours {value_proposition} through {solution_method}.

Would you be open to a brief {duration} call to explore how this could {specific_benefit}?

Best regards,
{sender_name}""",
                "tips": [
                    "Keep subject line under 50 characters",
                    "Mention specific company research",
                    "Include clear value proposition",
                    "End with specific, low-commitment ask"
                ]
            },
            "ecommerce": {
                "name": "E-commerce Partnership",
                "subject": "Increasing {company}'s conversion rates",
                "body": """Hi {name},

I saw {specific_research_detail} and was impressed by {company}'s growth.

We've helped similar {industry} businesses increase {metric} by {percentage}% through {method}.

Would you be interested in a quick call to see how this might work for {company}?

Best,
{sender_name}""",
                "tips": [
                    "Reference specific company achievements",
                    "Use concrete metrics and percentages",
                    "Mention similar industry success",
                    "Keep email under 100 words"
                ]
            },
            "consulting": {
                "name": "Professional Services",
                "subject": "Thoughts on {company}'s {current_challenge}",
                "body": """Hi {name},

I've been following {company}'s journey in {industry} and particularly noted {specific_observation}.

Based on our work with {similar_companies}, I believe there's an opportunity to {improvement_area}.

Would you be open to a brief conversation about how we've helped similar organizations {specific_outcome}?

Best regards,
{sender_name}""",
                "tips": [
                    "Show you've researched their business",
                    "Reference similar client successes",
                    "Focus on outcomes, not features",
                    "Use consultative tone, not sales-y"
                ]
            },
            "finance": {
                "name": "Financial Services",
                "subject": "Cost optimization opportunity for {company}",
                "body": """Hi {name},

I noticed {company} recently {recent_event}. Congratulations on the growth!

We specialize in helping {company_size} companies in {industry} optimize {financial_area} and have achieved average savings of {percentage}%.

Would you be interested in a 15-minute call to explore potential opportunities?

Best,
{sender_name}""",
                "tips": [
                    "Reference recent company news",
                    "Use specific financial metrics",
                    "Mention relevant company size/industry",
                    "Suggest short, specific meeting duration"
                ]
            },
            "followup": {
                "name": "Follow-up Email",
                "subject": "Following up on {previous_topic}",
                "body": """Hi {name},

I wanted to follow up on our conversation about {previous_topic}.

Since we last spoke, {relevant_update}. This reminded me of the {specific_point} we discussed.

Would it be helpful to schedule a brief call to explore {next_steps}?

Best regards,
{sender_name}""",
                "tips": [
                    "Reference specific previous conversation",
                    "Provide relevant update or value",
                    "Suggest concrete next steps",
                    "Keep tone helpful, not pushy"
                ]
            }
        }
    
    def get_all_templates(self):
        """Return all available templates with metadata"""
        return {
            industry: {
                "name": template["name"],
                "preview": template["subject"],
                "tips_count": len(template["tips"])
            }
            for industry, template in self.templates.items()
        }
    
    def generate_template(self, industry: str, variables: dict = None):
        """Generate a complete email template"""
        if variables is None:
            variables = {}
            
        template = self.templates.get(industry, self.templates["saas"])
        
        # Fill in template with provided variables, or show placeholder
        try:
            subject = template["subject"].format(**variables) if variables else template["subject"]
            body = template["body"].format(**variables) if variables else template["body"]
        except KeyError as e:
            # If missing variables, return template with placeholders
            subject = template["subject"]
            body = template["body"]
        
        return {
            "name": template["name"],
            "subject": subject,
            "body": body,
            "tips": template["tips"],
            "variables_needed": self._extract_variables(template["subject"] + template["body"])
        }
    
    def _extract_variables(self, text):
        """Extract variable placeholders from template text"""
        import re
        return list(set(re.findall(r'\{(\w+)\}', text)))


class EmailSuggestionEngine:
    def __init__(self):
        self.improvement_rules = {
            "subject_length": {
                "rule": lambda subject: len(subject) > 50,
                "suggestion": "Subject line is too long. Keep it under 50 characters for better open rates.",
                "priority": "high"
            },
            "personalization": {
                "rule": lambda email: "{name}" not in email.lower() and "hi there" in email.lower(),
                "suggestion": "Add personalization by using the recipient's name instead of generic greetings.",
                "priority": "high"
            },
            "call_to_action": {
                "rule": lambda email: "?" not in email and "call" not in email.lower(),
                "suggestion": "Add a clear call-to-action. Consider asking for a specific meeting or response.",
                "priority": "medium"
            },
            "length": {
                "rule": lambda email: len(email.split()) > 150,
                "suggestion": "Email is too long. Keep cold emails under 150 words for better response rates.",
                "priority": "medium"
            },
            "value_proposition": {
                "rule": lambda email: not any(word in email.lower() for word in ["help", "increase", "improve", "save", "grow"]),
                "suggestion": "Include a clear value proposition. Mention how you can help, increase, improve, or save.",
                "priority": "high"
            },
            "social_proof": {
                "rule": lambda email: not any(word in email.lower() for word in ["helped", "clients", "customers", "companies"]),
                "suggestion": "Add social proof by mentioning other clients or companies you've helped.",
                "priority": "low"
            }
        }
    
    def analyze_email(self, subject: str, body: str):
        """Analyze email and provide improvement suggestions"""
        full_email = f"{subject} {body}"
        suggestions = []
        
        for rule_name, rule_data in self.improvement_rules.items():
            if rule_data["rule"](full_email):
                suggestions.append({
                    "type": rule_name,
                    "message": rule_data["suggestion"],
                    "priority": rule_data["priority"]
                })
        
        # Calculate improvement score
        total_rules = len(self.improvement_rules)
        passed_rules = total_rules - len(suggestions)
        improvement_score = int((passed_rules / total_rules) * 100)
        
        return {
            "improvement_score": improvement_score,
            "suggestions": sorted(suggestions, key=lambda x: {"high": 3, "medium": 2, "low": 1}[x["priority"]], reverse=True),
            "word_count": len(body.split()),
            "subject_length": len(subject)
        }


class EmailRewriter:
    def __init__(self):
        self.rewrite_rules = {
            "subject_optimization": {
                "max_length": 50,
                "power_words": ["Quick", "Regarding", "Question about", "Following up on", "Thoughts on"],
                "avoid_words": ["Amazing", "Incredible", "Revolutionary", "Best", "Free", "Act now"]
            },
            "personalization_fixes": {
                "generic_greetings": ["Hi there", "Dear Sir/Madam", "To whom it may concern"],
                "better_greetings": ["Hi {name}", "Hello {name}", "Good morning {name}"]
            },
            "structure_improvements": {
                "opening_templates": [
                    "I noticed {specific_detail} about {company}.",
                    "I've been following {company}'s work in {industry}.",
                    "Saw your recent {achievement/news} - congratulations!"
                ],
                "value_prop_templates": [
                    "We help {company_type} companies {specific_benefit}.",
                    "Based on our work with {similar_companies}, we typically see {specific_outcome}.",
                    "We specialize in helping {industry} businesses {improvement_area}."
                ],
                "cta_templates": [
                    "Would you be open to a brief {duration} call to discuss?",
                    "Are you available for a quick conversation about {specific_topic}?",
                    "Would it be helpful to explore how this might work for {company}?"
                ]
            }
        }
    
    def rewrite_subject(self, original_subject, company=None, specific_topic=None):
        """Rewrite subject line for better performance"""
        # Remove spam-like words
        cleaned_subject = original_subject
        for word in self.rewrite_rules["subject_optimization"]["avoid_words"]:
            cleaned_subject = cleaned_subject.replace(word, "")
        
        # Optimize length
        if len(cleaned_subject) > 50:
            # Try to make it more concise
            if company and specific_topic:
                cleaned_subject = f"Question about {company}'s {specific_topic}"
            elif company:
                cleaned_subject = f"Quick question about {company}"
            else:
                # Truncate and add ellipsis
                cleaned_subject = cleaned_subject[:47] + "..."
        
        return cleaned_subject.strip()
    
    def rewrite_email_body(self, original_body, suggestions, context=None):
        """Rewrite email body based on suggestions"""
        if context is None:
            context = {}
        
        # Extract company, name, and other details from context or make placeholders
        company = context.get("company", "{company}")
        name = context.get("name", "{name}")
        industry = context.get("industry", "{industry}")
        specific_detail = context.get("specific_detail", "{specific_research_detail}")
        
        # Start building the rewritten email
        rewritten_parts = []
        
        # 1. Improved greeting
        if any(s["type"] == "personalization" for s in suggestions):
            rewritten_parts.append(f"Hi {name},")
        else:
            rewritten_parts.append("Hi {name},")
        
        rewritten_parts.append("")  # Empty line
        
        # 2. Strong opening with research
        opening_templates = self.rewrite_rules["structure_improvements"]["opening_templates"]
        opening = opening_templates[0].format(
            specific_detail=specific_detail,
            company=company,
            industry=industry
        )
        rewritten_parts.append(opening)
        rewritten_parts.append("")
        
        # 3. Value proposition
        value_prop_templates = self.rewrite_rules["structure_improvements"]["value_prop_templates"]
        value_prop = value_prop_templates[0].format(
            company_type=f"{industry}",
            specific_benefit=context.get("benefit", "increase efficiency and reduce costs"),
            similar_companies=f"similar {industry} companies",
            specific_outcome=context.get("outcome", "20-30% improvement in key metrics"),
            improvement_area=context.get("improvement_area", "optimize operations")
        )
        rewritten_parts.append(value_prop)
        rewritten_parts.append("")
        
        # 4. Social proof (if suggested)
        if any(s["type"] == "social_proof" for s in suggestions):
            social_proof = f"We've helped companies like {context.get('similar_company', '{similar_company}')} achieve {context.get('specific_result', 'significant improvements')}."
            rewritten_parts.append(social_proof)
            rewritten_parts.append("")
        
        # 5. Clear call to action
        cta_templates = self.rewrite_rules["structure_improvements"]["cta_templates"]
        cta = cta_templates[0].format(
            duration=context.get("meeting_duration", "15-minute"),
            specific_topic=context.get("discussion_topic", "potential opportunities"),
            company=company
        )
        rewritten_parts.append(cta)
        rewritten_parts.append("")
        
        # 6. Professional closing
        rewritten_parts.append("Best regards,")
        rewritten_parts.append(context.get("sender_name", "{your_name}"))
        
        return "\n".join(rewritten_parts)
    
    def generate_rewrite_suggestions(self, original_subject, original_body, suggestions):
        """Generate specific rewrite suggestions"""
        rewrite_suggestions = []
        
        for suggestion in suggestions:
            if suggestion["type"] == "subject_length":
                rewrite_suggestions.append({
                    "area": "Subject Line",
                    "issue": "Too long for optimal open rates",
                    "suggestion": "Make it more concise and specific",
                    "example": self.rewrite_subject(original_subject)
                })
            
            elif suggestion["type"] == "personalization":
                rewrite_suggestions.append({
                    "area": "Greeting",
                    "issue": "Generic or missing personalization",
                    "suggestion": "Use recipient's name and mention company research",
                    "example": "Hi {name}, I noticed {specific_detail} about {company}."
                })
            
            elif suggestion["type"] == "value_proposition":
                rewrite_suggestions.append({
                    "area": "Value Proposition",
                    "issue": "Unclear how you help clients",
                    "suggestion": "Be specific about benefits and outcomes",
                    "example": "We help {industry} companies increase {metric} by {percentage}% through {method}."
                })
            
            elif suggestion["type"] == "call_to_action":
                rewrite_suggestions.append({
                    "area": "Call to Action",
                    "issue": "Missing or weak call to action",
                    "suggestion": "Include specific, low-commitment ask",
                    "example": "Would you be open to a brief 15-minute call to explore how this might work for {company}?"
                })
            
            elif suggestion["type"] == "length":
                rewrite_suggestions.append({
                    "area": "Email Length",
                    "issue": "Email is too long",
                    "suggestion": "Keep cold emails under 150 words",
                    "example": "Focus on: Research → Value Prop → Social Proof → CTA"
                })
            
            elif suggestion["type"] == "social_proof":
                rewrite_suggestions.append({
                    "area": "Social Proof",
                    "issue": "Missing credibility indicators",
                    "suggestion": "Mention similar clients or results",
                    "example": "We've helped similar {industry} companies achieve {specific_outcome}."
                })
        
        return rewrite_suggestions
    
    def full_rewrite(self, original_subject, original_body, suggestions, context=None):
        """Perform a complete email rewrite"""
        if context is None:
            context = {}
        
        # Generate rewritten subject
        new_subject = self.rewrite_subject(original_subject, context.get("company"), context.get("topic"))
        
        # Generate rewritten body
        new_body = self.rewrite_email_body(original_body, suggestions, context)
        
        # Generate specific suggestions for each area
        rewrite_suggestions = self.generate_rewrite_suggestions(original_subject, original_body, suggestions)
        
        # Calculate word counts
        original_words = len(original_body.split())
        new_words = len(new_body.split())
        
        return {
            "original": {
                "subject": original_subject,
                "body": original_body,
                "word_count": original_words,
                "subject_length": len(original_subject)
            },
            "rewritten": {
                "subject": new_subject,
                "body": new_body,
                "word_count": new_words,
                "subject_length": len(new_subject)
            },
            "improvements": {
                "word_reduction": original_words - new_words,
                "subject_optimization": len(original_subject) - len(new_subject),
                "areas_improved": len(rewrite_suggestions)
            },
            "rewrite_suggestions": rewrite_suggestions,
            "estimated_improvement": min(95, 60 + len(rewrite_suggestions) * 8)  # Estimated score improvement
        }


import csv
import io
import uuid
from datetime import datetime
from typing import List, Dict, Any

class BatchAnalyzer:
    def __init__(self, suggestion_engine, email_rewriter):
        self.suggestion_engine = suggestion_engine
        self.email_rewriter = email_rewriter
        self.batch_results = {}  # Store batch results temporarily
        
    def parse_csv_content(self, csv_content: str) -> List[Dict[str, Any]]:
        """Parse CSV content and extract email data"""
        emails = []
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        # Try to detect column names automatically
        fieldnames = csv_reader.fieldnames
        if not fieldnames:
            raise ValueError("CSV file appears to be empty or invalid")
        
        # Map common column variations to standard names
        column_mapping = self._detect_columns(fieldnames)
        
        for i, row in enumerate(csv_reader):
            try:
                email_data = {
                    'id': i + 1,
                    'subject': row.get(column_mapping.get('subject', ''), '').strip(),
                    'body': row.get(column_mapping.get('body', ''), '').strip(),
                    'sender_name': row.get(column_mapping.get('sender_name', ''), '').strip(),
                    'sender_email': row.get(column_mapping.get('sender_email', ''), '').strip(),
                    'company': row.get(column_mapping.get('company', ''), '').strip(),
                    'industry': row.get(column_mapping.get('industry', ''), '').strip(),
                    'original_row': row
                }
                
                # Skip rows without subject or body
                if email_data['subject'] or email_data['body']:
                    emails.append(email_data)
                    
            except Exception as e:
                # Log error but continue processing
                print(f"Error processing row {i + 1}: {e}")
                continue
                
        return emails
    
    def _detect_columns(self, fieldnames) -> Dict[str, str]:
        """Automatically detect column mappings"""
        mapping = {}
        
        # Column variations for different fields
        subject_variations = ['subject', 'subject_line', 'email_subject', 'title', 'headline']
        body_variations = ['body', 'email_body', 'content', 'message', 'text', 'email_content']
        sender_name_variations = ['sender_name', 'name', 'sender', 'from_name', 'author']
        sender_email_variations = ['sender_email', 'email', 'from_email', 'sender_address']
        company_variations = ['company', 'company_name', 'organization', 'business']
        industry_variations = ['industry', 'sector', 'vertical', 'category']
        
        # Find best matches (case insensitive)
        for field in fieldnames:
            field_lower = field.lower()
            
            if not mapping.get('subject') and any(var in field_lower for var in subject_variations):
                mapping['subject'] = field
            elif not mapping.get('body') and any(var in field_lower for var in body_variations):
                mapping['body'] = field
            elif not mapping.get('sender_name') and any(var in field_lower for var in sender_name_variations):
                mapping['sender_name'] = field
            elif not mapping.get('sender_email') and any(var in field_lower for var in sender_email_variations):
                mapping['sender_email'] = field
            elif not mapping.get('company') and any(var in field_lower for var in company_variations):
                mapping['company'] = field
            elif not mapping.get('industry') and any(var in field_lower for var in industry_variations):
                mapping['industry'] = field
        
        return mapping
    
    def analyze_batch(self, emails: List[Dict[str, Any]], include_rewrite: bool = False) -> Dict[str, Any]:
        """Analyze a batch of emails"""
        batch_id = str(uuid.uuid4())
        results = []
        summary_stats = {
            'total_emails': len(emails),
            'processed_emails': 0,
            'average_score': 0,
            'score_distribution': {'poor': 0, 'fair': 0, 'good': 0, 'excellent': 0},
            'common_issues': {},
            'processing_time': 0
        }
        
        start_time = datetime.now()
        total_score = 0
        
        for email_data in emails:
            try:
                # Analyze email
                analysis = self.suggestion_engine.analyze_email(
                    email_data['subject'], 
                    email_data['body']
                )
                
                result = {
                    'id': email_data['id'],
                    'subject': email_data['subject'],
                    'body': email_data['body'][:200] + '...' if len(email_data['body']) > 200 else email_data['body'],
                    'sender_name': email_data['sender_name'],
                    'sender_email': email_data['sender_email'],
                    'company': email_data['company'],
                    'industry': email_data['industry'],
                    'score': analysis['improvement_score'],
                    'word_count': analysis['word_count'],
                    'subject_length': analysis['subject_length'],
                    'suggestions': analysis['suggestions'],
                    'suggestion_count': len(analysis['suggestions']),
                    'priority_issues': [s for s in analysis['suggestions'] if s['priority'] == 'high']
                }
                
                # Add rewrite if requested
                if include_rewrite and analysis['suggestions']:
                    context = {
                        'company': email_data['company'],
                        'name': 'recipient',
                        'industry': email_data['industry']
                    }
                    rewrite_result = self.email_rewriter.full_rewrite(
                        email_data['subject'],
                        email_data['body'],
                        analysis['suggestions'],
                        context
                    )
                    result['rewrite'] = rewrite_result
                
                results.append(result)
                total_score += analysis['improvement_score']
                summary_stats['processed_emails'] += 1
                
                # Update score distribution
                score = analysis['improvement_score']
                if score < 40:
                    summary_stats['score_distribution']['poor'] += 1
                elif score < 60:
                    summary_stats['score_distribution']['fair'] += 1
                elif score < 80:
                    summary_stats['score_distribution']['good'] += 1
                else:
                    summary_stats['score_distribution']['excellent'] += 1
                
                # Track common issues
                for suggestion in analysis['suggestions']:
                    issue_type = suggestion['type']
                    if issue_type in summary_stats['common_issues']:
                        summary_stats['common_issues'][issue_type] += 1
                    else:
                        summary_stats['common_issues'][issue_type] = 1
                        
            except Exception as e:
                # Add error result but continue processing
                results.append({
                    'id': email_data['id'],
                    'subject': email_data['subject'],
                    'error': str(e),
                    'score': 0,
                    'suggestions': [],
                    'suggestion_count': 0
                })
                continue
        
        # Calculate final stats
        if summary_stats['processed_emails'] > 0:
            summary_stats['average_score'] = round(total_score / summary_stats['processed_emails'], 1)
        
        summary_stats['processing_time'] = (datetime.now() - start_time).total_seconds()
        
        batch_result = {
            'batch_id': batch_id,
            'timestamp': start_time.isoformat(),
            'summary': summary_stats,
            'results': results,
            'column_mapping_detected': True
        }
        
        # Store temporarily (in production, save to database)
        self.batch_results[batch_id] = batch_result
        
        return batch_result
    
    def generate_csv_report(self, batch_result: Dict[str, Any]) -> str:
        """Generate CSV report from batch analysis"""
        output = io.StringIO()
        
        # Define CSV columns
        fieldnames = [
            'ID', 'Subject', 'Body_Preview', 'Sender_Name', 'Sender_Email', 
            'Company', 'Industry', 'Score', 'Word_Count', 'Subject_Length',
            'Suggestion_Count', 'Priority_Issues', 'Top_Issue', 'Top_Suggestion'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in batch_result['results']:
            if 'error' in result:
                row = {
                    'ID': result['id'],
                    'Subject': result['subject'],
                    'Score': 0,
                    'Top_Issue': f"ERROR: {result['error']}"
                }
            else:
                top_suggestion = result['suggestions'][0] if result['suggestions'] else None
                row = {
                    'ID': result['id'],
                    'Subject': result['subject'],
                    'Body_Preview': result['body'],
                    'Sender_Name': result['sender_name'],
                    'Sender_Email': result['sender_email'],
                    'Company': result['company'],
                    'Industry': result['industry'],
                    'Score': result['score'],
                    'Word_Count': result['word_count'],
                    'Subject_Length': result['subject_length'],
                    'Suggestion_Count': result['suggestion_count'],
                    'Priority_Issues': len(result['priority_issues']),
                    'Top_Issue': top_suggestion['type'] if top_suggestion else 'None',
                    'Top_Suggestion': top_suggestion['message'] if top_suggestion else 'No issues found'
                }
            
            writer.writerow(row)
        
        return output.getvalue()
    
    def get_batch_result(self, batch_id: str):
        """Retrieve batch result by ID"""
        return self.batch_results.get(batch_id)


class CampaignTracker:
    def __init__(self):
        self.campaigns = {}
    
    def create_campaign(self, name: str, description: str = "") -> str:
        """Create a new email campaign"""
        campaign_id = str(uuid.uuid4())
        self.campaigns[campaign_id] = {
            'id': campaign_id,
            'name': name,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'batches': [],
            'total_emails': 0,
            'average_score': 0,
            'improvement_trend': []
        }
        return campaign_id
    
    def add_batch_to_campaign(self, campaign_id: str, batch_result: Dict[str, Any]):
        """Add a batch analysis to a campaign"""
        if campaign_id in self.campaigns:
            campaign = self.campaigns[campaign_id]
            campaign['batches'].append({
                'batch_id': batch_result['batch_id'],
                'timestamp': batch_result['timestamp'],
                'email_count': batch_result['summary']['total_emails'],
                'average_score': batch_result['summary']['average_score']
            })
            
            # Update campaign stats
            campaign['total_emails'] += batch_result['summary']['total_emails']
            
            # Calculate overall average
            total_score = sum(batch['average_score'] * batch['email_count'] for batch in campaign['batches'])
            campaign['average_score'] = round(total_score / campaign['total_emails'], 1)
            
            # Track improvement trend
            campaign['improvement_trend'] = [batch['average_score'] for batch in campaign['batches']]
    
    def get_campaign_stats(self, campaign_id: str):
        """Get comprehensive campaign statistics"""
        if campaign_id not in self.campaigns:
            return {}
            
        campaign = self.campaigns[campaign_id]
        
        # Calculate trend
        trend = "stable"
        if len(campaign['improvement_trend']) >= 2:
            recent_avg = sum(campaign['improvement_trend'][-2:]) / 2
            older_avg = sum(campaign['improvement_trend'][:-2]) / max(1, len(campaign['improvement_trend']) - 2)
            
            if recent_avg > older_avg + 5:
                trend = "improving"
            elif recent_avg < older_avg - 5:
                trend = "declining"
        
        return {
            **campaign,
            'trend': trend,
            'batch_count': len(campaign['batches']),
            'latest_batch': campaign['batches'][-1] if campaign['batches'] else None
        }
