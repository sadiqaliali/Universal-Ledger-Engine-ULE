"""Vietnamese language patterns for NLQ."""

# Order matters! More specific patterns must come before general patterns.
PATTERNS = {
    r"hiển\s+thị\s+tất\s+cả\s+người\s+dùng":
        ("SELECT * FROM users", []),

    r"xem\s+tất\s+cả\s+người\s+dùng":
        ("SELECT * FROM users", []),

    r"hiển\s+thị\s+người\s+dùng\s+trên\s+(\d+)\s+tuổi":
        ("SELECT * FROM users WHERE age > ?", [0]),

    r"hiển\s+thị\s+người\s+dùng\s+trên\s+(\d+)\s+tuổi\s+trở\s+lên":
        ("SELECT * FROM users WHERE age > ?", [0]),

    r"hiển\s+thị\s+người\s+dùng\s+dưới\s+(\d+)\s+tuổi":
        ("SELECT * FROM users WHERE age < ?", [0]),

    r"hiển\s+thị\s+tất\s+cả\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"xem\s+tất\s+cả\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"hiển\s+thị\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"đếm\s+số\s+lượng\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"có\s+bao\s+nhiêu\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"số\s+lượng\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"hiển\s+thị\s+(\w+)\s+nơi\s+(\w+)\s+lớn\s+hơn\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} > ?", [2]),

    r"hiển\s+thị\s+(\w+)\s+nơi\s+(\w+)\s+nhỏ\s+hơn\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} < ?", [2]),

    r"hiển\s+thị\s+(\w+)\s+nơi\s+(\w+)\s+bằng\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} = ?", [2]),

    r"hiển\s+thị\s+bảng":
        ("SELECT name FROM sqlite_master WHERE type='table'", []),

    r"danh\s+sách\s+bảng":
        ("SELECT name FROM sqlite_master WHERE type='table'", []),

    r"hiển\s+thị\s+tất\s+cả\s+(\w+)\s+sắp\s+xếp\s+theo\s+(\w+)":
        ("SELECT * FROM {0} ORDER BY {1}", []),

    r"hiển\s+thị\s+(\d+)\s+(\w+)\s+đầu\s+tiên":
        ("SELECT * FROM {0} LIMIT ?", [1]),

    r"hiển\s+thị\s+top\s+(\d+)\s+(\w+)":
        ("SELECT * FROM {0} LIMIT ?", [1]),
}
