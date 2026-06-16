"""Italian NLQ patterns for ULE."""

PATTERNS = {
    r"mostra\s+tutti\s+i\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"mostra\s+tutte\s+le\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"mostra\s+tutti\s+gli\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"elenca\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"mostra\s+(\w+)\s+con\s+(\w+)\s+maggiore\s+di\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} > ?", [2]),

    r"mostra\s+(\w+)\s+con\s+(\w+)\s+minore\s+di\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} < ?", [2]),

    r"conta\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"quanti\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"numero\s+di\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"inserisci\s+in\s+(\w+)\s*\((.+)\)":
        ("SELECT * FROM {0}", [1]),

    r"nuovo\s+(\w+)\s+crea\s*\((.+)\)":
        ("SELECT * FROM {0}", [1]),

    r"crea\s+tabella\s+(\w+)\s*\((.+)\)":
        ("SELECT * FROM {0}", [1]),

    r"elimina\s+tabella\s+(\w+)":
        ("DROP TABLE {0}", []),

    r"mostra\s+tabelle":
        ("SELECT name FROM sqlite_master WHERE type='table'", []),

    r"elenca\s+tabelle":
        ("SELECT name FROM sqlite_master WHERE type='table'", []),
}
