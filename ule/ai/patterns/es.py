"""Spanish language patterns for NLQ."""

PATTERNS = {
    r"mostrar todos los usuarios":
        ("SELECT * FROM users", []),

    r"ver todos los usuarios":
        ("SELECT * FROM users", []),

    r"mostrar\s+todos?\s+los?\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"ver\s+todos?\s+los?\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"mostrar los usuarios mayores de\s+(\d+)\s+años":
        ("SELECT * FROM users WHERE age > ?", [0]),

    r"mostrar los usuarios menores de\s+(\d+)\s+años":
        ("SELECT * FROM users WHERE age < ?", [0]),

    r"contar los usuarios":
        ("SELECT * FROM {0}", []),

    r"cuántos usuarios":
        ("SELECT * FROM {0}", []),

    r"contar\s+los?\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"cuántos?\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"mostrar\s+los?\s+(\w+)\s+donde\s+(\w+)\s+es\s+mayor\s+que\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} > ?", [2]),

    r"mostrar\s+los?\s+(\w+)\s+donde\s+(\w+)\s+es\s+menor\s+que\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} < ?", [2]),

    r"mostrar\s+los?\s+(\w+)\s+donde\s+(\w+)\s+es\s+igual\s+a\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} = ?", [2]),

    r"mostrar\s+las\s+tablas":
        ("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_%'", []),

    r"listar\s+las\s+tablas":
        ("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_%'", []),

    r"mostrar\s+todos?\s+los?\s+(\w+)\s+ordenados?\s+por\s+(\w+)":
        ("SELECT * FROM {0} ORDER BY {1}", []),

    r"mostrar\s+los?\s+(\d+)\s+primeros?\s+(\w+)":
        ("SELECT * FROM {1} LIMIT ?", [0]),

    r"mostrar\s+los?\s+(\d+)\s+mejores?\s+(\w+)":
        ("SELECT * FROM {1} LIMIT ?", [0]),
}
