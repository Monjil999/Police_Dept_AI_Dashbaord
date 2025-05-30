# 🚔 Police Data Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-red)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()

**Advanced police data analytics powered by AI - From raw data to actionable insights in seconds**

Transform police department data into comprehensive analytics dashboards with AI-powered natural language querying. Built for transparency, accountability, and data-driven policing insights.


<img width="1422" alt="image" src="https://github.com/user-attachments/assets/c8aa803c-c381-444f-9da2-fd164fe56a06" />


## 🌟 Key Features

### 📊 **Multi-Department Analytics**
- **4 Major Police Departments**: Seattle, Philadelphia, Chicago, Los Angeles
- **Real-time Data**: Direct integration with Stanford Open Policing Project
- **Memory-Optimized Processing**: Chunked loading with 50-70% memory reduction

### 🤖 **AI-Powered Q&A Interface**
- **Natural Language Queries**: Ask questions in plain English
- **Sub-10 Second Responses**: Powered by Groq's DeepSeek-R1-Distill-Llama-70B
- **Intelligent SQL Generation**: Automatic text-to-SQL conversion
- **Pattern Recognition**: Smart query templates for common questions

### 📈 **CompStat-Style Dashboard**
- **12 Key Metrics**: Total stops, arrest rates, citation rates, warning rates
- **5 Interactive Tabs**: Overview, Analysis, Temporal, Demographics, Geography
- **Real-time Filtering**: Filter by race, gender, district, time period
- **Performance Optimized**: Sub-45 second dashboard loads

### 🗺️ **Geospatial Analytics**
- **Interactive Heat Maps**: Stop patterns by location and time
- **District Analysis**: Geographic distribution of police activities
- **Coordinate Mapping**: Precise location-based insights

### **Memory Optimization**
- **Chunked Data Loading**: Process large datasets in 50K row chunks
- **Data Type Optimization**: Automatic downcasting reduces memory by 50-70%
- **Smart Categorization**: Convert low-cardinality strings to categories
- **Efficient Storage**: Use appropriate integer sizes (int8, int16, uint8, etc.)
- **Cloud-Compatible**: Handles 5M+ records within 1GB memory limits

## 🚀 Quick Start

### Prerequisites

```bash
Python 3.8+
Streamlit 1.28+
```

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Monjil999/Police_Dept_AI_Dashbaord.git
cd Police_Dept_AI_Dashbaord
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables** (Optional)
```bash
# Create .env file
echo "GROQ_API_KEY=your_groq_api_key_here" > .env
echo "REDIS_URL=redis://localhost:6379/0" >> .env
```

4. **Run the application**
```bash
streamlit run app.py
```

5. **Open in browser**
```
http://localhost:8501
```

## 🔐 API Configuration

### Option 1: Environment Variable (Recommended)
```bash
export GROQ_API_KEY="your_groq_api_key_here"
```

### Option 2: User Input (In-App)
1. Get your free API key from [Groq Console](https://console.groq.com/keys)
2. Enter it in the sidebar under "🔐 API Configuration"
3. Start asking questions about police data!

### Option 3: .env File
```bash
# .env file
GROQ_API_KEY=your_groq_api_key_here
REDIS_URL=redis://localhost:6379/0
```

## 📖 Usage Guide

### 1. **Select Police Department**
Choose from 4 major departments:
- **Seattle Police Department** (319,959 records, memory-optimized)
- **Philadelphia Police Department** (1.8M+ records, chunked processing)
- **Chicago Police Department** (846K records, memory-optimized)
- **Los Angeles Police Department** (5.4M+ records, chunked processing)

### 2. **Explore the Dashboard**
Navigate through 5 interactive tabs:

#### 📊 **Overview Tab**
- Executive summary with key statistics
- Stop outcome distribution
- Dataset metadata and performance metrics

#### 🔍 **Analysis Tab**
- Stop patterns by race and demographics
- Peak hour analysis with hourly breakdowns
- Comparative analytics across categories

#### 📈 **Temporal Tab**
- Time-series analysis of police stops
- Monthly and yearly trend identification
- Seasonal pattern recognition

#### 👥 **Demographics Tab**
- Race, gender, and age distribution analysis
- Cross-demographic comparisons
- District-wise demographic breakdowns

#### 🗺️ **Geography Tab**
- Interactive heat maps of stop locations
- District-wise activity mapping
- Geographic pattern identification

### 3. **AI-Powered Q&A**
Ask natural language questions:

```
"How many blacks were arrested?"
"What are the peak hours for police stops?"
"Show me arrest counts by race"
"Which district has the most stops?"
"Compare citation rates between races"
```

## 🏗️ Technical Architecture

### **Data Pipeline**
```
Stanford Open Policing Project → Data Fetcher → SQLite Database → Redis Cache → Dashboard
```

### **AI Stack**
- **LLM Model**: Groq API with DeepSeek-R1-Distill-Llama-70B
- **Text-to-SQL**: Custom prompt engineering with schema awareness  
- **Performance**: Sub-10 second response times
- **Fallback**: Pattern matching for common queries

### **Visualization Stack**
- **Frontend**: Streamlit with custom CSS
- **Charts**: Plotly Express for interactive visualizations
- **Maps**: Plotly geographic plotting
- **Caching**: Redis + SQLite for optimal performance

### **Security Features**
- **API Key Protection**: No hardcoded keys in source code
- **User Key Input**: Secure password-masked input field
- **Environment Variables**: Support for .env configuration
- **Data Privacy**: Local processing, no external data sharing

## 📁 Project Structure

```
Police_Dept_AI_Dashbaord/
├── app.py                    # Main Streamlit application
├── config.py                 # Configuration and settings
├── data_fetcher.py          # Real data downloading and processing
├── database.py              # SQLite and Redis database management  
├── llm_agent.py             # AI query processing and SQL generation
├── dashboard.py             # Dashboard visualization components
├── user_input_interface.py  # Advanced user requirements collection
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore file
└── README.md               # This file
```

## 🔧 Configuration Options

### **Performance Settings**
```python
MAX_DASHBOARD_LOAD_TIME = 45    # seconds
MAX_LLM_RESPONSE_TIME = 10      # seconds
CACHE_EXPIRY = 3600            # 1 hour
```

### **Data Sources**
- **Primary**: Stanford Open Policing Project
- **Backup**: City-specific open data portals
- **Format**: CSV (ZIP compressed), Excel
- **Update Frequency**: Real-time downloads

### **Database Configuration**
```python
DATABASE_URL = "sqlite:///police_data.db"
REDIS_URL = "redis://localhost:6379/0"
```

## 📊 Sample Analytics

### **Key Performance Indicators**
- **Total Stops**: 8.4M+ across all departments
- **Geographic Coverage**: 4 major US cities
- **Time Range**: 2006-2023 (varies by department)
- **Data Points**: 23-83 columns per department

### **Dashboard Metrics**
| Metric | Description | Availability |
|--------|-------------|-------------|
| Total Stops | Number of police stops | ✅ All departments |
| Arrest Rate | Percentage resulting in arrest | ✅ All departments |
| Citation Rate | Percentage resulting in citation | ✅ Seattle, Philadelphia |
| Warning Rate | Percentage resulting in warning | ✅ Seattle, Philadelphia |
| Peak Hour | Hour with most stops | ✅ All departments |
| Top District | District with most activity | ✅ Where available |

## 🚦 Performance Benchmarks

- **Dashboard Load Time**: < 45 seconds (Target achieved)
- **AI Response Time**: < 10 seconds (Target achieved)  
- **Data Processing**: Chunked loading with 50-70% memory reduction
- **Cache Hit Rate**: 95%+ for repeated queries
- **Memory Usage**: ~600MB total (optimized data types + chunked processing)

## 🔍 Troubleshooting

### **Common Issues**

1. **"API key not configured"**
   - Solution: Add your Groq API key in sidebar or environment variable

2. **"Data download failed"**
   - Solution: Check internet connection, try different department

3. **"Query generation failed"**
   - Solution: Verify API key, try simpler question format

4. **Dashboard not loading**
   - Solution: Refresh page, check browser console for errors

### **Debug Features**
- **Debug info** in sidebar: Data loaded status, API key status
- **Performance metrics**: Load times and response times
- **Error logging**: Detailed error messages in console

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open Pull Request**

### **Development Setup**
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Format code
black .
flake8 .
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Stanford Open Policing Project** for comprehensive police data
- **Groq** for high-performance AI inference
- **Streamlit** for rapid web app development
- **Police Data Initiative** for open data standards

---

**Built with ❤️ for police transparency and data-driven accountability**

[![GitHub stars](https://img.shields.io/github/stars/Monjil999/Police_Dept_AI_Dashbaord.svg?style=social&label=Star)](https://github.com/Monjil999/Police_Dept_AI_Dashbaord)
[![GitHub forks](https://img.shields.io/github/forks/Monjil999/Police_Dept_AI_Dashbaord.svg?style=social&label=Fork)](https://github.com/Monjil999/Police_Dept_AI_Dashbaord/fork)
