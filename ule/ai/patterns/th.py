"""Thai language patterns for NLQ."""

# Order matters! More specific patterns must come before general patterns.
# Note: Thai doesn't use spaces between words, so patterns use different separators
PATTERNS = {
    r"แสดงผู้ใช้ทั้งหมด":
        ("SELECT * FROM users", []),

    r"ดูผู้ใช้ทั้งหมด":
        ("SELECT * FROM users", []),

    r"แสดงผู้ใช้ที่อายุมากกว่า\s*(\d+)\s*ปี":
        ("SELECT * FROM users WHERE age > ?", [0]),

    r"แสดงผู้ใช้ที่อายุเกิน\s*(\d+)":
        ("SELECT * FROM users WHERE age > ?", [0]),

    r"แสดงผู้ใช้ที่อายุน้อยกว่า\s*(\d+)\s*ปี":
        ("SELECT * FROM users WHERE age < ?", [0]),

    r"แสดงทั้งหมด\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"ดูทั้งหมด\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"แสดง\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"นับจำนวน\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"มี\s+(\w+)\s+กี่คน":
        ("SELECT * FROM {0}", []),

    r"จำนวน\s+(\w+)":
        ("SELECT * FROM {0}", []),

    r"แสดง\s+(\w+)\s+ที่\s+(\w+)\s+มากกว่า\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} > ?", [2]),

    r"แสดง\s+(\w+)\s+ที่\s+(\w+)\s+น้อยกว่า\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} < ?", [2]),

    r"แสดง\s+(\w+)\s+ที่\s+(\w+)\s+เท่ากับ\s+(\d+)":
        ("SELECT * FROM {0} WHERE {1} = ?", [2]),

    r"แสดงตาราง":
        ("SELECT name FROM sqlite_master WHERE type='table'", []),

    r"รายการตาราง":
        ("SELECT name FROM sqlite_master WHERE type='table'", []),

    r"แสดงทั้งหมด\s+(\w+)\s+เรียงตาม\s+(\w+)":
        ("SELECT * FROM {0} ORDER BY {1}", []),

    r"แสดง\s+(\d+)\s+(\w+)\s+แรก":
        ("SELECT * FROM {0} LIMIT ?", [1]),

    r"แสดง\s+top\s+(\d+)\s+(\w+)":
        ("SELECT * FROM {0} LIMIT ?", [1]),
}
