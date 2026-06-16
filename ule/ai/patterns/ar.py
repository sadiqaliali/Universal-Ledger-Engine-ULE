"""Arabic language patterns for NLQ."""

# Order matters! More specific patterns must come before general patterns.
# Note: Arabic is RTL (Right-to-Left)
PATTERNS = {
    r"اعرض\s+جميع\s+المستخدمين":
        ("SELECT * FROM users", []),

    r"أظهر\s+جميع\s+المستخدمين":
        ("SELECT * FROM users", []),

    r"اعرض\s+المستخدمين\s+الذين\s+تزيد\s+أعمارهم\s+عن\s+(\d+)":
        ("SELECT * FROM users WHERE age > ?", [0]),

    r"أظهر\s+المستخدمين\s+الذين\s+تزيد\s+أعمارهم\s+عن\s+(\d+)\s+سنة":
        ("SELECT * FROM users WHERE age > ?", [0]),

    r"اعرض\s+المستخدمين\s+الأقل\s+من\s+(\d+)\s+سنة":
        ("SELECT * FROM users WHERE age < ?", [0]),

    r"اعرض\s+جميع\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"أظهر\s+جميع\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"عرض\s+جميع\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"كم\s+عدد\s+(\w+)":
        ("SELECT COUNT(*) FROM {0}", []),

    r"كم\s+(\w+)":
        ("SELECT COUNT(*) FROM {0}", []),

    r"عدد\s+(\w+)":
        ("SELECT COUNT(*) FROM {0}", []),

    r"اعرض\s+(\w+)\s+حيث\s+(\w+)\s+أكبر\s+من\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} > ?", [2]),

    r"اعرض\s+(\w+)\s+حيث\s+(\w+)\s+أقل\s+من\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} < ?", [2]),

    r"اعرض\s+(\w+)\s+حيث\s+(\w+)\s+يساوي\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} = ?", [2]),

    r"اعرض\s+الجداول":
        ("SELECT name FROM sqlite_master WHERE type='table'", []),

    r"أظهر\s+قائمة\s+الجداول":
        ("SELECT name FROM sqlite_master WHERE type='table'", []),

    r"اعرض\s+جميع\s+(\w+)\s+مرتبة\s+حسب\s+(\w+)":
        ("SELECT * FROM {0} ORDER BY {1}", []),

    r"اعرض\s+أول\s+(\d+)\s+(\w+)":
        ("SELECT * FROM {0} LIMIT ?", [1]),

    r"اعرض\s+أفضل\s+(\d+)\s+(\w+)":
        ("SELECT * FROM {0} LIMIT ?", [1]),
}
