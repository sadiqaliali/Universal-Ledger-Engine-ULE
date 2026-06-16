"""Hindi language patterns for NLQ."""

# Order matters! More specific patterns must come before general patterns.
PATTERNS = {
    r"सभी\s+(\w+)\s+दिखाएं\s+जिनकी\s+उम्र\s+(\d+)\s+से\s+अधिक\s+है":
        ("SELECT * FROM {0} WHERE age > ?", [1]),

    r"(\w+)\s+दिखाएं\s+जो\s+(\d+)\s+साल\s+से\s+बड़े\s+हैं":
        ("SELECT * FROM {0} WHERE age > ?", [1]),

    r"सभी\s+(\w+)\s+दिखाएं\s+जिनकी\s+उम्र\s+(\d+)\s+से\s+कम\s+है":
        ("SELECT * FROM {0} WHERE age < ?", [1]),

    r"सभी\s+उपयोगकर्ता\s+दिखाएं":
        ("SELECT * FROM users", []),

    r"सभी\s+लोग\s+दिखाएं":
        ("SELECT * FROM users", []),

    r"सभी\s+(\w+)\s+दिखाएं":
        ("SELECT * FROM {0}", []),

    r"सारे\s+(\w+)\s+दिखाएं":
        ("SELECT * FROM {0}", []),

    r"कुल\s+(\w+)\s+गिनें":
        ("SELECT * FROM {0}", []),

    r"(\w+)\s+की\s+गिनती\s+करीं":
        ("SELECT * FROM {0}", []),

    r"कितने\s+(\w+)\s+हैं":
        ("SELECT * FROM {0}", []),

    r"(\w+)\s+दिखाएं\s+जहां\s+(\w+)\s+(\d+)\s+से\s+अधिक\s+है":
        ("SELECT * FROM {0} WHERE {1} > ?", [2]),

    r"(\w+)\s+दिखाएं\s+जहां\s+(\w+)\s+(\d+)\s+से\s+कम\s+है":
        ("SELECT * FROM {0} WHERE {1} < ?", [2]),

    r"(\w+)\s+दिखाएं\s+जहां\s+(\w+)\s+(\d+)\s+के\s+बराबर\s+है":
        ("SELECT * FROM {0} WHERE {1} = ?", [2]),

    r"टेबल\s+दिखाएं":
        ("SELECT name FROM sqlite_master WHERE type='table'", []),

    r"सभी\s+टेबल\s+की\s+सूची\s+दिखाएं":
        ("SELECT name FROM sqlite_master WHERE type='table'", []),

    r"सभी\s+(\w+)\s+दिखाएं\s+(\w+)\s+के\s+अनुसार\s+क्रमबद्ध":
        ("SELECT * FROM {0} ORDER BY {1}", []),

    r"शीर्ष\s+(\d+)\s+(\w+)\s+दिखाएं":
        ("SELECT * FROM {0} LIMIT ?", [1]),
}
