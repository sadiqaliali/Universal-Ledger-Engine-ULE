"""
ULE Transformer NLQ - HuggingFace Integration

Uses HuggingFace transformer models for improved natural language
query understanding and SQL generation.
"""

import re
from typing import Optional, Dict, Any, List, Tuple


class TransformerNLQ:
    """
    Transformer-based Natural Language to Query system.
    
    Uses HuggingFace models for better NLQ understanding.
    Falls back to pattern-based NLQ if transformers unavailable.
    
    Usage:
        nlq = TransformerNLQ()
        
        # Use transformer model if available
        if nlq.has_transformer:
            result = nlq.query_to_sql("show me all users older than 25")
        
        # Falls back to pattern matching
        result = nlq.query_to_sql("find products under $100")
    """
    
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or 't5-small'
        self._tokenizer = None
        self._model = None
        self._has_transformer = False
        
        # Try to load transformer
        self._try_load_model()
    
    def _try_load_model(self):
        """Try to load HuggingFace transformer model."""
        try:
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            self._has_transformer = True
        except ImportError:
            self._has_transformer = False
        except Exception as e:
            print(f"Warning: Could not load transformer model: {e}")
            self._has_transformer = False
    
    @property
    def has_transformer(self) -> bool:
        """Check if transformer model is loaded."""
        return self._has_transformer
    
    def query_to_sql(self, query: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Convert natural language query to SQL.
        
        Args:
            query: Natural language query
            schema: Database schema context
            
        Returns:
            Dict with 'sql', 'params', 'confidence', 'method'
        """
        if self._has_transformer:
            return self._transformer_query(query, schema)
        else:
            return self._fallback_query(query, schema)
    
    def _transformer_query(self, query: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Use transformer model to generate SQL."""
        try:
            # Prepare input
            prefix = "translate English to SQL: "
            input_text = prefix + query
            
            if schema:
                input_text += f" | Schema: {schema}"
            
            # Tokenize
            inputs = self._tokenizer(input_text, return_tensors='pt', max_length=512, truncation=True)
            
            # Generate
            outputs = self._model.generate(
                inputs['input_ids'],
                max_length=256,
                num_beams=4,
                early_stopping=True
            )
            
            # Decode
            sql = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Parse SQL from output
            return self._parse_transformer_output(sql, query)
            
        except Exception as e:
            return {
                'sql': None,
                'params': (),
                'confidence': 0.0,
                'method': 'transformer_error',
                'error': str(e)
            }
    
    def _parse_transformer_output(self, sql: str, original_query: str) -> Dict[str, Any]:
        """Parse and validate transformer output."""
        try:
            # Clean up SQL
            sql = sql.strip()
            if sql.startswith('```'):
                sql = sql[3:]
            if sql.endswith('```'):
                sql = sql[:-3]
            sql = sql.strip()
            
            # Extract parameters
            params = self._extract_params(sql)
            
            # Calculate confidence
            confidence = self._calculate_confidence(sql, original_query)
            
            return {
                'sql': sql if sql else None,
                'params': params,
                'confidence': confidence,
                'method': 'transformer'
            }
        except Exception as e:
            return {
                'sql': None,
                'params': (),
                'confidence': 0.0,
                'method': 'parse_error',
                'error': str(e)
            }
    
    def _fallback_query(self, query: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fallback to pattern-based query parsing."""
        query_lower = query.lower().strip()
        
        # Simple pattern matching
        patterns = [
            # SELECT all
            (r'(?:show|display|get|list|find)\s+(?:all\s+)?(\w+)', 'select_all'),
            # SELECT with condition
            (r'(?:show|display|get|list|find)\s+(\w+)\s+(?:where|with|that)\s+(.+)', 'select_where'),
            # COUNT
            (r'(?:count|how many)\s+(\w+)', 'count'),
            # INSERT
            (r'(?:add|insert|create)\s+(\w+)\s+(.+)', 'insert'),
            # DELETE
            (r'(?:delete|remove)\s+(\w+)\s+(?:where|with)?\s*(.*)', 'delete'),
            # UPDATE
            (r'(?:update|change|modify)\s+(\w+)\s+(?:set\s+)?(.+)', 'update'),
        ]
        
        for pattern, op_type in patterns:
            match = re.match(pattern, query_lower)
            if match:
                groups = match.groups()
                return self._build_query(op_type, groups, query)
        
        return {
            'sql': None,
            'params': (),
            'confidence': 0.0,
            'method': 'fallback_no_match',
            'error': 'No matching pattern found'
        }
    
    def _build_query(self, op_type: str, groups: Tuple, original_query: str) -> Dict[str, Any]:
        """Build SQL query from pattern match."""
        try:
            if op_type == 'select_all':
                table = groups[0]
                return {
                    'sql': f'SELECT * FROM {table}',
                    'params': (),
                    'confidence': 0.7,
                    'method': 'pattern'
                }
            
            elif op_type == 'select_where':
                table = groups[0]
                condition = groups[1]
                
                # Parse simple conditions
                condition_match = re.match(r'(\w+)\s*(>|<|=|>=|<=|!=)\s*(\S+)', condition)
                if condition_match:
                    col, op, val = condition_match.groups()
                    return {
                        'sql': f'SELECT * FROM {table} WHERE {col} {op} ?',
                        'params': (val,),
                        'confidence': 0.6,
                        'method': 'pattern'
                    }
                
                return {
                    'sql': f'SELECT * FROM {table}',
                    'params': (),
                    'confidence': 0.5,
                    'method': 'pattern'
                }
            
            elif op_type == 'count':
                table = groups[0]
                return {
                    'sql': f'SELECT COUNT(*) FROM {table}',
                    'params': (),
                    'confidence': 0.8,
                    'method': 'pattern'
                }
            
            elif op_type == 'insert':
                table = groups[0]
                values_str = groups[1]
                
                # Parse key=value pairs
                values = {}
                for match in re.finditer(r'(\w+)\s*[=:]\s*(\S+)', values_str):
                    values[match.group(1)] = match.group(2)
                
                if values:
                    columns = ', '.join(values.keys())
                    placeholders = ', '.join(['?' for _ in values])
                    return {
                        'sql': f'INSERT INTO {table} ({columns}) VALUES ({placeholders})',
                        'params': tuple(values.values()),
                        'confidence': 0.6,
                        'method': 'pattern'
                    }
            
            elif op_type == 'delete':
                table = groups[0]
                condition = groups[1] if len(groups) > 1 else ''
                
                if condition:
                    condition_match = re.match(r'(\w+)\s*(>|<|=|>=|<=|!=)\s*(\S+)', condition)
                    if condition_match:
                        col, op, val = condition_match.groups()
                        return {
                            'sql': f'DELETE FROM {table} WHERE {col} {op} ?',
                            'params': (val,),
                            'confidence': 0.6,
                            'method': 'pattern'
                        }
                
                return {
                    'sql': f'DELETE FROM {table}',
                    'params': (),
                    'confidence': 0.4,
                    'method': 'pattern'
                }
            
            elif op_type == 'update':
                table = groups[0]
                set_clause = groups[1]
                
                # Parse SET clause
                set_match = re.match(r'(\w+)\s*[=:]\s*(\S+)', set_clause)
                if set_match:
                    col, val = set_match.groups()
                    return {
                        'sql': f'UPDATE {table} SET {col} = ?',
                        'params': (val,),
                        'confidence': 0.5,
                        'method': 'pattern'
                    }
        
        except Exception as e:
            return {
                'sql': None,
                'params': (),
                'confidence': 0.0,
                'method': 'build_error',
                'error': str(e)
            }
        
        return {
            'sql': None,
            'params': (),
            'confidence': 0.0,
            'method': 'no_match'
        }
    
    def _extract_params(self, sql: str) -> Tuple:
        """Extract parameters from SQL."""
        params = []
        
        # Find values in WHERE clause
        where_match = re.search(r'WHERE\s+.+?\s*(=|>|<|>=|<=|!=)\s*[\'"]?([^\'"\s]+)[\'"]?', sql, re.IGNORECASE)
        if where_match:
            params.append(where_match.group(2))
        
        # Find VALUES
        values_match = re.search(r'VALUES\s*\((.+?)\)', sql, re.IGNORECASE)
        if values_match:
            values = values_match.group(1).split(',')
            params.extend([v.strip().strip("'\"") for v in values])
        
        return tuple(params)
    
    def _calculate_confidence(self, sql: str, original_query: str) -> float:
        """Calculate confidence in the generated SQL."""
        confidence = 0.5  # Base confidence
        
        # Increase if SQL looks valid
        if sql and any(kw in sql.upper() for kw in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']):
            confidence += 0.2
        
        # Decrease if SQL is incomplete
        if not sql or len(sql) < 10:
            confidence -= 0.3
        
        return max(0.0, min(1.0, confidence))
    
    def batch_query(self, queries: List[str], 
                   schema: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Process multiple queries.
        
        Args:
            queries: List of natural language queries
            schema: Database schema context
            
        Returns:
            List of results
        """
        return [self.query_to_sql(q, schema) for q in queries]
