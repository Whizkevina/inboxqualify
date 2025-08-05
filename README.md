# InboxQualify 📧✨

**AI-Powered Cold Email Scoring & Analysis Tool**

> **⚠️ SECURITY NOTICE:** Before running this application, please complete the security setup by reading [SECURITY_SETUP.md](SECURITY_SETUP.md)

InboxQualify is a sophisticated web application that uses artificial intelligence to analyze and score your cold emails, providing actionable feedback to boost response rates and improve outreach effectiveness.

![InboxQualify Demo](https://img.shields.io/badge/Status-Live-brightgreen) ![Python](https://img.shields.io/badge/Python-3.12+-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green) ![AI](https://img.shields.io/badge/AI-Hugging%20Face-orange)

## 🚨 Quick Security Setup

1. **Copy environment template:** `cp .env.example .env`
2. **Edit `.env` with YOUR credentials** (never use defaults!)
3. **Read the full security guide:** [SECURITY_SETUP.md](SECURITY_SETUP.md)

## 🚀 What It Does

InboxQualify analyzes your cold emails across four critical dimensions:

- **📊 Relevance & Hook** (45 points): Personalization, research quality, and opening effectiveness
- **💰 Value Proposition** (30 points): Clarity of benefits, metrics, and recipient focus
- **📞 Call to Action** (15 points): Engagement level and friction assessment
- **🎯 Professionalism** (10 points): Tone, spam-avoidance, and optimal length

### Key Features

✅ **AI-Enhanced Scoring**: Combines Hugging Face sentiment analysis with rule-based evaluation  
✅ **Real-time Analysis**: Instant feedback with detailed breakdown  
✅ **Professional UI**: Modern, responsive SaaS-style interface  
✅ **Mobile Friendly**: Works seamlessly on all devices  
✅ **Actionable Feedback**: Specific suggestions for improvement  

## 🎯 How It Works

### The Analysis Process

1. **Input**: Paste your email subject line and body content
2. **AI Processing**: 
   - Hugging Face DistilBERT model analyzes sentiment and tone
   - Local rules engine evaluates structure and best practices
3. **Scoring**: Combined analysis generates score out of 100
4. **Feedback**: Detailed breakdown with specific improvement suggestions

### Scoring System

| Category | Max Points | What It Measures |
|----------|------------|------------------|
| **Relevance & Hook** | 45 | Personalization quality, specific research, authentic engagement |
| **Value Proposition** | 30 | Clear benefits, credible metrics, recipient-focused language |
| **Call to Action** | 15 | Low-friction requests, engaging questions |
| **Professionalism** | 10 | Appropriate tone, spam avoidance, optimal length |

### Score Interpretation

- **90-100**: Excellent - Likely to get responses
- **70-89**: Good - Minor improvements needed
- **50-69**: Fair - Significant improvements required  
- **Below 50**: Poor - Major revision needed

## 🛠️ Technical Architecture

### Backend (FastAPI + Python)
```
API/
├── main.py                 # FastAPI application & routing
├── huggingface_analyzer.py # AI sentiment analysis
└── local_analyzer.py       # Rule-based scoring engine
```

### Frontend (Vanilla JS + Modern CSS)
```
├── index.html              # Main application interface
├── css/styles.css          # Modern SaaS-style design system  
└── js/script.js            # API integration & UI handling
```

### AI Integration
- **Model**: `distilbert-base-uncased-finetuned-sst-2-english`
- **Provider**: Hugging Face Inference API
- **Fallback**: Local rule-based analysis ensures reliability
- **Rate Limit**: 30,000 requests/month (free tier)

## 🏃‍♂️ Quick Start

### Prerequisites
- Python 3.12+
- Hugging Face API key (free at [huggingface.co](https://huggingface.co))

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/inboxqualify.git
cd inboxqualify
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
# Create .env file
echo "HUGGINGFACE_API_KEY=your_api_key_here" > .env
```

4. **Run the application**
```bash
python -m uvicorn API.main:app --reload --host 127.0.0.1 --port 8000
```

5. **Open in browser**
```
http://127.0.0.1:8000
```

## 📁 Project Structure

```
inboxqualify/
├── API/
│   ├── __pycache__/           # Python cache (auto-generated)
│   ├── huggingface_analyzer.py # AI sentiment analysis
│   ├── local_analyzer.py      # Rule-based email scoring
│   └── main.py                # FastAPI backend server
├── css/
│   └── styles.css             # Modern SaaS design system
├── js/
│   └── script.js              # Frontend JavaScript
├── .env                       # Environment variables (create this)
├── .gitignore                 # Git ignore rules
├── enhanced_features.py       # Future feature ideas
├── index.html                 # Main web interface
├── README.md                  # This file
├── requirements.txt           # Python dependencies
└── test_email.json           # Sample test data
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the root directory:

```env
HUGGINGFACE_API_KEY=your_hugging_face_api_key_here
```

### API Endpoints
- `GET /`: Serve the main application
- `POST /qualify`: Analyze email content

### Request Format
```json
{
  "subject": "Your email subject line",
  "email_body": "Your email content here..."
}
```

### Response Format
```json
{
  "overallScore": 98,
  "verdict": "Excellent - This email is likely to get responses (AI Enhanced)",
  "breakdown": [
    {
      "name": "Relevance & Hook",
      "score": 45,
      "maxScore": 45,
      "feedback": "Strong personalization and research evident..."
    }
    // ... more categories
  ]
}
```

## 🎨 Design System

InboxQualify features a modern, professional design inspired by leading SaaS applications:

- **Typography**: Inter font family for optimal readability
- **Colors**: Sophisticated gray palette with blue accent gradients
- **Layout**: Mobile-first responsive design with CSS Grid
- **Components**: Card-based architecture with subtle shadows
- **Interactions**: Smooth animations and hover effects

## 🚀 Deployment Options

### Local Development
```bash
python -m uvicorn API.main:app --reload --host 127.0.0.1 --port 8000
```

### Production Deployment
Deploy to platforms like:
- **Railway**: Simple Python app deployment
- **Render**: Free tier available
- **Heroku**: Container-based deployment
- **DigitalOcean**: App Platform
- **AWS/GCP/Azure**: Cloud platform deployment

## 🤝 Contributing

Contributions are welcome! Here are some ways to help:

1. **Report bugs** or suggest features via Issues
2. **Improve documentation** 
3. **Add new analysis features** (see `enhanced_features.py` for ideas)
4. **Enhance the UI/UX**
5. **Add tests** for better reliability

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Submit a pull request with a clear description

## 📈 Future Enhancements

See `enhanced_features.py` for a comprehensive list of planned features:

- 📧 Email template generator
- 📊 Batch analysis for multiple emails
- 🔗 CRM integrations (HubSpot, Salesforce)
- 📱 Mobile app development
- 🧠 Multiple AI provider support
- 👥 Team collaboration features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Hugging Face** for providing excellent AI models and APIs
- **FastAPI** for the high-performance Python web framework
- **DistilBERT** for efficient sentiment analysis
- **Inter Font** for beautiful typography

## 📞 Support

Having issues? Here are some resources:

- 📖 **Documentation**: This README covers most use cases
- 🐛 **Bug Reports**: Open an issue with details and steps to reproduce
- 💡 **Feature Requests**: Share your ideas via GitHub Issues
- 📧 **Contact**: [Your email or contact method]

---

**Built with ❤️ for better cold email outreach**

*Transform your cold emails from ignored to irresistible with AI-powered analysis!*
