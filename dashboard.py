import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PoliceDashboard:
    def __init__(self):
        """Initialize the Police Dashboard with configuration."""
        self.config = {
            'chart_height': 400,
            'map_height': 500,
            'color_scheme': 'viridis'
        }
        self.color_palette = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e', 
            'success': '#2ca02c',
            'warning': '#d62728',
            'info': '#9467bd'
        }
    
    def _get_empty_metrics(self) -> Dict:
        """Return empty metrics structure when data is unavailable."""
        return {
            'total_stops': 0,
            'arrests': 0,
            'arrest_rate': "0%",
            'citations': 0,
            'citation_rate': "0%",
            'warnings': 0,
            'warning_rate': "0%",
            'date_range': "Unknown",
            'avg_age': "Unknown",
            'unique_locations': 0,
            'gender_distribution': {},
            'race_distribution': {}
        }
    
    def generate_kpi_metrics(self, df: pd.DataFrame) -> Dict:
        """Generate key performance indicators from the data."""
        try:
            if df is None or len(df) == 0:
                return self._get_empty_metrics()
            
            metrics = {}
            
            # Basic counts
            metrics['total_stops'] = len(df)
            
            # Get unique locations
            location_cols = ['location', 'address', 'street']
            unique_locations = 0
            for col in location_cols:
                if col in df.columns:
                    unique_locations = df[col].nunique()
                    break
            metrics['unique_locations'] = unique_locations
            
            # Calculate arrest rate - handle different schemas
            arrests = 0
            if 'arrest_made' in df.columns:
                try:
                    if df['arrest_made'].dtype in ['int64', 'float64', 'bool']:
                        arrests = int(df['arrest_made'].sum())
                    else:
                        arrests = len(df[df['arrest_made'] == 1])
                except:
                    arrests = 0
            elif 'stop_outcome' in df.columns:
                try:
                    arrest_mask = df['stop_outcome'].str.contains('arrest', case=False, na=False)
                    arrests = int(arrest_mask.sum())
                except:
                    arrests = 0
            
            metrics['arrests'] = arrests
            metrics['arrest_rate'] = f"{(arrests / len(df) * 100):.1f}%" if len(df) > 0 else "0%"
            
            # Calculate citation rate - handle different schemas
            citations = 0
            if 'citation_issued' in df.columns:
                try:
                    if df['citation_issued'].dtype in ['int64', 'float64', 'bool']:
                        citations = int(df['citation_issued'].sum())
                    else:
                        citations = len(df[df['citation_issued'] == 1])
                except:
                    citations = 0
            elif 'stop_outcome' in df.columns:
                try:
                    citation_mask = df['stop_outcome'].str.contains('citation', case=False, na=False)
                    citations = int(citation_mask.sum())
                except:
                    citations = 0
            
            if citations > 0:
                metrics['citations'] = citations
                metrics['citation_rate'] = f"{(citations / len(df) * 100):.1f}%"
            else:
                metrics['citations'] = "N/A"
                metrics['citation_rate'] = "N/A"
            
            # Calculate warning rate - handle different schemas
            warnings = 0
            if 'warning_issued' in df.columns:
                try:
                    if df['warning_issued'].dtype in ['int64', 'float64', 'bool']:
                        warnings = int(df['warning_issued'].sum())
                    else:
                        warnings = len(df[df['warning_issued'] == 1])
                except:
                    warnings = 0
            elif 'stop_outcome' in df.columns:
                try:
                    warning_mask = df['stop_outcome'].str.contains('warning', case=False, na=False)
                    warnings = int(warning_mask.sum())
                except:
                    warnings = 0
            
            if warnings > 0:
                metrics['warnings'] = warnings
                metrics['warning_rate'] = f"{(warnings / len(df) * 100):.1f}%"
            else:
                metrics['warnings'] = "N/A"
                metrics['warning_rate'] = "N/A"
            
            # Date range calculation - improved
            date_range = "Unknown"
            if 'date' in df.columns:
                try:
                    # Try multiple date parsing approaches
                    df_temp = df.copy()
                    
                    # Convert categorical to string first if needed
                    if df_temp['date'].dtype.name == 'category':
                        df_temp['date'] = df_temp['date'].astype(str)
                    
                    # First try: assume standard format
                    df_temp['parsed_date'] = pd.to_datetime(df_temp['date'], errors='coerce')
                    valid_dates = df_temp['parsed_date'].dropna()
                    
                    if len(valid_dates) > 0:
                        start_date = valid_dates.min().strftime('%Y-%m-%d')
                        end_date = valid_dates.max().strftime('%Y-%m-%d')
                        date_range = f"{start_date} to {end_date}"
                        logger.info(f"Calculated date range: {date_range}")
                    else:
                        # Try alternative formats
                        for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d']:
                            try:
                                df_temp['parsed_date'] = pd.to_datetime(df_temp['date'], format=fmt, errors='coerce')
                                valid_dates = df_temp['parsed_date'].dropna()
                                if len(valid_dates) > 0:
                                    start_date = valid_dates.min().strftime('%Y-%m-%d')
                                    end_date = valid_dates.max().strftime('%Y-%m-%d')
                                    date_range = f"{start_date} to {end_date}"
                                    logger.info(f"Calculated date range with format {fmt}: {date_range}")
                                    break
                            except:
                                continue
                except Exception as e:
                    logger.warning(f"Error calculating date range: {e}")
                    date_range = "Date parsing failed"
            
            # Age calculation
            avg_age = "N/A"
            if 'driver_age' in df.columns:
                try:
                    # Clean age data
                    ages = pd.to_numeric(df['driver_age'], errors='coerce')
                    valid_ages = ages[(ages > 0) & (ages < 120)].dropna()
                    
                    if len(valid_ages) > 0:
                        avg_age = f"{valid_ages.mean():.1f}"
                except:
                    avg_age = "N/A"
            
            # Set all metrics
            metrics['date_range'] = date_range
            metrics['avg_age'] = avg_age
            
            # Gender distribution
            if 'driver_gender' in df.columns:
                gender_dist = df['driver_gender'].value_counts()
                metrics['gender_distribution'] = gender_dist.to_dict()
            else:
                metrics['gender_distribution'] = {}
            
            # Race distribution
            if 'driver_race' in df.columns:
                race_dist = df['driver_race'].value_counts()
                metrics['race_distribution'] = race_dist.to_dict()
            else:
                metrics['race_distribution'] = {}
            
            logger.info(f"Generated metrics: {len(metrics)} items including date range: {metrics['date_range']}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error generating metrics: {e}")
            return self._get_empty_metrics()
    
    def display_kpi_cards(self, metrics: Dict):
        """Display KPI metrics in card format."""
        if not metrics:
            st.error("Unable to calculate metrics")
            return
        
        # Create columns for KPI cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Stops",
                value=f"{metrics['total_stops']:,}",
                help="Total number of police stops in the dataset"
            )
        
        with col2:
            st.metric(
                label="Arrest Rate",
                value=f"{metrics['arrest_rate']}",
                help="Percentage of stops that resulted in arrest"
            )
        
        with col3:
            # Check if citation data exists
            if 'citation_rate' in metrics and metrics['citation_rate'] != "N/A":
                st.metric(
                    label="Citation Rate", 
                    value=f"{metrics['citation_rate']}",
                    help="Percentage of stops that resulted in a citation"
                )
            else:
                st.metric(
                    label="Citation Rate", 
                    value="Not Available",
                    help="Citation data not available in this dataset"
                )
        
        with col4:
            # Check if warning data exists
            if 'warning_rate' in metrics and metrics['warning_rate'] != "N/A":
                st.metric(
                    label="Warning Rate",
                    value=f"{metrics['warning_rate']}",
                    help="Percentage of stops that resulted in a warning"
                )
            else:
                st.metric(
                    label="Warning Rate",
                    value="Not Available",
                    help="Warning data not available in this dataset"
                )
        
        # Additional metrics row
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            # Check if warning data exists and is numeric
            if 'warnings' in metrics and isinstance(metrics['warnings'], (int, float)) and metrics['warnings'] > 0:
                st.metric(
                    label="Warnings",
                    value=f"{metrics['warnings']:,}",
                    help="Number of warnings issued"
                )
            else:
                st.metric(
                    label="Warnings",
                    value=metrics.get('warnings', '0'),
                    help="Warning data not available or no warnings issued"
                )
        
        with col6:
            # Check if citation data exists and is numeric
            citation_value = metrics.get('citations', 0)
            if isinstance(citation_value, (int, float)):
                st.metric(
                    label="Citations",
                    value=f"{citation_value:,}",
                    help="Number of citations issued"
                )
            else:
                st.metric(
                    label="Citations",
                    value=str(citation_value),
                    help="Citation data not available"
                )
        
        with col7:
            st.metric(
                label="Data Range",
                value=metrics['date_range'],
                help="Date range of the dataset"
            )
        
        with col8:
            # Show what data IS available
            available_features = []
            if 'arrests' in metrics and isinstance(metrics.get('arrests'), (int, float)) and metrics['arrests'] > 0:
                available_features.append("Arrests")
            if 'citations' in metrics and isinstance(metrics.get('citations'), (int, float)) and metrics['citations'] > 0:
                available_features.append("Citations")
            if 'warnings' in metrics and isinstance(metrics.get('warnings'), (int, float)) and metrics['warnings'] > 0:
                available_features.append("Warnings")
            
            st.metric(
                label="Available Data",
                value=f"{len(available_features)} features",
                help=f"Available: {', '.join(available_features) if available_features else 'Basic stop data only'}"
            )
        
        # Third row of additional metrics
        col9, col10, col11, col12 = st.columns(4)
        
        with col9:
            st.metric(
                label="Average Age",
                value=metrics['avg_age'],
                help="Average age of stopped individuals"
            )
        
        with col10:
            st.metric(
                label="Locations",
                value=f"{metrics['unique_locations']:,}",
                help="Number of unique stop locations"
            )
    
    def create_search_rate_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create search rate by race chart."""
        try:
            if 'driver_race' not in df.columns:
                fig = go.Figure()
                fig.add_annotation(text="Race data not available", x=0.5, y=0.5)
                return fig
            
            if 'search_conducted' in df.columns:
                search_by_race = df.groupby('driver_race').agg({
                    'search_conducted': ['count', 'sum']
                }).round(2)
                
                search_by_race.columns = ['total_stops', 'searches_conducted']
                search_by_race['search_rate'] = (search_by_race['searches_conducted'] / search_by_race['total_stops'] * 100).round(2)
                search_by_race = search_by_race.reset_index()
                
                fig = px.bar(
                    search_by_race,
                    x='driver_race',
                    y='search_rate',
                    title='Search Rate by Race',
                    labels={'search_rate': 'Search Rate (%)', 'driver_race': 'Race'},
                    color='search_rate',
                    color_continuous_scale='Viridis'
                )
            else:
                # Fallback to arrest rate
                arrest_by_race = df.groupby('driver_race').size().reset_index(name='stops')
                
                fig = px.bar(
                    arrest_by_race,
                    x='driver_race',
                    y='stops',
                    title='Stops by Race',
                    labels={'stops': 'Number of Stops', 'driver_race': 'Race'}
                )
            
            fig.update_layout(showlegend=False)
            return fig
            
        except Exception as e:
            logger.error(f"Error creating search rate chart: {e}")
            fig = go.Figure()
            fig.add_annotation(text="Chart unavailable", x=0.5, y=0.5)
            return fig
    
    def create_temporal_analysis(self, df: pd.DataFrame) -> go.Figure:
        """Create temporal analysis of stops over time."""
        try:
            if 'date' not in df.columns:
                fig = go.Figure()
                fig.add_annotation(text="Date data not available", x=0.5, y=0.5)
                return fig
            
            # Parse dates
            df['parsed_date'] = pd.to_datetime(df['date'], errors='coerce')
            valid_dates = df.dropna(subset=['parsed_date'])
            
            if len(valid_dates) == 0:
                fig = go.Figure()
                fig.add_annotation(text="No valid dates found", x=0.5, y=0.5)
                return fig
            
            # Group by month
            valid_dates['year_month'] = valid_dates['parsed_date'].dt.to_period('M')
            monthly_stops = valid_dates.groupby('year_month').size().reset_index(name='stops')
            monthly_stops['year_month'] = monthly_stops['year_month'].astype(str)
            
            fig = px.line(
                monthly_stops,
                x='year_month',
                y='stops',
                title='Police Stops Over Time',
                labels={'stops': 'Number of Stops', 'year_month': 'Month'}
            )
            
            fig.update_layout(xaxis_tickangle=-45)
            return fig
            
        except Exception as e:
            logger.error(f"Error creating temporal analysis: {e}")
            fig = go.Figure()
            fig.add_annotation(text="Temporal analysis unavailable", x=0.5, y=0.5)
            return fig
    
    def create_outcome_distribution(self, df: pd.DataFrame) -> go.Figure:
        """Create stop outcome distribution pie chart."""
        try:
            # Check multiple possible outcome columns
            outcome_columns = ['stop_outcome', 'stop_result', 'outcome', 'result']
            outcome_col = None
            
            for col in outcome_columns:
                if col in df.columns:
                    outcome_col = col
                    break
            
            if outcome_col is None:
                # Create synthetic outcomes based on available data
                synthetic_outcomes = []
                if 'arrest_made' in df.columns:
                    arrests = df['arrest_made'].sum() if df['arrest_made'].dtype in ['int64', 'float64', 'bool'] else len(df[df['arrest_made'] == 1])
                    if arrests > 0:
                        synthetic_outcomes.append(('Arrest', arrests))
                
                if 'citation_issued' in df.columns:
                    citations = df['citation_issued'].sum() if df['citation_issued'].dtype in ['int64', 'float64', 'bool'] else len(df[df['citation_issued'] == 1])
                    if citations > 0:
                        synthetic_outcomes.append(('Citation', citations))
                
                if 'warning_issued' in df.columns:
                    warnings = df['warning_issued'].sum() if df['warning_issued'].dtype in ['int64', 'float64', 'bool'] else len(df[df['warning_issued'] == 1])
                    if warnings > 0:
                        synthetic_outcomes.append(('Warning', warnings))
                
                # Calculate "Other" category
                total_with_outcomes = sum([count for _, count in synthetic_outcomes])
                other_count = len(df) - total_with_outcomes
                if other_count > 0:
                    synthetic_outcomes.append(('Other/No Action', other_count))
                
                if synthetic_outcomes:
                    fig = px.pie(
                        values=[count for _, count in synthetic_outcomes],
                        names=[name for name, _ in synthetic_outcomes],
                        title='Distribution of Stop Outcomes (Reconstructed)'
                    )
                    return fig
                else:
                    fig = go.Figure()
                    fig.add_annotation(text="Outcome data not available", x=0.5, y=0.5)
                    return fig
            
            # Use existing outcome column
            outcome_counts = df[outcome_col].value_counts().head(10)
            
            # Special handling for single outcome (like Philadelphia PD with only "arrest")
            if len(outcome_counts) == 1:
                # Show a bar chart instead of pie chart for single outcomes
                fig = go.Figure(data=[
                    go.Bar(
                        x=[outcome_counts.index[0]],
                        y=[outcome_counts.values[0]],
                        text=[f"{outcome_counts.values[0]:,}"],
                        textposition='auto',
                    )
                ])
                fig.update_layout(
                    title=f'Stop Outcomes: {outcome_counts.index[0].title()} Only',
                    xaxis_title='Outcome Type',
                    yaxis_title='Number of Stops',
                    showlegend=False
                )
                return fig
            
            # Multiple outcomes - use pie chart
            fig = px.pie(
                values=outcome_counts.values,
                names=outcome_counts.index,
                title='Distribution of Stop Outcomes'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating outcome distribution: {e}")
            fig = go.Figure()
            fig.add_annotation(text="Outcome chart unavailable", x=0.5, y=0.5)
            return fig
    
    def create_demographic_analysis(self, df: pd.DataFrame) -> go.Figure:
        """Create demographic analysis charts."""
        try:
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Stops by Race', 'Stops by Gender', 'Age Distribution', 'Stops by District'),
                specs=[[{'type': 'bar'}, {'type': 'bar'}],
                       [{'type': 'histogram'}, {'type': 'bar'}]]
            )
            
            # Race distribution - check multiple column names
            race_columns = ['driver_race', 'subject_race', 'race', 'ethnicity']
            race_col = None
            for col in race_columns:
                if col in df.columns and df[col].notna().sum() > 0:
                    race_col = col
                    break
            
            if race_col:
                race_counts = df[race_col].value_counts().head(8)
                if len(race_counts) > 0:
                    fig.add_trace(
                        go.Bar(x=race_counts.index, y=race_counts.values, name='Race', marker_color='#1f77b4'),
                        row=1, col=1
                    )
                else:
                    fig.add_annotation(text="No race data", x=0.5, y=0.5, xref="x1", yref="y1", showarrow=False)
            else:
                fig.add_annotation(text="Race data not available", x=0.5, y=0.5, xref="x1", yref="y1", showarrow=False)
            
            # Gender distribution - check multiple column names
            gender_columns = ['driver_gender', 'subject_gender', 'gender', 'sex']
            gender_col = None
            for col in gender_columns:
                if col in df.columns and df[col].notna().sum() > 0:
                    gender_col = col
                    break
            
            if gender_col:
                gender_counts = df[gender_col].value_counts()
                if len(gender_counts) > 0:
                    fig.add_trace(
                        go.Bar(x=gender_counts.index, y=gender_counts.values, name='Gender', marker_color='#ff7f0e'),
                        row=1, col=2
                    )
                else:
                    fig.add_annotation(text="No gender data", x=0.5, y=0.5, xref="x2", yref="y2", showarrow=False)
            else:
                fig.add_annotation(text="Gender data not available", x=0.5, y=0.5, xref="x2", yref="y2", showarrow=False)
            
            # Age distribution - check multiple column names
            age_columns = ['driver_age', 'subject_age', 'age']
            age_col = None
            for col in age_columns:
                if col in df.columns and df[col].notna().sum() > 0:
                    age_col = col
                    break
            
            if age_col:
                # Clean and convert age data
                ages = pd.to_numeric(df[age_col], errors='coerce')
                valid_ages = ages[(ages > 0) & (ages < 120)].dropna()
                
                if len(valid_ages) > 0:
                    fig.add_trace(
                        go.Histogram(x=valid_ages, name='Age', nbinsx=20, marker_color='#2ca02c'),
                        row=2, col=1
                    )
                else:
                    fig.add_annotation(text="No valid age data", x=0.5, y=0.5, xref="x3", yref="y3", showarrow=False)
            else:
                fig.add_annotation(text="Age data not available", x=0.5, y=0.5, xref="x3", yref="y3", showarrow=False)
            
            # District distribution - check multiple column names
            district_columns = ['district', 'police_district', 'precinct', 'beat', 'sector']
            district_col = None
            for col in district_columns:
                if col in df.columns and df[col].notna().sum() > 0:
                    district_col = col
                    break
            
            if district_col:
                district_counts = df[district_col].value_counts().head(10)
                if len(district_counts) > 0:
                    fig.add_trace(
                        go.Bar(x=district_counts.index, y=district_counts.values, name='District', marker_color='#d62728'),
                        row=2, col=2
                    )
                else:
                    fig.add_annotation(text="No district data", x=0.5, y=0.5, xref="x4", yref="y4", showarrow=False)
            else:
                fig.add_annotation(text="District data not available", x=0.5, y=0.5, xref="x4", yref="y4", showarrow=False)
            
            fig.update_layout(
                height=600,
                showlegend=False,
                title_text="Demographic Analysis"
            )
            
            # Update axis labels
            fig.update_xaxes(title_text="Race", row=1, col=1)
            fig.update_xaxes(title_text="Gender", row=1, col=2)
            fig.update_xaxes(title_text="Age", row=2, col=1)
            fig.update_xaxes(title_text="District", row=2, col=2)
            
            fig.update_yaxes(title_text="Count", row=1, col=1)
            fig.update_yaxes(title_text="Count", row=1, col=2)
            fig.update_yaxes(title_text="Count", row=2, col=1)
            fig.update_yaxes(title_text="Count", row=2, col=2)
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating demographic analysis: {e}")
            fig = go.Figure()
            fig.add_annotation(text=f"Demographic analysis unavailable: {str(e)}", x=0.5, y=0.5)
            return fig
    
    def create_hourly_pattern_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create hourly pattern analysis chart."""
        try:
            if 'time' not in df.columns:
                fig = go.Figure()
                fig.add_annotation(text="Time data not available", x=0.5, y=0.5)
                return fig
            
            # Extract hour from time strings
            df_temp = df.copy()
            df_temp['hour'] = pd.to_numeric(df_temp['time'].str[:2], errors='coerce')
            df_temp = df_temp.dropna(subset=['hour'])
            
            if len(df_temp) == 0:
                fig = go.Figure()
                fig.add_annotation(text="No valid time data found", x=0.5, y=0.5)
                return fig
            
            hourly_counts = df_temp['hour'].value_counts().sort_index()
            
            fig = px.bar(
                x=hourly_counts.index,
                y=hourly_counts.values,
                title='Police Stops by Hour of Day',
                labels={'x': 'Hour of Day', 'y': 'Number of Stops'}
            )
            
            # Add peak hour annotation
            peak_hour = hourly_counts.idxmax()
            peak_count = hourly_counts.max()
            fig.add_annotation(
                x=peak_hour,
                y=peak_count,
                text=f"Peak: {peak_hour}:00<br>{peak_count:,} stops",
                showarrow=True,
                arrowhead=2
            )
            
            fig.update_layout(showlegend=False)
            return fig
            
        except Exception as e:
            logger.error(f"Error creating hourly pattern chart: {e}")
            fig = go.Figure()
            fig.add_annotation(text="Hourly pattern chart unavailable", x=0.5, y=0.5)
            return fig

    def create_geographic_heatmap(self, df: pd.DataFrame) -> go.Figure:
        """Create geographic heatmap if coordinates are available."""
        try:
            if not all(col in df.columns for col in ['lat', 'longitude']):
                fig = go.Figure()
                fig.add_annotation(text="Geographic coordinates not available", x=0.5, y=0.5)
                return fig
            
            # Filter valid coordinates
            coords_df = df[['lat', 'longitude']].copy()
            coords_df = coords_df.dropna()
            coords_df = coords_df[(coords_df['lat'] != 0) & (coords_df['longitude'] != 0)]
            
            if len(coords_df) == 0:
                fig = go.Figure()
                fig.add_annotation(text="No valid coordinates found", x=0.5, y=0.5)
                return fig
            
            # Sample data for performance (max 1000 points)
            if len(coords_df) > 1000:
                coords_df = coords_df.sample(1000)
            
            fig = px.scatter_mapbox(
                coords_df,
                lat='lat',
                lon='longitude',
                title=f'Police Stop Locations ({len(coords_df):,} stops shown)',
                zoom=10,
                height=500
            )
            
            fig.update_layout(
                mapbox_style="open-street-map",
                margin={"r":0,"t":50,"l":0,"b":0}
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating geographic heatmap: {e}")
            fig = go.Figure()
            fig.add_annotation(text="Geographic visualization unavailable", x=0.5, y=0.5)
            return fig

    def render_dashboard(self, df: pd.DataFrame, department: str):
        """Render the complete dashboard."""
        st.title(f"Police Analytics Dashboard - {department}")
        
        # Calculate and display KPIs
        metrics = self.generate_kpi_metrics(df)
        self.display_kpi_cards(metrics)
        
        st.divider()
        
        # Create tabs for different visualizations
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Analysis", "Temporal", "Demographics", "Geography"])
        
        with tab1:
            st.subheader("📊 Executive Summary")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Dataset Overview:**")
                st.write(f"• Total records: {len(df):,}")
                st.write(f"• Date range: {metrics['date_range']}")
                st.write(f"• Districts: {df['district'].nunique() if 'district' in df.columns else 0}")
                
                # Calculate peak hour on demand
                peak_hour = "Unknown"
                if 'time' in df.columns:
                    try:
                        df_temp = df.copy()
                        df_temp['hour'] = pd.to_numeric(df_temp['time'].str[:2], errors='coerce')
                        df_temp = df_temp.dropna(subset=['hour'])
                        if len(df_temp) > 0:
                            hour_counts = df_temp['hour'].value_counts()
                            if len(hour_counts) > 0:
                                peak_hour = f"{int(hour_counts.index[0]):02d}:00"
                    except:
                        peak_hour = "Unknown"
                
                st.write(f"• Peak hour: {peak_hour}")
                if 'driver_race' in df.columns:
                    races = df['driver_race'].nunique()
                    st.write(f"• Race categories: {races}")
            
            with col2:
                outcome_chart = self.create_outcome_distribution(df)
                st.plotly_chart(outcome_chart, use_container_width=True, key="overview_outcome")
        
        with tab2:
            st.subheader("🔍 Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                search_chart = self.create_search_rate_chart(df)
                st.plotly_chart(search_chart, use_container_width=True, key="analysis_search")
            
            with col2:
                hourly_chart = self.create_hourly_pattern_chart(df)
                st.plotly_chart(hourly_chart, use_container_width=True, key="analysis_hourly")
        
        with tab3:
            st.subheader("📈 Temporal Analysis")
            temporal_chart = self.create_temporal_analysis(df)
            st.plotly_chart(temporal_chart, use_container_width=True, key="temporal_main")
        
        with tab4:
            st.subheader("👥 Demographics")
            demo_chart = self.create_demographic_analysis(df)
            st.plotly_chart(demo_chart, use_container_width=True, key="demographics_main")
        
        with tab5:
            st.subheader("🗺️ Geographic Distribution")
            geo_chart = self.create_geographic_heatmap(df)
            st.plotly_chart(geo_chart, use_container_width=True, key="geography_main")
    
    def create_filtered_view(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create simple filters for the dashboard."""
        st.sidebar.header("🔧 Filters")
        
        original_count = len(df)
        
        # Simple demographics filters
        if 'driver_race' in df.columns:
            races = ['All'] + list(df['driver_race'].dropna().unique())
            selected_race = st.sidebar.selectbox("Race:", races)
            if selected_race != 'All':
                df = df[df['driver_race'] == selected_race]
        
        if 'driver_gender' in df.columns:
            genders = ['All'] + list(df['driver_gender'].dropna().unique())
            selected_gender = st.sidebar.selectbox("Gender:", genders)
            if selected_gender != 'All':
                df = df[df['driver_gender'] == selected_gender]
        
        if 'district' in df.columns:
            districts = ['All'] + list(df['district'].dropna().unique())
            selected_district = st.sidebar.selectbox("District:", districts)
            if selected_district != 'All':
                df = df[df['district'] == selected_district]
        
        # Show filter summary
        filtered_count = len(df)
        st.sidebar.metric(
            "Filtered Records",
            f"{filtered_count:,}",
            help=f"Showing {filtered_count:,} out of {original_count:,} total records"
        )
        
        return df 