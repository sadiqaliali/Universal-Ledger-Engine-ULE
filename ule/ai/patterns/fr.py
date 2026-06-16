"""French language patterns for NLQ."""

PATTERNS = {
    r"afficher tous les utilisateurs":
        ("SELECT * FROM users", []),

    r"montrer tous les utilisateurs":
        ("SELECT * FROM users", []),

    r"afficher\s+tous\s+les\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"montrer\s+tous\s+les\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"afficher les utilisateurs de plus de\s+(\d+)\s+ans":
        ("SELECT * FROM users WHERE age > ?", [0]),

    r"afficher les utilisateurs de moins de\s+(\d+)\s+ans":
        ("SELECT * FROM users WHERE age < ?", [0]),

    r"compter les utilisateurs":
        ("SELECT * FROM {0}", []),

    r"combien d'utilisateurs":
        ("SELECT * FROM {0}", []),

    r"compter\s+les\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"combien\s+de\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"afficher\s+les\s+(\w+)\s+où\s+(\w+)\s+est\s+supérieur\s+à\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} > ?", [2]),

    r"afficher\s+les\s+(\w+)\s+où\s+(\w+)\s+est\s+inférieur\s+à\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} < ?", [2]),

    r"afficher\s+les\s+(\w+)\s+où\s+(\w+)\s+égale?\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} = ?", [2]),

    r"afficher\s+les\s+tables":
        ("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_%'", []),

    r"lister\s+les\s+tables":
        ("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_%'", []),

    r"afficher\s+tous\s+les\s+(\w+)\s+triés\s+par\s+(\w+)":
        ("SELECT * FROM {0} ORDER BY {1}", []),

    r"afficher\s+les\s+(\d+)\s+premiers\s+(\w+)":
        ("SELECT * FROM {1} LIMIT ?", [0]),
}
