"""Portuguese language patterns for NLQ."""

PATTERNS = {
    r"mostrar\s+todos?\s+os?\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"ver\s+todos?\s+os?\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"mostrar\s+os?\s+(\w+)\s+com\s+mais\s+de\s+(\d+)\s+anos":
        ("SELECT * FROM {0} WHERE age > ?", [1]),

    r"mostrar\s+os?\s+(\w+)\s+com\s+menos\s+de\s+(\d+)\s+anos":
        ("SELECT * FROM {0} WHERE age < ?", [1]),

    r"contar\s+os?\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"quantos?\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"mostrar\s+os?\s+(\w+)\s+onde\s+(\w+)\s+é\s+maior\s+que\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} > ?", [2]),

    r"mostrar\s+os?\s+(\w+)\s+onde\s+(\w+)\s+é\s+menor\s+que\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} < ?", [2]),

    r"mostrar\s+os?\s+(\w+)\s+onde\s+(\w+)\s+é\s+igual\s+a\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} = ?", [2]),

    r"mostrar\s+as\s+tabelas":
        ("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_%'", []),

    r"listar\s+as\s+tabelas":
        ("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_%'", []),

    r"mostrar\s+todos?\s+os?\s+(\w+)\s+ordenados?\s+por\s+(\w+)":
        ("SELECT * FROM {0} ORDER BY {1}", []),

    r"mostrar\s+os?\s+(\d+)\s+primeiros?\s+(\w+)":
        ("SELECT * FROM {1} LIMIT ?", [0]),

    r"mostrar\s+os?\s+(\d+)\s+melhores?\s+(\w+)":
        ("SELECT * FROM {1} LIMIT ?", [0]),
}
