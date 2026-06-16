"""English language patterns for NLQ (Parameterized)."""

# Structure: { regex: (sql_template, param_group_indices) }
# {0} is always the sanitized table name.
# ? are the positional parameters.

PATTERNS = {
    r"show\s+all\s+(\w+)\s+older\s+than\s+(\d+)":
        ("SELECT * FROM {0} WHERE age > ?", [1]),

    r"show\s+(\w+)\s+older\s+than\s+(\d+)":
        ("SELECT * FROM {0} WHERE age > ?", [1]),

    r"show\s+all\s+(\w+)\s+younger\s+than\s+(\d+)":
        ("SELECT * FROM {0} WHERE age < ?", [1]),

    r"show\s+(\w+)\s+younger\s+than\s+(\d+)":
        ("SELECT * FROM {0} WHERE age < ?", [1]),

    r"show\s+all\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"display\s+all\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"count\s+all\s+(\w+)":
        ("SELECT COUNT(*) FROM {0}", []),

    r"how\s+many\s+(\w+)":
        ("SELECT COUNT(*) FROM {0}", []),

    r"show\s+(\w+)\s+where\s+(\w+)\s+greater\s+than\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} > ?", [2]),

    r"find\s+(\w+)\s+with\s+(\w+)\s+above\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} > ?", [2]),

    r"show\s+(\w+)\s+where\s+(\w+)\s+less\s+than\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} < ?", [2]),

    r"find\s+(\w+)\s+with\s+(\w+)\s+below\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} < ?", [2]),

    r"show\s+(\w+)\s+where\s+(\w+)\s+equals?\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} = ?", [2]),

    r"find\s+(\w+)\s+with\s+(\w+)\s+equal\s+to\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} = ?", [2]),

    r"show\s+tables":
        ("SELECT name FROM sqlite_master WHERE type='table'", []),

    r"list\s+tables":
        ("SELECT name FROM sqlite_master WHERE type='table'", []),

    r"show\s+all\s+(\w+)\s+ordered\s+by\s+(\w+)":
        ("SELECT * FROM {0} ORDER BY {1}", []),

    r"show\s+all\s+(\w+)\s+sorted\s+by\s+(\w+)":
        ("SELECT * FROM {0} ORDER BY {1}", []),

    r"show\s+top\s+(\d+)\s+(\w+)":
        ("SELECT * FROM {1} LIMIT ?", [0]),

    r"show\s+first\s+(\d+)\s+(\w+)":
        ("SELECT * FROM {1} LIMIT ?", [0]),
}
