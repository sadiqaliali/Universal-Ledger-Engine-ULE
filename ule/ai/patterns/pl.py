"""Polish NLQ patterns for ULE."""

PATTERNS = {
    r"poka[żz]\s+wszystkie\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"poka[żz]\s+wszystkich\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"poka[żz]\s+wszyscy\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"wy[śs]wietl\s+wszystkie\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"lista\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"poka[żz]\s+(\w+)\s+z\s+(\w+)\s+wi[ęe]ksze\s+ni[żz]\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} > ?", [2]),

    r"poka[żz]\s+(\w+)\s+z\s+(\w+)\s+mniejsze\s+ni[żz]\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} < ?", [2]),

    r"policz\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"ile\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"liczba\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"wstaw\s+do\s+(\w+)\s*\((.+)\)":
        ("SELECT * FROM {0}", [1]),

    r"nowy\s+(\w+)\s+utw[óo]rz\s*\((.+)\)":
        ("SELECT * FROM {0}", [1]),

    r"utw[óo]rz\s+tabel[ęe]\s+(\w+)\s*\((.+)\)":
        ("SELECT * FROM {0}", [1]),

    r"usu[ńn]\s+tabel[ęe]\s+(\w+)":
        ("DROP TABLE {0}", []),

    r"poka[żz]\s+tabele":
        ("SELECT name FROM sqlite_master WHERE type='table'", []),

    r"lista\s+tabel":
        ("SELECT name FROM sqlite_master WHERE type='table'", []),
}
