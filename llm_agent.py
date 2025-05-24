import time
import json
import sqlite3
import re
from typing import Dict, Optional, Tuple, Any
import logging
from groq import Groq
import pandas as pd
from config import GROQ_API_KEY, GROQ_MODEL, MAX_LLM_RESPONSE_TIME
from database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PoliceDataLLMAgent:
    def __init__(self, api_key: Optional[str] = None):
        # Use provided API key or fall back to config
        self.api_key = api_key or GROQ_API_KEY
        
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
            self.llm_available = True
        else:
            self.client = None
            self.llm_available = False
            logger.warning("No Groq API key provided. LLM features will be disabled.")
        
        self.db_manager = DatabaseManager()
    
    def get_table_info(self, department: str) -> Dict:
        """Get actual table schema and sample data for a department."""
        try:
            # Get table name
            table_name = self.db_manager._get_table_name(department)
            logger.info(f"Getting table info for department '{department}' -> table '{table_name}'")
            
            # Use direct database connection to avoid replacement issues
            conn = sqlite3.connect('police_data.db')
            logger.info(f"SQLite connection established")
            
            # Get sample data directly
            query = f"SELECT * FROM {table_name} LIMIT 5"
            logger.info(f"Executing query: {query}")
            sample_df = pd.read_sql_query(query, conn)
            logger.info(f"Sample data retrieved: {len(sample_df)} rows, {len(sample_df.columns)} columns")
            
            if sample_df is None or sample_df.empty:
                logger.error("Sample data is empty or None")
                conn.close()
                return None
                
            # Get column info
            columns = list(sample_df.columns)
            logger.info(f"Columns: {columns[:10]}...")  # Show first 10 columns
            
            # Get distinct values for categorical columns
            categorical_info = {}
            
            # Check race column
            race_col = None
            for col in ['driver_race', 'subject_race', 'race']:
                if col in columns:
                    race_col = col
                    break
            
            if race_col:
                race_query = f"SELECT DISTINCT {race_col} FROM {table_name} WHERE {race_col} IS NOT NULL LIMIT 10"
                logger.info(f"Getting race values: {race_query}")
                race_values_df = pd.read_sql_query(race_query, conn)
                categorical_info['race_values'] = race_values_df[race_col].tolist()
                logger.info(f"Race values: {categorical_info['race_values']}")
            
            # Check stop outcome column
            outcome_col = None
            for col in ['stop_outcome', 'disposition', 'outcome']:
                if col in columns:
                    outcome_col = col
                    break
                    
            if outcome_col:
                outcome_query = f"SELECT DISTINCT {outcome_col} FROM {table_name} WHERE {outcome_col} IS NOT NULL LIMIT 10"
                logger.info(f"Getting outcome values: {outcome_query}")
                outcome_values_df = pd.read_sql_query(outcome_query, conn)
                categorical_info['outcome_values'] = outcome_values_df[outcome_col].tolist()
                logger.info(f"Outcome values: {categorical_info['outcome_values']}")
            
            conn.close()
            logger.info("Table info retrieved successfully")
            
            return {
                'table_name': table_name,
                'columns': columns,
                'sample_data': sample_df.head(3).to_dict('records'),
                'categorical_info': categorical_info,
                'total_rows': len(sample_df)
            }
            
        except Exception as e:
            logger.error(f"Error getting table info for '{department}': {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def _create_dynamic_system_prompt(self, table_info: Dict) -> str:
        """Create a system prompt with real table information."""
        
        columns_list = ", ".join(table_info['columns'])
        
        sample_data_str = ""
        for i, row in enumerate(table_info['sample_data']):
            # Show more detail about each column's actual values
            row_details = []
            for col, val in row.items():
                row_details.append(f"{col}: {repr(val)}")
            sample_data_str += f"Row {i+1}: {', '.join(row_details[:8])}...\n"
        
        categorical_info_str = ""
        for key, values in table_info['categorical_info'].items():
            categorical_info_str += f"- {key}: {values}\n"
        
        return f"""You are a SQLite query generator. Generate ONLY valid SQLite SQL queries.

**DATABASE: SQLite (NOT MySQL/PostgreSQL)**

**TABLE INFO:**
Table: {table_info['table_name']}
Columns: {columns_list}

**SAMPLE DATA (showing actual formats):**
{sample_data_str}

**CATEGORICAL VALUES:**
{categorical_info_str}

**SQLITE SYNTAX RULES:**
1. Use SQLite functions: strftime(), substr(), CAST(), datetime()
2. For hour extraction: CAST(substr(time, 1, 2) AS INTEGER) NOT HOUR()
3. For dates: strftime('%Y-%m', date) NOT DATE_FORMAT()
4. Always end with complete ORDER BY clause
5. Use exact table name: {table_info['table_name']}
6. Use exact column names from above list

**REQUIRED EXAMPLES:**
- Time analysis: "SELECT CAST(substr(time, 1, 2) AS INTEGER) as hour, COUNT(*) as stop_count FROM {table_info['table_name']} WHERE time IS NOT NULL GROUP BY hour ORDER BY stop_count DESC"
- Race analysis: "SELECT driver_race, COUNT(*) as count FROM {table_info['table_name']} WHERE driver_race IS NOT NULL GROUP BY driver_race ORDER BY count DESC"
- Monthly: "SELECT strftime('%Y-%m', date) as month, COUNT(*) as stops FROM {table_info['table_name']} WHERE date IS NOT NULL GROUP BY month ORDER BY month"

**CRITICAL:**
- Return ONLY complete SQLite query
- NO explanations, NO thinking, NO incomplete queries
- Always include complete ORDER BY clause"""

    def generate_sql_query(self, question: str, department: str) -> Tuple[Optional[str], float]:
        """Generate SQL query from natural language question using real schema."""
        start_time = time.time()
        
        try:
            # Get table name directly
            table_name = self.db_manager._get_table_name(department)
            logger.info(f"Generating SQL for department '{department}' using table '{table_name}'")
            
            # Simple direct query generation based on question patterns
            question_lower = question.lower()
            
            # Basic pattern matching for common queries with better logic
            if 'total number of stops' in question_lower or 'how many stops' in question_lower:
                sql_query = f"SELECT COUNT(*) as total_stops FROM {table_name}"
                
            elif 'how many arrests' in question_lower and 'race' not in question_lower:
                sql_query = f"SELECT COUNT(*) as total_arrests FROM {table_name} WHERE arrest_made = 1"
                
            elif 'arrest rate' in question_lower and ('black' in question_lower and 'white' in question_lower):
                # Comparative arrest rate query
                sql_query = f"""
                SELECT driver_race, 
                       COUNT(*) as total_stops,
                       SUM(CASE WHEN arrest_made = 1 THEN 1 ELSE 0 END) as arrests,
                       ROUND(100.0 * SUM(CASE WHEN arrest_made = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as arrest_rate
                FROM {table_name} 
                WHERE driver_race IN ('black', 'white') 
                GROUP BY driver_race 
                ORDER BY arrest_rate DESC
                """
                
            elif 'arrest' in question_lower and 'race' in question_lower:
                sql_query = f"""
                SELECT driver_race, 
                       COUNT(*) as total_stops,
                       SUM(CASE WHEN arrest_made = 1 THEN 1 ELSE 0 END) as arrests,
                       ROUND(100.0 * SUM(CASE WHEN arrest_made = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as arrest_rate
                FROM {table_name} 
                WHERE driver_race IS NOT NULL 
                GROUP BY driver_race 
                ORDER BY arrests DESC
                """
                
            elif 'citation' in question_lower and 'issued' in question_lower:
                sql_query = f"SELECT COUNT(*) as total_citations FROM {table_name} WHERE citation_issued = 1"
                
            elif 'warning' in question_lower and 'issued' in question_lower:
                sql_query = f"SELECT COUNT(*) as total_warnings FROM {table_name} WHERE warning_issued = 1"
                
            elif 'peak hour' in question_lower or 'hour' in question_lower:
                sql_query = f"""
                SELECT CAST(substr(time, 1, 2) AS INTEGER) as hour, 
                       COUNT(*) as stop_count 
                FROM {table_name} 
                WHERE time IS NOT NULL AND length(time) >= 2
                GROUP BY hour 
                ORDER BY stop_count DESC
                """
            
            elif 'month' in question_lower or 'over time' in question_lower:
                sql_query = f"""
                SELECT strftime('%Y-%m', date) as month, 
                       COUNT(*) as stops 
                FROM {table_name} 
                WHERE date IS NOT NULL 
                GROUP BY month 
                ORDER BY month
                """
            
            elif 'district' in question_lower and 'highest' in question_lower:
                sql_query = f"""
                SELECT district, COUNT(*) as stops 
                FROM {table_name} 
                WHERE district IS NOT NULL 
                GROUP BY district 
                ORDER BY stops DESC 
                LIMIT 10
                """
            
            elif 'average age' in question_lower:
                sql_query = f"""
                SELECT ROUND(AVG(CAST(driver_age AS FLOAT)), 1) as average_age 
                FROM {table_name} 
                WHERE driver_age IS NOT NULL AND driver_age > 0 AND driver_age < 120
                """
            
            elif 'race' in question_lower and 'breakdown' not in question_lower:
                sql_query = f"""
                SELECT driver_race, COUNT(*) as stops 
                FROM {table_name} 
                WHERE driver_race IS NOT NULL 
                GROUP BY driver_race 
                ORDER BY stops DESC
                """
                
            else:
                # Check if LLM is available for complex queries
                if not self.llm_available:
                    # Fallback to simple count query when no API key
                    sql_query = f"SELECT COUNT(*) as total_stops FROM {table_name}"
                    logger.info("Using fallback query due to missing API key")
                else:
                    # Try the complex method as fallback
                    table_info = self.get_table_info(department)
                    if not table_info:
                        # Ultimate fallback - simple count query
                        sql_query = f"SELECT COUNT(*) as total_stops FROM {table_name}"
                    else:
                        # Use the original complex method
                        system_prompt = self._create_dynamic_system_prompt(table_info)
                        
                        response = self.client.chat.completions.create(
                            model=GROQ_MODEL,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": f"Generate SQL for: {question}"}
                            ],
                            temperature=0.1,
                            max_tokens=500
                        )
                        
                        sql_query = self._clean_sql_response(response.choices[0].message.content)
            
            generation_time = time.time() - start_time
            logger.info(f"Generated SQL: {sql_query[:100]}...")
            
            return sql_query, generation_time
            
        except Exception as e:
            generation_time = time.time() - start_time
            logger.error(f"Error generating SQL query: {e}")
            # Return a safe fallback query
            table_name = self.db_manager._get_table_name(department)
            return f"SELECT COUNT(*) as total_records FROM {table_name}", generation_time
    
    def _clean_sql_response(self, sql_query: str) -> str:
        """Clean and fix SQL response."""
        # Remove thinking markers
        if '<think>' in sql_query:
            think_start = sql_query.find('<think>')
            think_end = sql_query.find('</think>')
            if think_start != -1 and think_end != -1:
                sql_query = sql_query[:think_start] + sql_query[think_end + 8:]
            elif think_start != -1:
                sql_query = sql_query[:think_start]
        
        # Remove code blocks
        if sql_query.startswith('```sql'):
            sql_query = sql_query[6:]
        elif sql_query.startswith('```'):
            sql_query = sql_query[3:]
        if sql_query.endswith('```'):
            sql_query = sql_query[:-3]
        
        # Fix incomplete ORDER BY
        if sql_query.upper().endswith(' ORDER'):
            sql_query = sql_query + ' BY COUNT(*) DESC'
        elif 'GROUP BY' in sql_query.upper() and 'ORDER BY' not in sql_query.upper():
            if 'COUNT(' in sql_query.upper():
                sql_query = sql_query + ' ORDER BY COUNT(*) DESC'
        
        # Fix MySQL syntax to SQLite
        sql_query = sql_query.replace('HOUR(time)', 'CAST(substr(time, 1, 2) AS INTEGER)')
        
        if sql_query.endswith(';'):
            sql_query = sql_query[:-1]
        
        return sql_query.strip()
    
    def execute_query_and_explain(self, question: str, department: str) -> Dict[str, Any]:
        """Execute query and provide explanation of results."""
        start_time = time.time()
        
        try:
            # Generate SQL query
            sql_query, generation_time = self.generate_sql_query(question, department)
            
            if not sql_query:
                return {
                    'success': False,
                    'error': 'Could not generate SQL query',
                    'latency': time.time() - start_time
                }
            
            # Execute the query
            result_df = self.db_manager.execute_sql_query(sql_query, department)
            
            if result_df is None or result_df.empty:
                return {
                    'success': False,
                    'error': 'Query execution failed or returned no results',
                    'sql_query': sql_query,
                    'latency': time.time() - start_time
                }
            
            # Generate explanation
            explanation = self._generate_explanation(question, result_df, sql_query)
            
            total_latency = time.time() - start_time
            
            return {
                'success': True,
                'sql_query': sql_query,
                'results': result_df,
                'explanation': explanation,
                'latency': total_latency,
                'generation_time': generation_time,
                'within_threshold': total_latency <= MAX_LLM_RESPONSE_TIME
            }
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return {
                'success': False,
                'error': str(e),
                'latency': time.time() - start_time
            }
    
    def _generate_explanation(self, question: str, result_df: pd.DataFrame, sql_query: str) -> str:
        """Generate a natural language explanation of the results."""
        try:
            if len(result_df) == 0:
                return "No data found for your query."
            
            rows_count = len(result_df)
            columns = list(result_df.columns)
            question_lower = question.lower()
            
            # Handle specific race questions for arrests
            if any(race in question_lower for race in ['black', 'blacks']) and 'arrest' in question_lower:
                # Look for any race column
                race_col = None
                for col in ['driver_race', 'subject_race', 'race']:
                    if col in columns:
                        race_col = col
                        break
                
                if race_col:
                    black_data = result_df[result_df[race_col].str.lower() == 'black']
                    if not black_data.empty:
                        # Get count from appropriate column
                        count_col = None
                        for col in ['total_arrests', 'count', 'arrest_count']:
                            if col in columns:
                                count_col = col
                                break
                        
                        if count_col:
                            count = black_data[count_col].iloc[0]
                        else:
                            count = len(black_data)
                        
                        return f"According to the data, **{count:,}** Black individuals were arrested."
                    else:
                        return "No arrest data found for Black individuals in this dataset."
            
            # Handle search rate questions - check if search data exists
            elif 'search rate' in question_lower or 'searched' in question_lower:
                search_cols = [col for col in columns if 'search' in col.lower()]
                if not search_cols:
                    return "⚠️ **Search data not available**: The current dataset doesn't include search-related information. Only stop outcomes like arrests, citations, and warnings are available."
            
            # Generic response for other queries
            if 'total_arrests' in columns:
                total_arrests = result_df['total_arrests'].sum()
                top_group = result_df.iloc[0][columns[0]] if len(columns) > 1 else 'N/A'
                top_count = result_df.iloc[0]['total_arrests']
                return f"Arrest analysis shows {total_arrests:,} total arrests across {rows_count} groups. {top_group} had the highest number of arrests ({top_count:,})."
            
            elif any('count' in col.lower() for col in columns):
                count_col = [col for col in columns if 'count' in col.lower()][0]
                total_count = result_df[count_col].sum()
                return f"Analysis shows {total_count:,} total records across {rows_count} groups."
            
            else:
                return f"Query returned {rows_count} rows with data about: {', '.join(columns[:3])}{'...' if len(columns) > 3 else ''}."
                
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return "Results obtained, but explanation generation failed."
    
    def get_sample_questions(self) -> list:
        """Return a list of sample questions users can ask."""
        return [
            "How many blacks were arrested?",
            "How many whites were arrested?",
            "Show me arrest counts by race",
            "Which race has the most stops?",
            "What are the peak hours for police stops?",
            "How many stops by district?",
            "Show stops by month over time"
        ] 