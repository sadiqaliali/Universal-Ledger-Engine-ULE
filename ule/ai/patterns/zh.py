"""Chinese language patterns for NLQ."""

PATTERNS = {
    r"显示所有用户":
        ("SELECT * FROM users", []),

    r"列出所有用户":
        ("SELECT * FROM users", []),

    r"显示所有\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"列出所有\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"显示\s+(\d+)\s+岁以上的\s+(\w+)":
        ("SELECT * FROM {1} WHERE age > ?", [0]),

    r"显示\s+(\d+)\s+岁以下的\s+(\w+)":
        ("SELECT * FROM {1} WHERE age < ?", [0]),

    r"显示\s+(\d+)\s+岁以上的用户":
        ("SELECT * FROM users WHERE age > ?", [0]),

    r"显示\s+(\d+)\s+岁以下的用户":
        ("SELECT * FROM users WHERE age < ?", [0]),

    r"统计用户数量":
        ("SELECT * FROM {0}", []),

    r"有多少用户":
        ("SELECT * FROM {0}", []),

    r"统计\s+(\w+)\s+的数量":
        ("SELECT * FROM {0}", []),

    r"有多少\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"显示\s+(\w+)\s+其中\s+(\w+)\s+大于\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} > ?", [2]),

    r"显示\s+(\w+)\s+其中\s+(\w+)\s+小于\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} < ?", [2]),

    r"显示\s+(\w+)\s+其中\s+(\w+)\s+等于\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} = ?", [2]),

    r"显示所有表":
        ("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_%'", []),

    r"列出所有表":
        ("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_%'", []),

    r"显示所有用户\s+按\s+(\w+)\s+排序":
        ("SELECT * FROM users ORDER BY {0}", []),

    r"显示前\s+(\d+)\s+个用户":
        ("SELECT * FROM users LIMIT ?", [0]),

    r"显示前\s+(\d+)\s+条用户":
        ("SELECT * FROM users LIMIT ?", [0]),
}
