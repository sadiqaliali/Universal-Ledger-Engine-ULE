"""Natural Language Query engine for ULE - 20 languages."""

import re
import json
from typing import Optional, Dict, List, Any, Tuple
from pathlib import Path

# Import language pattern modules
from ule.ai.patterns import en, ur, zh, fr, ru, ja, ko, es, pt, hi, ar, bn, tr, id, vi, th, de, it, pl, sv


class SQLResult(str):
    """String that carries parameters."""
    def __new__(cls, sql, params):
        obj = super().__new__(cls, sql)
        obj.params = params
        return obj

class NaturalLanguageQuery:
    """
    Natural Language to SQL translator.

    Supports: English, Chinese, Urdu, French, Russian,
              Japanese, Korean, Spanish, Portuguese, Hindi,
              Arabic, Bengali, Turkish, Indonesian, Vietnamese, Thai,
              German, Italian, Polish, Swedish
    """

    LANGUAGE_MODULES = {
        "en": en,
        "ur": ur,
        "zh": zh,
        "fr": fr,
        "ru": ru,
        "ja": ja,
        "ko": ko,
        "es": es,
        "pt": pt,
        "hi": hi,
        "ar": ar,
        "bn": bn,
        "tr": tr,
        "id": id,
        "vi": vi,
        "th": th,
        "de": de,
        "it": it,
        "pl": pl,
        "sv": sv,
    }
    
    def __init__(self, db_connection):
        self._conn = db_connection
        self._patterns: Dict[str, List[Tuple[re.Pattern, str]]] = {}
        self._load_patterns()
    
    def _load_patterns(self) -> None:
        """Load patterns for all languages."""
        for lang_code, module in self.LANGUAGE_MODULES.items():
            self._patterns[lang_code] = []
            
            if hasattr(module, "PATTERNS"):
                for pattern, template in module.PATTERNS.items():
                    try:
                        regex = re.compile(pattern, re.IGNORECASE)
                        self._patterns[lang_code].append((regex, template))
                    except re.error:
                        pass  # Skip invalid patterns
    
    def translate(self, query: str, language: str = "en") -> Optional[Tuple[str, tuple]]:
        """
        Translate natural language to SQL with parameters.
        
        Args:
            query: Natural language query
            language: Language code
        
        Returns:
            Tuple of (SQL query, params) or None if no match
        """
        if language not in self._patterns:
            raise ValueError(f"Unsupported language: {language}")
        
        patterns = self._patterns[language]
        
        for regex, template_data in patterns:
            match = regex.search(query)
            if match:
                try:
                    # template_data can be a string (legacy) or a tuple (template, param_group_indices)
                    if isinstance(template_data, tuple):
                        template, param_indices = template_data
                        
                        # Extract and quote groups for identifier formatting
                        groups = list(match.groups())
                        
                        # Quoting all groups that might be used as identifiers
                        # This ensures {0}, {1}, etc. in the template are safely escaped
                        # We use double quotes for SQLite identifiers
                        quoted_groups = ['"{0}"'.format(g.replace('"', '""')) for g in groups]
                        
                        # Construct params based on indices
                        params = tuple(groups[i] for i in param_indices)
                        
                        # Format the SQL with quoted identifiers
                        sql = template.format(*quoted_groups)
                        return SQLResult(sql, params)
                    else:
                        # Fallback for legacy string-only patterns (mark for deprecation)
                        sql = template_data.format(*match.groups())
                        return SQLResult(sql, ())
                except (IndexError, KeyError):
                    continue
        
        return None
    
    def ask(self, query: str, language: str = "en") -> List[Dict]:
        """
        Execute natural language query safely.
        """
        result = self.translate(query, language)
        
        if not result:
            # Try direct execution as fallback if it looks like safe SQL
            if query.strip().upper().startswith(("SELECT ", "SHOW ", "FIND ")):
                return self._execute_direct(query)
            raise ValueError(f"Could not understand query: {query}")
        
        return self._execute_sql(result, result.params)
    
    def _execute_sql(self, sql: str, params: tuple = ()) -> List[Dict]:
        """Execute SQL query with parameters."""
        cursor = self._conn.execute(sql, params)
        
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return []
    
    def _execute_direct(self, query: str) -> List[Dict]:
        """Try to execute query directly."""
        # Clean up query
        sql = query.strip()
        
        # Handle SHOW as SELECT
        if sql.upper().startswith("SHOW"):
            sql = "SELECT" + sql[4:]
        
        try:
            return self._execute_sql(sql)
        except Exception:
            raise ValueError(f"Could not execute query: {query}")
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes."""
        return list(self.LANGUAGE_MODULES.keys())
    
    def add_pattern(self, language: str, pattern: str, template: str) -> bool:
        """
        Add custom pattern for language.
        
        Args:
            language: Language code
            pattern: Regex pattern
            template: SQL template
        
        Returns:
            True if added successfully
        """
        if language not in self.LANGUAGE_MODULES:
            return False
        
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            self._patterns[language].append((regex, template))
            return True
        except re.error:
            return False


class HybridNLQ:
    """
    Hybrid Natural Language Query engine.
    
    Uses high-speed Regex patterns first, falls back to 
    Transformer models for semantic complexity.
    """
    
    def __init__(self, db_connection, model_name: Optional[str] = None):
        self.regex_nlq = NaturalLanguageQuery(db_connection)
        from ule.ai.transformer_nlq import TransformerNLQ
        self.transformer_nlq = TransformerNLQ(model_name)
        self._conn = db_connection
    
    def ask(self, query: str, language: str = "en", schema: Optional[Dict] = None) -> List[Dict]:
        """
        Execute natural language query using hybrid approach.
        """
        # 1. Try Regex first (fastest, lowest cost)
        result = self.regex_nlq.translate(query, language)
        sql = result if result else None
        params = result.params if result else ()
        
        # 2. Try Transformer if regex fails
        if not sql and self.transformer_nlq.has_transformer:
            t_result = self.transformer_nlq.query_to_sql(query, schema)
            sql = t_result.get('sql')
            params = t_result.get('params', ())
        
        if not sql:
            # Last resort: direct execution if it looks like SQL
            if query.strip().upper().startswith(("SELECT", "SHOW", "FIND")):
                return self.regex_nlq._execute_direct(query)
            raise ValueError(f"Could not understand query: {query}")
        
        return self.regex_nlq._execute_sql(sql, params)
