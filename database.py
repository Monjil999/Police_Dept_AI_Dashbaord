import sqlite3
import pandas as pd
import json
import hashlib
import time
from typing import Optional, Dict, Any
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import redis
from config import DATABASE_URL, REDIS_URL, CACHE_EXPIRY
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Class-level flag to avoid repeated cache status logging
_cache_status_logged = False

class DatabaseManager:
    def __init__(self):
        global _cache_status_logged
        self.engine = create_engine(DATABASE_URL)
        self.redis_client = None
        self._redis_available = False
        
        # Try to connect to Redis quietly, fallback to in-memory cache
        try:
            self.redis_client = redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=1)
            self.redis_client.ping()
            self._redis_available = True
            if not _cache_status_logged:
                logger.info("Redis cache connection established")
                _cache_status_logged = True
        except Exception:
            # Silent fallback to in-memory cache
            self._redis_available = False
            self._memory_cache = {}
            if not _cache_status_logged:
                logger.info("Using in-memory cache (Redis not available)")
                _cache_status_logged = True
    
    def _get_table_name(self, department: str) -> str:
        """Generate clean table name from department name."""
        clean_dept = department.lower()
        # Remove various forms of "police department"
        clean_dept = clean_dept.replace(' police department', '')
        clean_dept = clean_dept.replace('police department', '')
        clean_dept = clean_dept.replace('department', '')
        clean_dept = clean_dept.replace(' police', '')
        clean_dept = clean_dept.replace('police', '')
        # Clean up spaces and special characters
        clean_dept = clean_dept.replace(' ', '_')
        clean_dept = clean_dept.replace('-', '_')
        clean_dept = clean_dept.strip('_')  # Remove leading/trailing underscores
        # Remove duplicate underscores
        while '__' in clean_dept:
            clean_dept = clean_dept.replace('__', '_')
        return f"police_data_{clean_dept}"
    
    def _get_cache_key(self, key: str) -> str:
        """Generate a cache key."""
        return f"police_data:{hashlib.md5(key.encode()).hexdigest()}"
    
    def cache_set(self, key: str, value: Any, expiry: int = CACHE_EXPIRY):
        """Set a value in cache."""
        try:
            cache_key = self._get_cache_key(key)
            if self._redis_available and self.redis_client:
                self.redis_client.setex(cache_key, expiry, json.dumps(value))
            else:
                self._memory_cache[cache_key] = {
                    'value': value,
                    'expiry': time.time() + expiry
                }
        except Exception:
            # Silently fallback to memory cache
            if not hasattr(self, '_memory_cache'):
                self._memory_cache = {}
            cache_key = self._get_cache_key(key)
            self._memory_cache[cache_key] = {
                'value': value,
                'expiry': time.time() + expiry
            }
    
    def cache_get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        try:
            cache_key = self._get_cache_key(key)
            if self._redis_available and self.redis_client:
                cached = self.redis_client.get(cache_key)
                return json.loads(cached) if cached else None
            else:
                if not hasattr(self, '_memory_cache'):
                    self._memory_cache = {}
                cached = self._memory_cache.get(cache_key)
                if cached and cached['expiry'] > time.time():
                    return cached['value']
                elif cached:
                    del self._memory_cache[cache_key]
                return None
        except Exception:
            # Silently fallback to memory cache
            if not hasattr(self, '_memory_cache'):
                return None
            cached = self._memory_cache.get(self._get_cache_key(key))
            if cached and cached['expiry'] > time.time():
                return cached['value']
            return None
    
    def store_police_data(self, department: str, data: pd.DataFrame, metadata: Dict):
        """Store police data in the database."""
        try:
            table_name = self._get_table_name(department)
            
            # Clean the dataframe to avoid column issues
            clean_data = data.copy()
            
            # Remove any duplicate columns
            clean_data = clean_data.loc[:, ~clean_data.columns.duplicated()]
            
            # Clean column names to avoid SQLite issues
            clean_columns = {}
            for col in clean_data.columns:
                # Replace problematic characters in column names
                clean_col = str(col).replace(' ', '_').replace('-', '_').replace('.', '_')
                clean_col = ''.join(c for c in clean_col if c.isalnum() or c == '_')
                clean_col = clean_col.strip('_')
                clean_columns[col] = clean_col
            
            clean_data = clean_data.rename(columns=clean_columns)
            
            # Ensure no duplicate column names after cleaning
            if len(clean_data.columns) != len(set(clean_data.columns)):
                logger.warning("Duplicate column names detected after cleaning, removing duplicates")
                clean_data = clean_data.loc[:, ~clean_data.columns.duplicated()]
            
            # Drop existing table first to avoid conflicts
            with self.engine.connect() as conn:
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                    conn.execute(text(f"DROP TABLE IF EXISTS {table_name}_metadata"))
                    conn.commit()
                except Exception:
                    pass  # Table might not exist, which is fine
            
            # Store the cleaned data
            clean_data.to_sql(table_name, self.engine, if_exists='replace', index=False)
            
            # Store metadata (convert lists to JSON strings)
            metadata_table = f"{table_name}_metadata"
            metadata_copy = metadata.copy()
            
            # Convert lists to JSON strings for storage
            for key, value in metadata_copy.items():
                if isinstance(value, (list, dict)):
                    metadata_copy[key] = json.dumps(value)
            
            metadata_df = pd.DataFrame([metadata_copy])
            metadata_df.to_sql(metadata_table, self.engine, if_exists='replace', index=False)
            
            logger.info(f"Data stored for {department}: {len(clean_data)} rows in table {table_name}")
            return table_name
            
        except Exception as e:
            logger.error(f"Error storing data: {e}")
            return None
    
    def get_police_data(self, department: str) -> Optional[pd.DataFrame]:
        """Retrieve police data from database."""
        try:
            table_name = self._get_table_name(department)
            
            # Check cache first
            cached_data = self.cache_get(f"data_{table_name}")
            if cached_data:
                return pd.DataFrame(cached_data)
            
            # Query from database
            df = pd.read_sql_table(table_name, self.engine)
            
            # Cache the result
            self.cache_set(f"data_{table_name}", df.to_dict('records'))
            
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving data: {e}")
            return None
    
    def execute_sql_query(self, query: str, department: str) -> Optional[pd.DataFrame]:
        """Execute a SQL query on police data."""
        try:
            table_name = self._get_table_name(department)
            logger.info(f"Executing query for department '{department}' using table '{table_name}'")
            
            # Smart table name replacement - only replace standalone 'police_data' not 'police_data_xxx'
            query = re.sub(r'\bpolice_data\b(?!_)', table_name, query)
            logger.info(f"Query after table replacement: {query[:100]}...")
            
            # Cache key for the query
            cache_key = f"query_{hashlib.md5(query.encode()).hexdigest()}"
            cached_result = self.cache_get(cache_key)
            if cached_result:
                logger.info("Returning cached query result")
                return pd.DataFrame(cached_result)
            
            # Execute query
            with self.engine.connect() as conn:
                result = pd.read_sql_query(text(query), conn)
            
            logger.info(f"Query executed successfully, returned {len(result)} rows")
            
            # Cache the result
            self.cache_set(cache_key, result.to_dict('records'))
            
            return result
            
        except SQLAlchemyError as e:
            logger.error(f"SQL execution error for department '{department}': {e}")
            logger.error(f"Failed query: {query}")
            return None
        except Exception as e:
            logger.error(f"Query execution error for department '{department}': {e}")
            logger.error(f"Failed query: {query}")
            return None
    
    def get_table_schema(self, department: str) -> Optional[Dict]:
        """Get the schema of the police data table."""
        try:
            table_name = self._get_table_name(department)
            
            # Check cache first
            cache_key = f"schema_{table_name}"
            cached_schema = self.cache_get(cache_key)
            if cached_schema:
                return cached_schema
            
            # Get schema from database
            with self.engine.connect() as conn:
                result = conn.execute(text(f"PRAGMA table_info({table_name})"))
                columns = result.fetchall()
                
                schema = {
                    'table_name': table_name,
                    'columns': [
                        {
                            'name': col[1],
                            'type': col[2],
                            'nullable': not col[3],
                            'primary_key': bool(col[5])
                        }
                        for col in columns
                    ]
                }
                
                # Cache the schema
                self.cache_set(cache_key, schema)
                return schema
                
        except Exception as e:
            logger.error(f"Error getting table schema: {e}")
            return None
    
    def get_sample_data(self, department: str, limit: int = 5) -> Optional[pd.DataFrame]:
        """Get sample data for preview."""
        try:
            table_name = self._get_table_name(department)
            
            with self.engine.connect() as conn:
                query = text(f"SELECT * FROM {table_name} LIMIT {limit}")
                result = pd.read_sql_query(query, conn)
                
            return result
            
        except Exception as e:
            logger.error(f"Error getting sample data: {e}")
            return None 