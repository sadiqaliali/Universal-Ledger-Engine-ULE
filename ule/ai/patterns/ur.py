"""Urdu language patterns for NLQ."""

# Urdu to English table name mapping
TABLE_MAP = {
    'صارفین': 'users',
    'صارف': 'users', 
    'لوگ': 'users',
    'آرڈرز': 'orders',
    'آرڈر': 'orders',
    'پراڈکٹس': 'products',
    'پراڈکٹ': 'products',
}

PATTERNS = {
    r"تمام\s+صارفین\s+دکھائیں":
        ("SELECT * FROM users", []),

    r"سب\s+صارفین\s+دکھائیں":
        ("SELECT * FROM users", []),

    r"تمام\s+صارف\s+دکھائیں":
        ("SELECT * FROM users", []),

    r"تمام\s+(صارفین|صارف|لوگ)\s+دکھائیں":
        ("SELECT * FROM users", [0]),

    r"سب\s+(صارفین|صارف|لوگ)\s+دکھائیں":
        ("SELECT * FROM users", [0]),

    r"users\s+دکھائیں\s+جن\s+کی\s+عمر\s+(\d+)\s+سے\s+زیادہ\s+ہے":
        ("SELECT * FROM users WHERE age > ?", [0]),

    r"صارفین\s+دکھائیں\s+جن\s+کی\s+عمر\s+(\d+)\s+سے\s+زیادہ\s+ہے":
        ("SELECT * FROM users WHERE age > ?", [0]),

    r"صارفین\s+دکھائیں\s+جو\s+(\d+)\s+سے\s+بڑی\s+عمر\s+کے\s+ہیں":
        ("SELECT * FROM users WHERE age > ?", [0]),

    r"صارفین\s+دکھائیں\s+جن\s+کی\s+عمر\s+(\d+)\s+سے\s+کم\s+ہے":
        ("SELECT * FROM users WHERE age < ?", [0]),

    r"کل\s+users\s+گنیں":
        ("SELECT * FROM {0}", []),

    r"کل\s+صارفین\s+گنیں":
        ("SELECT * FROM {0}", []),

    r"صارفین\s+کی\s+تعداد\s+بتائیں":
        ("SELECT * FROM {0}", []),

    r"صارفین\s+کی\s+تعداد\s+دکھائیں":
        ("SELECT * FROM {0}", []),

    r"صارفین\s+گنیں":
        ("SELECT * FROM {0}", []),

    r"تمام\s+(\w+)\s+دکھائیں":
        ("SELECT * FROM {0}", []),

    r"سب\s+(\w+)\s+دکھائیں":
        ("SELECT * FROM {0}", []),

    r"(\w+)\s+دکھائیں\s+جہاں\s+(\w+)\s+(\d+)\s+سے\s+زیادہ\s+ہو":
        ("SELECT * FROM {0} WHERE {1} > ?", [2]),

    r"(\w+)\s+دکھائیں\s+جہاں\s+(\w+)\s+(\d+)\s+سے\s+کم\s+ہو":
        ("SELECT * FROM {0} WHERE {1} < ?", [2]),

    r"(\w+)\s+دکھائیں\s+جہاں\s+(\w+)\s+(\d+)\s+کے\s+برابر\s+ہو":
        ("SELECT * FROM {0} WHERE {1} = ?", [2]),

    r"ٹیبلز\s+دکھائیں":
        ("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_%'", []),

    r"تمام\s+ٹیبلز\s+کی\s+فہرست":
        ("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_%'", []),

    r"(\w+)\s+دکھائیں\s+ترتیب\s+سے\s+(\w+)":
        ("SELECT * FROM {0} ORDER BY {1}", []),

    r"اوپر\s+کے\s+(\d+)\s+(\w+)\s+دکھائیں":
        ("SELECT * FROM {1} LIMIT ?", [0]),

    r"پہلے\s+(\d+)\s+(\w+)\s+دکھائیں":
        ("SELECT * FROM {1} LIMIT ?", [0]),
}
