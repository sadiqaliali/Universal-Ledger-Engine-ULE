"""Korean language patterns for NLQ."""

PATTERNS = {
    r"모든\s+(\w+)\s+표시":
        ("SELECT * FROM {0}", []),

    r"전체\s+(\w+)\s+보여줘":
        ("SELECT * FROM {0}", []),

    r"(\d+)\s+세\s+이상의\s+(\w+)\s+표시":
        ("SELECT * FROM {1} WHERE age > ?", [0]),

    r"(\d+)\s+세\s+미만의\s+(\w+)\s+표시":
        ("SELECT * FROM {1} WHERE age < ?", [0]),

    r"(\w+)\s+개수\s+세기":
        ("SELECT * FROM {0}", []),

    r"(\w+)\s+몇\s+개":
        ("SELECT * FROM {0}", []),

    r"(\w+)\s+표시\s+(\w+)\s*가\s+(\d+)\s*보다\s+큰":
        ("SELECT * FROM {0} WHERE {1} > ?", [2]),

    r"(\w+)\s+표시\s+(\w+)\s*가\s+(\d+)\s*보다\s+작은":
        ("SELECT * FROM {0} WHERE {1} < ?", [2]),

    r"(\w+)\s+표시\s+(\w+)\s*가\s+(\d+)\s*와\s+같은":
        ("SELECT * FROM {0} WHERE {1} = ?", [2]),

    r"테이블\s+표시":
        ("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_%'", []),

    r"전체\s+테이블\s+목록":
        ("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_%'", []),

    r"모든\s+(\w+)\s+(\w+)\s*로\s+정렬하여\s+표시":
        ("SELECT * FROM {0} ORDER BY {1}", []),

    r"처음\s+(\d+)\s+개의\s+(\w+)\s+표시":
        ("SELECT * FROM {1} LIMIT ?", [0]),

    r"상위\s+(\d+)\s+개의\s+(\w+)\s+표시":
        ("SELECT * FROM {1} LIMIT ?", [0]),
}
