"""Japanese language patterns for NLQ."""

PATTERNS = {
    r"すべての\s*(\w+)\s*を表示":
        ("SELECT * FROM {0}", []),

    r"(\w+)\s*を全部表示":
        ("SELECT * FROM {0}", []),

    r"(\d+)\s*歳以上の\s*(\w+)\s*を表示":
        ("SELECT * FROM {1} WHERE age > ?", [0]),

    r"(\d+)\s*歳未満の\s*(\w+)\s*を表示":
        ("SELECT * FROM {1} WHERE age < ?", [0]),

    r"(\w+)\s*の数を数える":
        ("SELECT * FROM {0}", []),

    r"(\w+)\s*は何個":
        ("SELECT * FROM {0}", []),

    r"(\w+)\s*を表示\s*(\w+)\s*が\s*(\d+)\s*より大きい":
        ("SELECT * FROM {0} WHERE {1} > ?", [2]),

    r"(\w+)\s*を表示\s*(\w+)\s*が\s*(\d+)\s*より小さい":
        ("SELECT * FROM {0} WHERE {1} < ?", [2]),

    r"(\w+)\s*を表示\s*(\w+)\s*が\s*(\d+)\s*と等しい":
        ("SELECT * FROM {0} WHERE {1} = ?", [2]),

    r"テーブルを表示":
        ("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_%'", []),

    r"すべてのテーブルを一覧":
        ("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '_%'", []),

    r"すべての\s*(\w+)\s*を\s*(\w+)\s*でソートして表示":
        ("SELECT * FROM {0} ORDER BY {1}", []),

    r"最初の\s*(\d+)\s*個の\s*(\w+)\s*を表示":
        ("SELECT * FROM {1} LIMIT ?", [0]),

    r"上位\s*(\d+)\s*件の\s*(\w+)\s*を表示":
        ("SELECT * FROM {1} LIMIT ?", [0]),
}
