"""Turkish language patterns for NLQ."""

# Order matters! More specific patterns must come before general patterns.
PATTERNS = {
    r"tüm\s+kullanıcıları\s+göster":
        ("SELECT * FROM users", []),

    r"bütün\s+kullanıcıları\s+göster":
        ("SELECT * FROM users", []),

    r"yaşı\s+(\d+)\s+dan\s+büyük\s+kullanıcıları\s+göster":
        ("SELECT * FROM users WHERE age > ?", [0]),

    r"(\d+)\s+yaşından\s+büyük\s+kullanıcıları\s+göster":
        ("SELECT * FROM users WHERE age > ?", [0]),

    r"(\d+)\s+yaşından\s+küçük\s+kullanıcıları\s+göster":
        ("SELECT * FROM users WHERE age < ?", [0]),

    r"tüm\s+(\w+)\s+göster":
        ("SELECT * FROM {0}", []),

    r"bütün\s+(\w+)\s+göster":
        ("SELECT * FROM {0}", []),

    r"tüm\s+(\w+)\s+listele":
        ("SELECT * FROM {0}", []),

    r"toplam\s+(\w+)\s+sayısını\s+göster":
        ("SELECT * FROM {0}", []),

    r"kaç\s+tane\s+(\w+)\+var":
        ("SELECT * FROM {0}", []),

    r"(\w+)\s+sayısı":
        ("SELECT * FROM {0}", []),

    r"(\w+)\s+göster\s+nerede\s+(\w+)\s+(\d+)\s+dan\s+büyük":
        ("SELECT * FROM {0} WHERE {1} > ?", [2]),

    r"(\w+)\s+göster\s+nerede\s+(\w+)\s+(\d+)\s+den\s+küçük":
        ("SELECT * FROM {0} WHERE {1} < ?", [2]),

    r"(\w+)\s+göster\s+nerede\s+(\w+)\s+(\d+)\s+e\s+eşit":
        ("SELECT * FROM {0} WHERE {1} = ?", [2]),

    r"tabloları\s+göster":
        ("SELECT name FROM sqlite_master WHERE type='table'", []),

    r"tüm\s+tabloları\s+listele":
        ("SELECT name FROM sqlite_master WHERE type='table'", []),

    r"tüm\s+(\w+)\s+göster\s+(\w+)\s+göre\s+sıralı":
        ("SELECT * FROM {0} ORDER BY {1}", []),

    r"ilk\s+(\d+)\s+(\w+)\s+göster":
        ("SELECT * FROM {0} LIMIT ?", [1]),

    r"en\s+üst\s+(\d+)\s+(\w+)\s+göster":
        ("SELECT * FROM {0} LIMIT ?", [1]),
}
