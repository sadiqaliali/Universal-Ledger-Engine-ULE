"""Swedish NLQ patterns for ULE."""

PATTERNS = {
    r"visa\s+alla\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"lista\s+alla\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"alla\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"visa\s+(\w+)\s+med\s+(\w+)\s+st[öo]rre\s+[aä]n\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} > ?", [2]),

    r"visa\s+(\w+)\s+med\s+(\w+)\s+mindre\s+[aä]n\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} < ?", [2]),

    r"r[äa]kna\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"hur\s+m[åa]nga\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"antal\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"infoga\s+i\s+(\w+)\s*\((.+)\)":
        ("SELECT * FROM {0}", [1]),

    r"ny\s+(\w+)\s+skapa\s*\((.+)\)":
        ("SELECT * FROM {0}", [1]),

    r"skapa\s+tabell\s+(\w+)\s*\((.+)\)":
        ("SELECT * FROM {0}", [1]),

    r"ta\s+bort\s+tabell\s+(\w+)":
        ("DROP TABLE {0}", []),

    r"visa\s+tabeller":
        ("SELECT name FROM sqlite_master WHERE type='table'", []),

    r"lista\s+tabeller":
        ("SELECT name FROM sqlite_master WHERE type='table'", []),
}
