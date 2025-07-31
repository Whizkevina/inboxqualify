# 📊 InboxQualify Admin Dashboard

## Overview

The InboxQualify Admin Dashboard provides comprehensive analytics and monitoring for your email analysis application. Track usage patterns, monitor AI API consumption, and gain insights into how users interact with your service.

## 🔧 Setup

### 1. Initial Configuration

Run the setup script to configure admin credentials:

```bash
python setup_admin.py
```

This will prompt you to:
- Set admin username (default: admin)  
- Set secure admin password (minimum 8 characters)
- Configure environment variables

### 2. Access Dashboard

Once your server is running, access the admin dashboard at:

**Local Development:** `http://localhost:8000/admin`  
**Production:** `https://yourdomain.com/admin`

Use the credentials you set during setup to log in.

## 📈 Dashboard Features

### Key Metrics (30-day overview)
- **Total Requests**: Number of email analyses performed
- **Success Rate**: Percentage of successful vs failed requests  
- **Unique Users**: Count of distinct IP addresses
- **Average Score**: Mean email quality score
- **AI Enhanced**: Requests processed with AI vs local analysis
- **Processing Time**: Average response time in milliseconds

### 🤖 API Usage Monitoring
- **Hugging Face Usage**: Track API requests and estimated token consumption
- **Monthly Limits**: Monitor usage against free tier limits (30,000 requests/month)
- **Usage Percentage**: Visual progress bar showing API consumption
- **Cost Estimation**: Approximate usage costs

### 📊 Visual Analytics
- **Daily Usage Chart**: 7-day trend of requests and AI usage
- **Hourly Patterns**: Today's usage by hour
- **Success/Failure Rates**: Request success tracking

### 🚨 Error Monitoring
- **Top Errors**: Most frequent error messages
- **Error Frequency**: Count of each error type
- **Real-time Alerts**: Monitor system health

### 🔄 Real-time Features
- **Auto-refresh**: Dashboard updates every 30 seconds
- **Manual Refresh**: On-demand data updates
- **Live Metrics**: Current system status

## 🛡️ Security Features

### Authentication
- **Basic HTTP Authentication**: Username/password protection
- **Environment Variables**: Credentials stored securely in `.env`
- **Admin-only Access**: Dashboard hidden from regular users

### Data Protection
- **SQLite Database**: Local analytics storage
- **IP Anonymization**: User privacy protection
- **Secure Headers**: HTTP security best practices

## 📊 Database Schema

The analytics system uses SQLite with three main tables:

### `usage_logs`
- Request-level tracking with IP, user agent, scores, timing
- Error logging with detailed messages
- AI enhancement tracking

### `daily_stats`  
- Aggregated daily metrics
- Unique user counts
- Success/failure rates

### `api_usage`
- API provider usage tracking
- Token consumption logs
- Cost monitoring

## 🔧 Configuration Options

### Environment Variables

Add these to your `.env` file:

```env
# Admin Access
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_secure_password

# API Keys
HUGGINGFACE_API_KEY=your_hf_api_key

# Optional: Database path
ANALYTICS_DB_PATH=analytics.db
```

### Customization

The dashboard can be customized by modifying:

- `admin_dashboard.py`: Backend logic and data processing
- `admin_templates/dashboard.html`: Frontend appearance and charts
- Analytics tracking in `API/main.py`: Request logging behavior

## 📱 Mobile Responsive

The dashboard is fully responsive and works on:
- Desktop computers
- Tablets  
- Mobile phones
- All modern browsers

## 🚀 Production Deployment

### Security Considerations
1. **Change default credentials** immediately
2. **Use HTTPS** in production
3. **Restrict admin access** by IP if possible
4. **Regular backup** of analytics database

### Performance
- Dashboard loads quickly with minimal resource usage
- SQLite database scales to millions of requests
- Efficient queries with proper indexing

### Monitoring
- Built-in health check endpoint: `/health`
- API status monitoring
- Error rate tracking

## 🎯 Use Cases

### Business Intelligence
- Track user engagement and growth
- Identify popular features and usage patterns
- Monitor service reliability and performance

### Technical Monitoring  
- API quota management
- Error tracking and debugging
- Performance optimization insights

### Product Development
- User behavior analysis
- Feature usage statistics
- Quality score distributions

## 📞 Troubleshooting

### Common Issues

**Dashboard not accessible:**
- Check admin credentials in `.env`
- Verify server is running with admin module
- Check for error messages in server logs

**Missing data:**
- Ensure analytics database is writable
- Check that requests are being logged
- Verify database initialization

**Charts not loading:**
- Check browser console for JavaScript errors
- Ensure Chart.js CDN is accessible
- Verify data format in API responses

### Support
For technical support or feature requests, check the main application documentation or create an issue in the project repository.

---

*The admin dashboard provides powerful insights while maintaining user privacy and system security.*
