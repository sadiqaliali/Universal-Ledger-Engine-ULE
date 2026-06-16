"""German NLQ patterns for ULE."""

PATTERNS = {
    r"zeige\s+alle\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"liste\s+alle\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"alle\s+(\w+)\s+anzeigen":
        ("SELECT * FROM {0}", []),

    r"zeige\s+(\w+)\s+mit\s+(\w+)\s+gr[öo]ßer\s+als\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} > ?", [2]),

    r"zeige\s+(\w+)\s+mit\s+(\w+)\s+kleiner\s+als\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} < ?", [2]),

    r"z[äa]hle\s+(\w+)":
        ("SELECT COUNT(*) FROM {0}", []),

    r"wie\s+viele\s+(\w+)":
        ("SELECT COUNT(*) FROM {0}", []),

    r"anzahl\s+(\w+)":
        ("SELECT COUNT(*) FROM {0}", []),

    r"f[üu]ge\s+(\w+)\s+ein\s*\((.+)\)":
        ("SELECT * FROM {0}", [1]),

    r"neue\s+(\w+)\s+erstellen\s*\((.+)\)":
        ("SELECT * FROM {0}", [1]),

    r"erstelle\s+tabelle\s+(\w+)\s*\((.+)\)":
        ("SELECT * FROM {0}", [1]),

    r"l[öo]sche\s+tabelle\s+(\w+)":
        ("DROP TABLE {0}", []),

    r"zeige\s+tabellen":
        ("SELECT name FROM sqlite_master WHERE type='table'", []),

    r"liste\s+tabellen":
        ("SELECT name FROM sqlite_master WHERE type='table'", []),
}
