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
        self.color_palette = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e', 
            'success': '#2ca02c',
            'warning': '#d62728',
            'info': '#9467bd'
        }
    
    def generate_kpi_metrics(self, df: pd.DataFrame) -> Dict:
        """Generate key performance indicators from police data."""
        try:
            total_stops = len(df)
            available_columns = list(df.columns)
            
            # Calculate citation and warning rates (which ARE available)
            citation_rate = 0
            citation_data_available = 'citation_issued' in df.columns
            if citation_data_available:
                citation_rate = (df['citation_issued'].sum() / total_stops * 100) if total_stops > 0 else 0
            
            warning_rate = 0
            warning_data_available = 'warning_issued' in df.columns
            if warning_data_available:
                warning_rate = (df['warning_issued'].sum() / total_stops * 100) if total_stops > 0 else 0
            
            force_rate = 0
            force_data_available = 'use_of_force' in df.columns
            if force_data_available:
                force_rate = (df['use_of_force'].sum() / total_stops * 100) if total_stops > 0 else 0
            
            arrest_rate = 0
            if 'arrest_made' in df.columns:
                arrest_rate = (df['arrest_made'].sum() / total_stops * 100) if total_stops > 0 else 0
            elif 'stop_outcome' in df.columns:
                arrest_count = df['stop_outcome'].str.contains('ARREST', case=False, na=False).sum()
                arrest_rate = (arrest_count / total_stops * 100) if total_stops > 0 else 0
            
            # Date range
            date_range = "Unknown"
            if 'date' in df.columns:
                try:
                    valid_dates = pd.to_datetime(df['date'], errors='coerce').dropna()
                    if len(valid_dates) > 0:
                        date_range = f"{valid_dates.min().strftime('%Y-%m-%d')} to {valid_dates.max().strftime('%Y-%m-%d')}"
                except:
                    pass
            
            # Peak hour analysis - FIXED
            peak_hour = "Unknown"
            if 'time' in df.columns:
                try:
                    # Extract hour from time strings like "02:19:37"
                    df_temp = df.copy()
                    df_temp['hour'] = pd.to_numeric(df_temp['time'].str[:2], errors='coerce')
                    df_temp = df_temp.dropna(subset=['hour'])
                    if len(df_temp) > 0:
                        hour_counts = df_temp['hour'].value_counts()
                        if len(hour_counts) > 0:
                            peak_hour = f"{int(hour_counts.index[0]):02d}:00"
                except Exception as e:
                    logger.error(f"Error calculating peak hour: {e}")
                    pass
            
            # Top district
            top_district = "Unknown"
            if 'district' in df.columns:
                district_counts = df['district'].value_counts()
                if len(district_counts) > 0:
                    top_district = district_counts.index[0]
            
            # Age statistics
            avg_age = "Unknown"
            if 'driver_age' in df.columns:
                valid_ages = pd.to_numeric(df['driver_age'], errors='coerce').dropna()
                if len(valid_ages) > 0:
                    avg_age = f"{valid_ages.mean():.1f} years"
            
            # Geographic coverage
            unique_locations = 0
            if 'location' in df.columns:
                unique_locations = df['location'].nunique()
            elif all(col in df.columns for col in ['lat', 'longitude']):
                # Count unique coordinate pairs
                coords = df[['lat', 'longitude']].dropna()
                unique_locations = len(coords.drop_duplicates())
            
            return {
                'total_stops': total_stops,
                'citation_rate': round(citation_rate, 2),
                'warning_rate': round(warning_rate, 2),
                'force_rate': round(force_rate, 2),
                'arrest_rate': round(arrest_rate, 2),
                'date_range': date_range,
                'unique_districts': df['district'].nunique() if 'district' in df.columns else 0,
                'peak_hour': peak_hour,
                'top_district': top_district,
                'avg_age': avg_age,
                'unique_locations': unique_locations,
                # Availability flags
                'citation_data_available': citation_data_available,
                'warning_data_available': warning_data_available,
                'force_data_available': force_data_available,
                'available_columns': available_columns
            }
            
        except Exception as e:
            logger.error(f"Error calculating KPIs: {e}")
            return {
                'total_stops': len(df) if df is not None else 0,
                'citation_rate': 0,
                'warning_rate': 0,
                'force_rate': 0,
                'arrest_rate': 0,
                'date_range': "Unknown",
                'unique_districts': 0,
                'peak_hour': "Unknown",
                'top_district': "Unknown", 
                'avg_age': "Unknown",
                'unique_locations': 0,
                'citation_data_available': False,
                'warning_data_available': False,
                'force_data_available': False,
                'available_columns': []
            }
    
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
                value=f"{metrics['arrest_rate']}%",
                help="Percentage of stops that resulted in arrest"
            )
        
        with col3:
            # Check if citation data exists
            if 'citation_data_available' in metrics and metrics['citation_data_available']:
                st.metric(
                    label="Citation Rate", 
                    value=f"{metrics['citation_rate']}%",
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
            if 'warning_data_available' in metrics and metrics['warning_data_available']:
                st.metric(
                    label="Warning Rate",
                    value=f"{metrics['warning_rate']}%",
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
            # Check if force data exists
            if 'force_data_available' in metrics and metrics['force_data_available']:
                st.metric(
                    label="Force Rate",
                    value=f"{metrics['force_rate']}%",
                    help="Percentage of stops involving use of force"
                )
            else:
                st.metric(
                    label="Force Rate",
                    value="Not Available",
                    help="Use of force data not available in this dataset"
                )
        
        with col6:
            st.metric(
                label="Districts",
                value=f"{metrics['unique_districts']}",
                help="Number of unique districts in data"
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
            if 'arrest_made' in metrics.get('available_columns', []):
                available_features.append("Arrests")
            if 'citation_issued' in metrics.get('available_columns', []):
                available_features.append("Citations")
            if 'warning_issued' in metrics.get('available_columns', []):
                available_features.append("Warnings")
            if 'use_of_force' in metrics.get('available_columns', []):
                available_features.append("Force")
            
            st.metric(
                label="Available Data",
                value=f"{len(available_features)} features",
                help=f"Available: {', '.join(available_features) if available_features else 'Basic stop data only'}"
            )
        
        # Third row of additional metrics
        col9, col10, col11, col12 = st.columns(4)
        
        with col9:
            st.metric(
                label="Peak Hour",
                value=metrics.get('peak_hour', 'Unknown'),
                help="Hour with the most police stops"
            )
        
        with col10:
            st.metric(
                label="Top District",
                value=str(metrics.get('top_district', 'Unknown'))[:15],
                help="District with the most stops"
            )
        
        with col11:
            st.metric(
                label="Average Age",
                value=metrics.get('avg_age', 'Unknown'),
                help="Average age of stopped individuals"
            )
        
        with col12:
            st.metric(
                label="Locations",
                value=f"{metrics.get('unique_locations', 0):,}",
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
            if 'stop_outcome' not in df.columns:
                fig = go.Figure()
                fig.add_annotation(text="Outcome data not available", x=0.5, y=0.5)
                return fig
            
            outcome_counts = df['stop_outcome'].value_counts().head(10)  # Top 10 outcomes
            
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
            
            # Race distribution
            if 'driver_race' in df.columns:
                race_counts = df['driver_race'].value_counts().head(8)
                fig.add_trace(
                    go.Bar(x=race_counts.index, y=race_counts.values, name='Race'),
                    row=1, col=1
                )
            
            # Gender distribution  
            if 'driver_gender' in df.columns:
                gender_counts = df['driver_gender'].value_counts()
                fig.add_trace(
                    go.Bar(x=gender_counts.index, y=gender_counts.values, name='Gender'),
                    row=1, col=2
                )
            
            # Age distribution
            if 'driver_age' in df.columns:
                valid_ages = df['driver_age'].dropna()
                if len(valid_ages) > 0:
                    fig.add_trace(
                        go.Histogram(x=valid_ages, name='Age', nbinsx=20),
                        row=2, col=1
                    )
            
            # District distribution
            if 'district' in df.columns:
                district_counts = df['district'].value_counts().head(10)
                fig.add_trace(
                    go.Bar(x=district_counts.index, y=district_counts.values, name='District'),
                    row=2, col=2
                )
            
            fig.update_layout(
                height=600,
                showlegend=False,
                title_text="Demographic Analysis"
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating demographic analysis: {e}")
            fig = go.Figure()
            fig.add_annotation(text="Demographic analysis unavailable", x=0.5, y=0.5)
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
                st.write(f"• Districts: {metrics['unique_districts']}")
                st.write(f"• Peak hour: {metrics['peak_hour']}")
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