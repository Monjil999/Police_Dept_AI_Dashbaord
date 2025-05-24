# 🚀 Deployment Guide - Police Data Analytics Platform

This guide covers different deployment options for the Police Data Analytics Platform.

## 📋 Prerequisites

- Python 3.8+
- Git
- Groq API Key (free at [console.groq.com](https://console.groq.com/keys))

## 🎯 Quick Deploy Options

### 1. **Local Development (Recommended for Testing)**

```bash
# Clone the repository
git clone https://github.com/Monjil999/Police_Dept_AI_Dashbaord.git
cd Police_Dept_AI_Dashbaord

# Install dependencies
pip install -r requirements.txt

# Set your API key
export GROQ_API_KEY="your_groq_api_key_here"

# Run the application
streamlit run app.py

# Access at: http://localhost:8501
```

### 2. **Streamlit Cloud (Free Hosting)**

1. **Fork this repository** to your GitHub account

2. **Deploy to Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Select your forked repository
   - Set branch: `main`
   - Set main file path: `app.py`
   - Click "Deploy"

3. **Configure Secrets:**
   - In Streamlit Cloud dashboard, go to "Secrets"
   - Add your API key:
   ```toml
   GROQ_API_KEY = "your_groq_api_key_here"
   ```

4. **Your app will be live at:** `https://your-app-name.streamlit.app`

### 3. **Docker Deployment**

```bash
# Build the Docker image
docker build -t police-analytics .

# Run with environment variables
docker run -p 8501:8501 \
  -e GROQ_API_KEY="your_groq_api_key_here" \
  police-analytics

# Access at: http://localhost:8501
```

### 4. **Heroku Deployment**

```bash
# Install Heroku CLI and login
heroku login

# Create new Heroku app
heroku create your-police-analytics-app

# Set environment variables
heroku config:set GROQ_API_KEY="your_groq_api_key_here"

# Deploy
git push heroku main

# Your app will be at: https://your-police-analytics-app.herokuapp.com
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file (copy from `.env.example`):

```bash
# Required
GROQ_API_KEY=your_groq_api_key_here

# Optional
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=sqlite:///police_data.db
MAX_DASHBOARD_LOAD_TIME=45
MAX_LLM_RESPONSE_TIME=10
```

### Performance Optimization

For production deployments:

1. **Install Redis** for better caching:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install redis-server
   
   # macOS
   brew install redis
   ```

2. **Configure database** for larger datasets:
   ```python
   # In config.py, increase memory limits
   CACHE_EXPIRY = 3600  # 1 hour
   MAX_RECORDS_DISPLAY = 10000
   ```

## 🚦 Performance Targets

- **Dashboard Load**: < 45 seconds
- **AI Response**: < 10 seconds  
- **Data Processing**: 1M records in ~10 seconds
- **Memory Usage**: ~2GB for largest datasets

## 🔍 Troubleshooting

### Common Issues

1. **Module not found errors:**
   ```bash
   pip install -r requirements.txt
   ```

2. **API key errors:**
   - Verify your Groq API key is valid
   - Check environment variables are set correctly

3. **Data download failures:**
   - Check internet connection
   - Try different police department

4. **Performance issues:**
   - Install Redis for better caching
   - Increase system memory if processing large datasets

## 🔐 Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** for sensitive configuration
3. **Enable HTTPS** in production deployments
4. **Regularly update dependencies** for security patches

## 📊 Monitoring

### Health Checks

The application exposes these metrics:
- Dashboard load times
- AI response times
- Database query performance
- Cache hit rates

### Logs

Monitor application logs for:
- API errors
- Database connection issues
- Performance bottlenecks
- User interaction patterns

## 🆘 Support

- **GitHub Issues**: [Report bugs](https://github.com/Monjil999/Police_Dept_AI_Dashbaord/issues)
- **Discussions**: [Get help](https://github.com/Monjil999/Police_Dept_AI_Dashbaord/discussions)

---

**Successfully deployed? ⭐ Star this repository to show your support!** 