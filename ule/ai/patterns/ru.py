"""Russian language patterns for NLQ."""

PATTERNS = {
    r"показать\s+всех?\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"отобразить\s+всех?\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"показать\s+(\w+)\s+старше\s+(\d+)\s+лет":
        ("SELECT * FROM {0} WHERE age > ?", [1]),

    r"показать\s+(\w+)\s+младше\s+(\d+)\s+лет":
        ("SELECT * FROM {0} WHERE age < ?", [1]),

    r"посчитать\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"сколько\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"показать\s+(\w+)\s+где\s+(\w+)\s+больше\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} > ?", [2]),

    r"показать\s+(\w+)\s+где\s+(\w+)\s+меньше\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} < ?", [2]),

    r"показать\s+(\w+)\s+где\s+(\w+)\s+равно\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} = ?", [2]),

    r"показать\s+таблицы":
        ("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_%'", []),

    r"список\s+таблиц":
        ("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_%'", []),

    r"показать\s+всех?\s+(\w+)\s+отсортировано\s+по\s+(\w+)":
        ("SELECT * FROM {0} ORDER BY {1}", []),

    r"показать\s+первые\s+(\d+)\s+(\w+)":
        ("SELECT * FROM {1} LIMIT ?", [0]),

    r"показать\s+топ\s+(\d+)\s+(\w+)":
        ("SELECT * FROM {1} LIMIT ?", [0]),
}
