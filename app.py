import streamlit as st
import pandas as pd
import time
import logging
from typing import Optional

# Import our custom modules
from data_fetcher import RealDataFetcher
from database import DatabaseManager
from llm_agent import PoliceDataLLMAgent
from dashboard import PoliceDashboard
from config import MAX_DASHBOARD_LOAD_TIME, GROQ_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Streamlit
st.set_page_config(
    page_title="Police Data Analytics",
    page_icon="🚔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #ff7f0e;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .error-box {
        background-color: #ffebee;
        border-left: 5px solid #f44336;
        padding: 1rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #e8f5e8;
        border-left: 5px solid #4caf50;
        padding: 1rem;
        margin: 1rem 0;
    }
    .latency-info {
        background-color: #fff3e0;
        border-left: 5px solid #ff9800;
        padding: 0.5rem;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

class PoliceAnalyticsApp:
    def __init__(self):
        self.data_fetcher = RealDataFetcher()
        self.db_manager = DatabaseManager()
        self.dashboard = PoliceDashboard()
        
        # Initialize session state
        if 'data_loaded' not in st.session_state:
            st.session_state.data_loaded = False
        if 'current_department' not in st.session_state:
            st.session_state.current_department = None
        if 'current_data' not in st.session_state:
            st.session_state.current_data = None
        if 'load_time' not in st.session_state:
            st.session_state.load_time = None
        if 'user_api_key' not in st.session_state:
            st.session_state.user_api_key = None
    
    def render_header(self):
        """Render the application header."""
        st.markdown('<h1 class="main-header">🚔 Police Data Analytics Platform</h1>', unsafe_allow_html=True)
        st.markdown("""
        **Advanced police data analytics powered by AI - From raw data to actionable insights in seconds**
        
        ✨ **Stretch Goals Implemented:**
        - 🔍 **Live Department Search**: Search any police department across both major data portals
        - 📊 **Multi-Tab Dashboard**: 5 comprehensive tabs with executive summary, search analysis, temporal trends, demographics, and geospatial mapping
        - 🎛️ **Advanced Filtering**: Date, time, demographics, location, and incident-specific filters with real-time record counts
        - 🗺️ **Geospatial Heat Maps**: Interactive maps showing stop patterns by district and time
        - 🤖 **AI-Powered Q&A**: Natural language queries with sub-10 second responses using Groq's deepseek-r1-distill-llama-70b
        - ⚡ **Performance Optimized**: Sub-45 second dashboard loads with intelligent caching
        
        🎯 **Core Features:**
        - **Live Data Discovery**: Search across Stanford Open Policing and Police Data Initiative datasets
        - **CompStat-style Dashboard**: Interactive visualizations with KPIs for search rates, hit rates, use of force, and demographics
        - **Natural Language Interface**: Ask complex questions in plain English and get instant SQL-powered answers
        """)
        st.divider()
    
    def render_department_selection(self):
        """Render department selection interface."""
        # Add the detailed user requirements interface
        with st.expander("🔧 **Advanced: Specify Detailed Data Requirements**", expanded=False):
            st.markdown("""
            For more specific data requirements, use our detailed questionnaire:
            """)
            
            if st.button("📋 **Open Detailed Requirements Form**"):
                st.session_state.show_requirements = True
            
            if st.session_state.get('show_requirements', False):
                from user_input_interface import collect_user_requirements
                requirements = collect_user_requirements()
                if requirements:
                    st.session_state.user_requirements = requirements
                    st.session_state.show_requirements = False
                    st.rerun()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Live search input for departments
            search_mode = st.radio(
                "Search Mode:",
                ["Quick Select", "Live Search"],
                horizontal=True,
                help="Quick Select shows predefined departments, Live Search allows you to search for any department"
            )
            
            if search_mode == "Quick Select":
                available_departments = self.data_fetcher.get_available_departments()
                selected_department = st.selectbox(
                    "Choose a police department to analyze:",
                    options=available_departments,
                    index=0,  # Default to Seattle PD
                    help="Select from major police departments with available real data from official sources"
                )
            else:
                selected_department = st.text_input(
                    "Enter police department name:",
                    value="Seattle Police Department",
                    placeholder="e.g., Seattle Police Department, NYPD, LAPD, etc.",
                    help="Type the name of any police department to search for data"
                )
                
                # Show data sources being searched
                st.info("""
                🔍 **Searching in official sources:**
                • Stanford Open Policing Project (https://openpolicing.stanford.edu/data/)
                • Police Data Initiative (https://www.policedatainitiative.org/datasets/)
                • City/State open data portals as backup sources
                """)
        
        # Initialize the return values
        data_loaded = False
        
        with col2:
            if st.button("🔍 Load Data", type="primary"):
                if selected_department:
                    data_loaded = self.load_department_data(selected_department)
                else:
                    st.error("Please enter a department name first!")
        
        # Show current user requirements if any
        if hasattr(st.session_state, 'user_requirements'):
            with st.expander("📋 **Your Current Requirements**"):
                requirements = st.session_state.user_requirements
                st.write(f"**Data Source:** {requirements.get('data_source', 'Not specified')}")
                st.write(f"**Location:** {requirements.get('location', {}).get('value', 'Not specified')}")
                st.write(f"**Data Types:** {', '.join(requirements.get('data_types', ['Not specified']))}")
                st.write(f"**Time Period:** {requirements.get('time_period', {}).get('preference', 'Not specified')}")
                st.write(f"**Data Size:** {requirements.get('data_size', {}).get('type', 'Not specified')}")
                
                if st.button("🗑️ Clear Requirements"):
                    del st.session_state.user_requirements
                    st.rerun()
        
        # Always return a tuple
        return selected_department, data_loaded
    
    def load_department_data(self, department: str) -> bool:
        """Load data for the selected department."""
        start_time = time.time()
        
        with st.spinner(f"🔍 Searching for {department} data..."):
            # Search for data sources
            data_sources = self.data_fetcher.find_department_data(department)
            
            if not data_sources:
                st.error(f"❌ Data not found for {department}")
                return False
            
            # Display found data sources
            st.success(f"✅ Found {len(data_sources)} data source(s) for {department}")
            
            for i, source in enumerate(data_sources):
                with st.expander(f"📊 Data Source {i+1}: {source['source']}"):
                    st.write(f"**Format:** {source['format']}")
                    st.write(f"**Last Updated:** {source['last_updated']}")
                    st.write(f"**Description:** {source['description']}")
                    st.write(f"**URL:** {source['url']}")
        
        with st.spinner("📥 Downloading and processing data..."):
            # Use the first data source for now
            primary_source = data_sources[0]
            
            # Download and preview data
            df, metadata = self.data_fetcher.download_and_preview_data(primary_source)
            
            if df is None:
                st.error(f"❌ Failed to download data: {metadata.get('error', 'Unknown error')}")
                return False
            
            # Store data in database
            table_name = self.db_manager.store_police_data(department, df, metadata)
            
            if not table_name:
                st.error("❌ Failed to store data in database")
                return False
        
        load_time = time.time() - start_time
        
        # Update session state
        st.session_state.data_loaded = True
        st.session_state.current_department = department
        st.session_state.current_data = df
        st.session_state.load_time = load_time
        
        # Display loading performance
        performance_color = "success" if load_time <= MAX_DASHBOARD_LOAD_TIME else "error"
        performance_icon = "✅" if load_time <= MAX_DASHBOARD_LOAD_TIME else "⚠️"
        
        st.markdown(f"""
        <div class="latency-info">
            {performance_icon} <strong>Dashboard Load Time:</strong> {load_time:.2f} seconds 
            (Target: ≤{MAX_DASHBOARD_LOAD_TIME}s)
        </div>
        """, unsafe_allow_html=True)
        
        # Display metadata
        with st.expander("📋 Dataset Metadata"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Rows", f"{metadata['rows']:,}")
            with col2:
                st.metric("Columns", len(metadata['columns']))
            with col3:
                st.metric("Memory Usage", f"{metadata['memory_usage']:.1f} MB")
            
            st.write(f"**Date Range:** {metadata['date_range']['start_date']} to {metadata['date_range']['end_date']}")
            st.write(f"**Download Time:** {metadata['download_time']:.2f} seconds")
            
            # Show column names
            st.write("**Columns:**", ", ".join(metadata['columns']))
        
        # Force UI update to show all sections
        st.success("🎉 Data loaded successfully! The dashboard and AI Q&A features are now available.")
        time.sleep(1)  # Brief pause to let user see the success message
        st.rerun()
        
        return True
    
    def render_dashboard(self):
        """Render the dashboard section."""
        if not st.session_state.data_loaded:
            st.info("👆 Please select and load a department's data first to view the dashboard.")
            return
        
        st.markdown('<h2 class="sub-header">2. CompStat-style Dashboard</h2>', unsafe_allow_html=True)
        
        # Apply filters
        filtered_data = self.dashboard.create_filtered_view(st.session_state.current_data.copy())
        
        # Render the dashboard
        self.dashboard.render_dashboard(filtered_data, st.session_state.current_department)
    
    def render_llm_interface(self):
        """Render the LLM Q&A interface."""
        st.subheader("🤖 3. AI-Powered Q&A Interface")
        
        # Check if LLM is available
        effective_api_key = st.session_state.user_api_key or GROQ_API_KEY
        
        if not effective_api_key:
            st.warning("⚠️ **AI Q&A features are currently disabled**")
            st.info("""
            To enable AI-powered queries:
            1. Get a free API key from [Groq Console](https://console.groq.com/keys)
            2. Enter it in the sidebar under "🔐 API Configuration"
            3. Start asking questions about the police data!
            """)
            return
        
        # Sample questions
        with st.expander("💡 Sample Questions You Can Ask"):
            sample_questions = self.get_llm_agent().get_sample_questions()
            for i, question in enumerate(sample_questions, 1):
                st.write(f"{i}. {question}")
        
        # Question input
        user_question = st.text_input(
            "Ask a question about the police data:",
            placeholder="e.g., How many arrests were made by race?",
            help="Ask questions in natural language - the AI will convert them to SQL queries"
        )
        
        if user_question and st.button("🔍 Ask Question", type="primary"):
            self.process_user_question(user_question)
    
    def process_user_question(self, question: str):
        """Process a user question using the LLM agent."""
        with st.spinner("🧠 AI is analyzing the data..."):
            result = self.get_llm_agent().execute_query_and_explain(question, st.session_state.current_department)
        
        if result['success']:
            # Display performance metrics
            latency_color = "success" if result['within_threshold'] else "warning"
            latency_icon = "✅" if result['within_threshold'] else "⚠️"
            
            st.markdown(f"""
            <div class="latency-info">
                {latency_icon} <strong>Response Time:</strong> {result['latency']:.2f} seconds 
                (Target: ≤10s) | <strong>SQL Generation:</strong> {result['generation_time']:.2f}s
            </div>
            """, unsafe_allow_html=True)
            
            # Display explanation
            st.markdown(f"""
            <div class="success-box">
                <strong>📊 Analysis Results:</strong><br>
                {result['explanation']}
            </div>
            """, unsafe_allow_html=True)
            
            # Display SQL query in expander
            with st.expander("🔍 View Generated SQL Query"):
                st.code(result['sql_query'], language='sql')
            
            # Display results
            if not result['results'].empty:
                st.subheader("📈 Query Results")
                
                # Show as table
                st.dataframe(result['results'], use_container_width=True)
                
                # Try to create a visualization if appropriate
                self.create_query_visualization(result['results'], question)
            
        else:
            st.markdown(f"""
            <div class="error-box">
                <strong>❌ Query Failed:</strong><br>
                {result['error']}
            </div>
            """, unsafe_allow_html=True)
            
            if 'sql_query' in result:
                with st.expander("🔍 View Generated SQL Query"):
                    st.code(result['sql_query'], language='sql')
    
    def create_query_visualization(self, df: pd.DataFrame, question: str):
        """Create visualization for query results."""
        if len(df) == 0:
            return
        
        try:
            import plotly.express as px
            
            # Determine visualization type based on data
            if len(df.columns) >= 2:
                numeric_cols = df.select_dtypes(include=['number']).columns
                categorical_cols = df.select_dtypes(include=['object', 'category']).columns
                
                if len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
                    # Bar chart for categorical vs numeric
                    x_col = categorical_cols[0]
                    y_col = numeric_cols[0]
                    
                    fig = px.bar(df, x=x_col, y=y_col, title=f"Results for: {question}")
                    st.plotly_chart(fig, use_container_width=True)
                
                elif len(numeric_cols) >= 2:
                    # Scatter plot for numeric vs numeric
                    fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1], title=f"Results for: {question}")
                    st.plotly_chart(fig, use_container_width=True)
        
        except Exception as e:
            logger.error(f"Error creating visualization: {e}")
    
    def render_footer(self):
        """Render application footer."""
        st.divider()
        
        st.markdown("""
        ### 🏗️ Technical Architecture
        
        **Data Pipeline:**
        - Live search across Stanford Open Policing and Police Data Initiative
        - Automated data download and caching in SQLite database
        - Redis caching for improved performance
        
        **AI Stack:**
        - **LLM Model:** Groq API with deepseek-r1-distill-llama-70b
        - **Text-to-SQL:** Custom prompt engineering with schema awareness
        - **Performance:** Sub-10 second response times for most queries
        
        **Visualization:**
        - Interactive Plotly charts and maps
        - Real-time filtering and data exploration
        - CompStat-style KPI dashboards
        """)
        
        # Performance summary
        if st.session_state.load_time:
            st.info(f"📊 **Performance Summary:** Dashboard loaded in {st.session_state.load_time:.2f}s | Ready for sub-10s AI queries")
    
    def render_api_key_input(self):
        """Render API key input in sidebar."""
        st.sidebar.header("🔐 API Configuration")
        
        # Check if system has default API key
        has_system_key = GROQ_API_KEY is not None
        
        if has_system_key:
            st.sidebar.success("✅ System API key available")
            use_own_key = st.sidebar.checkbox("Use your own API key", value=False)
            
            if use_own_key:
                user_api_key = st.sidebar.text_input(
                    "Enter your Groq API key:",
                    type="password",
                    help="Get your free API key from: https://console.groq.com/keys"
                )
                if user_api_key:
                    st.session_state.user_api_key = user_api_key
                    st.sidebar.success("✅ Using your API key")
                else:
                    st.session_state.user_api_key = None
            else:
                st.session_state.user_api_key = None
        else:
            st.sidebar.warning("⚠️ No system API key configured")
            st.sidebar.info("💡 To use AI features, please provide your Groq API key")
            
            user_api_key = st.sidebar.text_input(
                "Enter your Groq API key:",
                type="password",
                help="Get your free API key from: https://console.groq.com/keys"
            )
            
            if user_api_key:
                if st.session_state.user_api_key != user_api_key:
                    st.session_state.user_api_key = user_api_key
                    # Force a rerun to update the UI
                    st.rerun()
                st.sidebar.success("✅ API key configured")
            else:
                st.sidebar.error("❌ AI features disabled without API key")
                st.session_state.user_api_key = None
        
        # Show API key status
        effective_api_key = st.session_state.user_api_key or GROQ_API_KEY
        if effective_api_key:
            st.sidebar.info("🤖 AI Q&A features: **Enabled**")
        else:
            st.sidebar.warning("🤖 AI Q&A features: **Disabled**")
        
        # Debug info (can be removed later)
        st.sidebar.divider()
        st.sidebar.caption("Debug Info:")
        st.sidebar.caption(f"Data loaded: {st.session_state.data_loaded}")
        st.sidebar.caption(f"Current dept: {st.session_state.current_department}")
        st.sidebar.caption(f"API key set: {bool(effective_api_key)}")
        
        # Add a refresh button if data is loaded but not showing
        if st.session_state.data_loaded and st.sidebar.button("🔄 Refresh Interface"):
            st.rerun()
    
    def get_llm_agent(self) -> PoliceDataLLMAgent:
        """Get LLM agent with appropriate API key."""
        user_api_key = st.session_state.get('user_api_key')
        return PoliceDataLLMAgent(api_key=user_api_key)
    
    def render_main_interface(self):
        """Render the main interface when data is loaded."""
        # Dashboard
        self.render_dashboard()
        
        st.divider()
        
        # LLM Interface
        self.render_llm_interface()
        
        # Footer
        self.render_footer()
    
    def run(self):
        """Run the main application."""
        self.render_header()
        
        # Render API key input in sidebar
        self.render_api_key_input()
        
        # Always show department selection first
        if not st.session_state.data_loaded:
            st.subheader("1. Select Police Department")
            self.render_department_selection()
        else:
            # Show all sections when data is loaded
            st.subheader("📊 Data Successfully Loaded!")
            st.success(f"✅ **{st.session_state.current_department}** data is ready for analysis ({len(st.session_state.current_data):,} records)")
            
            # Option to load different department
            with st.expander("🔄 Load Different Department"):
                if st.button("Reset and Select New Department"):
                    # Clear session state
                    st.session_state.data_loaded = False
                    st.session_state.current_department = None
                    st.session_state.current_data = None
                    st.session_state.load_time = None
                    st.rerun()
            
            st.divider()
            
            # Render main interface with all sections
            self.render_main_interface()

def main():
    """Main entry point for the application."""
    try:
        app = PoliceAnalyticsApp()
        app.run()
    except Exception as e:
        st.error(f"Application error: {e}")
        logger.error(f"Application error: {e}", exc_info=True)

if __name__ == "__main__":
    main() 