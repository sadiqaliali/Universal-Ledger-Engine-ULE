"""Utility helper functions for ULE."""

import time
from typing import List, Dict, Any
from contextlib import contextmanager


def format_table(data: List[Dict], max_width: int = 30) -> str:
    """
    Format list of dicts as ASCII table.
    
    Args:
        data: List of row dicts
        max_width: Maximum column width
    
    Returns:
        Formatted table string
    """
    if not data:
        return "(no rows)"
    
    # Get headers
    headers = list(data[0].keys())
    
    # Calculate column widths
    widths = {}
    for header in headers:
        max_len = len(str(header))
        for row in data:
            val_len = len(str(row.get(header, "")))
            max_len = max(max_len, val_len)
        widths[header] = min(max_len, max_width)
    
    # Build table
    lines = []
    
    # Header separator
    separator = "+" + "+".join("-" * (widths[h] + 2) for h in headers) + "+"
    lines.append(separator)
    
    # Header row
    header_row = "|" + "|".join(f" {str(h).ljust(widths[h])} " for h in headers) + "|"
    lines.append(header_row)
    lines.append(separator)
    
    # Data rows
    for row in data:
        data_row = "|" + "|".join(
            f" {str(row.get(h, '')).ljust(widths[h])} " for h in headers
        ) + "|"
        lines.append(data_row)
    
    lines.append(separator)
    
    # Row count
    lines.append(f"({len(data)} rows)")
    
    return "\n".join(lines)


@contextmanager
def timer(operation: str = "Operation"):
    """Context manager to time operations."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        print(f"{operation} completed in {elapsed:.4f} seconds")


def truncate_string(s: str, max_length: int = 50) -> str:
    """Truncate string with ellipsis."""
    if len(s) <= max_length:
        return s
    return s[:max_length - 3] + "..."


def format_bytes(size: int) -> str:
    """Format bytes to human readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def validate_identifier(name: str) -> bool:
    """Validate SQL identifier."""
    if not name:
        return False
    
    # Must start with letter or underscore
    if not (name[0].isalpha() or name[0] == '_'):
        return False
    
    # Rest can be alphanumeric or underscore
    for char in name[1:]:
        if not (char.isalnum() or char == '_'):
            return False
    
    # Check for reserved words
    reserved = {
        'select', 'insert', 'update', 'delete', 'from', 'where',
        'create', 'drop', 'alter', 'table', 'index', 'view',
        'and', 'or', 'not', 'in', 'is', 'null', 'like', 'between'
    }
    
    return name.lower() not in reserved


def escape_string(s: str) -> str:
    """Escape string for SQL."""
    return s.replace("'", "''")


def parse_connection_string(conn_str: str) -> Dict[str, Any]:
    """Parse connection string into dict."""
    params = {}
    
    if ';' in conn_str:
        for part in conn_str.split(';'):
            if '=' in part:
                key, value = part.split('=', 1)
                params[key.strip()] = value.strip()
    
    return params
