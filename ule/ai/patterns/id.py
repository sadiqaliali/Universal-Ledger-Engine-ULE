"""Indonesian language patterns for NLQ."""

# Order matters! More specific patterns must come before general patterns.
PATTERNS = {
    r"tampilkan\s+semua\s+pengguna":
        ("SELECT * FROM users", []),

    r"lihat\s+semua\s+pengguna":
        ("SELECT * FROM users", []),

    r"tampilkan\s+pengguna\s+yang\s+berusia\s+lebih\s+dari\s+(\d+)\s+tahun":
        ("SELECT * FROM users WHERE age > ?", [0]),

    r"tampilkan\s+pengguna\s+dengan\s+usia\s+di\s+atas\s+(\d+)":
        ("SELECT * FROM users WHERE age > ?", [0]),

    r"tampilkan\s+pengguna\s+dengan\s+usia\s+di\s+bawah\s+(\d+)":
        ("SELECT * FROM users WHERE age < ?", [0]),

    r"tampilkan\s+semua\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"lihat\s+semua\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"tampilkan\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"hitung\s+jumlah\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"berapa\s+banyak\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"jumlah\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"tampilkan\s+(\w+)\s+dimana\s+(\w+)\s+lebih\s+dari\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} > ?", [2]),

    r"tampilkan\s+(\w+)\s+dimana\s+(\w+)\s+kurang\s+dari\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} < ?", [2]),

    r"tampilkan\s+(\w+)\s+dimana\s+(\w+)\s+sama\s+dengan\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} = ?", [2]),

    r"tampilkan\s+tabel":
        ("SELECT name FROM sqlite_master WHERE type='table'", []),

    r"daftar\s+tabel":
        ("SELECT name FROM sqlite_master WHERE type='table'", []),

    r"tampilkan\s+semua\s+(\w+)\s+diurutkan\s+berdasarkan\s+(\w+)":
        ("SELECT * FROM {0} ORDER BY {1}", []),

    r"tampilkan\s+(\d+)\s+(\w+)\s+pertama":
        ("SELECT * FROM {0} LIMIT ?", [1]),

    r"tampilkan\s+top\s+(\d+)\s+(\w+)":
        ("SELECT * FROM {0} LIMIT ?", [1]),
}
