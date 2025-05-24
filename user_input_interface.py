#!/usr/bin/env python3
"""
User Input Interface for Police Data Collection
Asks specific questions to gather user requirements for data from:
1. Stanford Open Policing Project: https://openpolicing.stanford.edu/data/
2. Police Data Initiative: https://www.policedatainitiative.org/datasets/
"""

import streamlit as st
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup
import re

class UserDataRequirements:
    def __init__(self):
        self.stanford_url = "https://openpolicing.stanford.edu/data/"
        self.pdi_url = "https://www.policedatainitiative.org/datasets/"
        
        # Known available locations from Stanford (from the actual data table)
        self.stanford_locations = {
            "Seattle, WA": {
                "stops": 319959,
                "time_range": "2006-01-01 to 2015-12-31",
                "url": "https://stacks.stanford.edu/file/druid:yg821jf8611/yg821jf8611_wa_seattle_2020_04_01.csv.zip"
            },
            "Chicago, IL": {
                "stops": "Available",
                "time_range": "TBD",
                "url": "https://stacks.stanford.edu/file/druid:yg821jf8611/yg821jf8611_il_chicago_2020_04_01.csv.zip"
            },
            "New York, NY": {
                "stops": "Available", 
                "time_range": "TBD",
                "url": "https://stacks.stanford.edu/file/druid:rk9745n3214/rk9745n3214_ny_new_york_2020_04_01.csv.zip"
            },
            "Los Angeles, CA": {
                "stops": "Available",
                "time_range": "TBD", 
                "url": "https://stacks.stanford.edu/file/druid:yg821jf8611/yg821jf8611_ca_los_angeles_2020_04_01.csv.zip"
            }
        }

def render_data_source_selection():
    """Ask user which data source they prefer."""
    st.markdown("## 📊 Data Source Selection")
    st.markdown("Please specify which official police data source you'd like to use:")
    
    source_choice = st.radio(
        "**Which data source would you prefer?**",
        [
            "Stanford Open Policing Project (traffic stops, searches, outcomes)",
            "Police Data Initiative (arrests, crimes, use of force)", 
            "Both sources (I'll search all available data)"
        ],
        help="Stanford focuses on traffic stops while PDI has broader police activities"
    )
    
    source_mapping = {
        "Stanford Open Policing Project (traffic stops, searches, outcomes)": "stanford",
        "Police Data Initiative (arrests, crimes, use of force)": "pdi",
        "Both sources (I'll search all available data)": "both"
    }
    
    return source_mapping[source_choice]

def render_location_selection():
    """Ask user for specific location requirements."""
    st.markdown("## 📍 Location Requirements")
    
    location_type = st.radio(
        "**How would you like to specify the location?**",
        [
            "Select from available cities",
            "Enter specific department name",
            "Search by state/region"
        ]
    )
    
    if location_type == "Select from available cities":
        st.markdown("**Available cities with confirmed data:**")
        
        # Show Stanford locations
        st.markdown("### Stanford Open Policing Project:")
        for city, info in UserDataRequirements().stanford_locations.items():
            stops_text = f"{info['stops']:,}" if isinstance(info['stops'], int) else info['stops']
            st.write(f"• **{city}**: {stops_text} records ({info['time_range']})")
        
        selected_city = st.selectbox(
            "Choose a city:",
            list(UserDataRequirements().stanford_locations.keys())
        )
        
        return {"type": "city", "value": selected_city}
    
    elif location_type == "Enter specific department name":
        department_name = st.text_input(
            "**Enter the exact police department name:**",
            placeholder="e.g., Seattle Police Department, NYPD, Chicago Police Department",
            help="Be as specific as possible for better search results"
        )
        
        return {"type": "department", "value": department_name}
    
    else:  # Search by state/region
        state_region = st.selectbox(
            "**Select state or region:**",
            [
                "California", "New York", "Illinois", "Washington", "Texas", 
                "Florida", "Pennsylvania", "Ohio", "Georgia", "North Carolina",
                "Michigan", "New Jersey", "Virginia", "Arizona", "Tennessee",
                "Other (specify below)"
            ]
        )
        
        if state_region == "Other (specify below)":
            state_region = st.text_input("Specify state/region:")
        
        return {"type": "state", "value": state_region}

def render_data_type_selection():
    """Ask user what type of police data they need."""
    st.markdown("## 📋 Data Type Requirements")
    
    data_types = st.multiselect(
        "**What type of police data do you need?** (Select all that apply)",
        [
            "Traffic stops and vehicle searches",
            "Arrests and criminal incidents", 
            "Use of force incidents",
            "Crime statistics and reports",
            "Officer misconduct records",
            "Community policing activities",
            "Any available police data"
        ],
        help="Different sources specialize in different types of data"
    )
    
    if not data_types:
        st.warning("Please select at least one data type.")
        return []
    
    return data_types

def render_time_period_selection():
    """Ask user about time period requirements."""
    st.markdown("## 📅 Time Period Requirements")
    
    time_preference = st.radio(
        "**What time period are you interested in?**",
        [
            "Most recent data available",
            "Specific year range",
            "All available historical data",
            "No preference"
        ]
    )
    
    time_details = {}
    time_details["preference"] = time_preference
    
    if time_preference == "Specific year range":
        col1, col2 = st.columns(2)
        with col1:
            start_year = st.number_input("Start year:", min_value=2000, max_value=2024, value=2020)
        with col2:
            end_year = st.number_input("End year:", min_value=2000, max_value=2024, value=2024)
        
        time_details["start_year"] = start_year
        time_details["end_year"] = end_year
    
    return time_details

def render_data_size_selection():
    """Ask user about data size requirements."""
    st.markdown("## 📊 Data Volume Requirements")
    
    size_preference = st.radio(
        "**How much data do you need?**",
        [
            "Sample data (1,000-5,000 records) - for quick analysis and testing",
            "Medium dataset (10,000-50,000 records) - for standard analysis",
            "Large dataset (100,000+ records) - for comprehensive research",
            "All available data - regardless of size"
        ]
    )
    
    size_mapping = {
        "Sample data (1,000-5,000 records) - for quick analysis and testing": {"type": "sample", "max_records": 5000},
        "Medium dataset (10,000-50,000 records) - for standard analysis": {"type": "medium", "max_records": 50000},
        "Large dataset (100,000+ records) - for comprehensive research": {"type": "large", "max_records": None},
        "All available data - regardless of size": {"type": "all", "max_records": None}
    }
    
    return size_mapping[size_preference]

def render_analysis_purpose_selection():
    """Ask user about their analysis purpose."""
    st.markdown("## 🎯 Analysis Purpose")
    
    purposes = st.multiselect(
        "**What is the purpose of your analysis?** (Select all that apply)",
        [
            "Academic research",
            "Journalism and reporting",
            "Policy analysis and reform",
            "Legal case preparation",
            "Community advocacy",
            "Personal education",
            "Data science project",
            "Other"
        ]
    )
    
    if "Other" in purposes:
        other_purpose = st.text_input("Please specify:")
        purposes.append(f"Other: {other_purpose}")
    
    return purposes

def render_specific_metrics_selection():
    """Ask user about specific metrics they're interested in."""
    st.markdown("## 📈 Specific Metrics of Interest")
    
    metrics = st.multiselect(
        "**Which specific metrics are you most interested in?** (Select all that apply)",
        [
            "Search rates by demographic groups",
            "Hit rates (contraband found in searches)",
            "Use of force frequency and patterns",
            "Arrest rates and outcomes",
            "Traffic stop frequency by location/time",
            "Demographic disparities in policing",
            "Citation vs warning patterns",
            "Officer behavior patterns",
            "Geographic distribution of incidents",
            "Temporal trends and patterns",
            "All available metrics"
        ]
    )
    
    return metrics

def render_output_format_selection():
    """Ask user about preferred output format."""
    st.markdown("## 💾 Output Format Preferences")
    
    col1, col2 = st.columns(2)
    
    with col1:
        file_format = st.selectbox(
            "**Preferred file format:**",
            ["CSV", "Excel", "JSON", "Parquet", "SQLite Database"]
        )
    
    with col2:
        visualization = st.selectbox(
            "**Visualization preference:**",
            ["Interactive dashboard", "Static reports", "Raw data only", "Both dashboard and raw data"]
        )
    
    return {"file_format": file_format, "visualization": visualization}

def collect_user_requirements():
    """Main function to collect all user requirements."""
    st.title("🚔 Police Data Requirements Collection")
    st.markdown("""
    **Please answer the following questions to help us find the exact police data you need from official sources:**
    
    📊 **Stanford Open Policing Project**: https://openpolicing.stanford.edu/data/
    🏛️ **Police Data Initiative**: https://www.policedatainitiative.org/datasets/
    """)
    
    # Collect all requirements
    requirements = {}
    
    # Data source
    requirements["data_source"] = render_data_source_selection()
    
    st.divider()
    
    # Location
    requirements["location"] = render_location_selection()
    
    st.divider()
    
    # Data type
    requirements["data_types"] = render_data_type_selection()
    
    st.divider()
    
    # Time period
    requirements["time_period"] = render_time_period_selection()
    
    st.divider()
    
    # Data size
    requirements["data_size"] = render_data_size_selection()
    
    st.divider()
    
    # Analysis purpose
    requirements["analysis_purpose"] = render_analysis_purpose_selection()
    
    st.divider()
    
    # Specific metrics
    requirements["metrics"] = render_specific_metrics_selection()
    
    st.divider()
    
    # Output format
    requirements["output"] = render_output_format_selection()
    
    # Summary and confirmation
    st.divider()
    st.markdown("## 📋 Requirements Summary")
    
    if st.button("🔍 **Search for Data Based on Requirements**", type="primary"):
        st.markdown("### Your Requirements:")
        st.json(requirements)
        
        st.success("✅ Requirements collected! Searching for matching datasets...")
        
        return requirements
    
    return None

if __name__ == "__main__":
    requirements = collect_user_requirements() 