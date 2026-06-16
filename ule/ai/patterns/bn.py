"""Bengali language patterns for NLQ."""

# Order matters! More specific patterns must come before general patterns.
PATTERNS = {
    r"সমস্ত\s+ব্যবহারকারী\s+দেখান\s+যাদের\s+বয়স\s+(\d+)\s+এর\s+চেয়ে\s+বেশি":
        ("SELECT * FROM users WHERE age > ?", [0]),

    r"(\d+)\s+বছরের\s+চেয়ে\s+বড়\s+ব্যবহারকারী\s+দেখান":
        ("SELECT * FROM users WHERE age > ?", [0]),

    r"(\d+)\s+বছরের\s+চেয়ে\s+ছোট\s+ব্যবহারকারী\s+দেখান":
        ("SELECT * FROM users WHERE age < ?", [0]),

    r"সমস্ত\s+ব্যবহারকারী\s+দেখান":
        ("SELECT * FROM users", []),

    r"সব\s+ব্যবহারকারী\s+দেখান":
        ("SELECT * FROM users", []),

    r"সমস্ত\s+(\w+)\s+দেখান":
        ("SELECT * FROM {0}", []),

    r"সব\s+(\w+)\s+দেখান":
        ("SELECT * FROM {0}", []),

    r"মোট\s+(\w+)\s+গণনা\s+করুন":
        ("SELECT * FROM {0}", []),

    r"কতটি\s+(\w+)\s+আছে":
        ("SELECT * FROM {0}", []),

    r"(\w+)\s+সংখ্যা\s+দেখান":
        ("SELECT * FROM {0}", []),

    r"(\w+)\s+দেখান\s+যেখানে\s+(\w+)\s+(\d+)\s+এর\s+চেয়ে\s+বড়":
        ("SELECT * FROM {0} WHERE {1} > ?", [2]),

    r"(\w+)\s+দেখান\s+যেখানে\s+(\w+)\s+(\d+)\s+এর\s+চেয়ে ছোট":
        ("SELECT * FROM {0} WHERE {1} < ?", [2]),

    r"(\w+)\s+দেখান\s+যেখানে\s+(\w+)\s+(\d+)\s+এর\s+সমান":
        ("SELECT * FROM {0} WHERE {1} = ?", [2]),

    r"টেবিল\s+দেখান":
        ("SELECT name FROM sqlite_master WHERE type='table'", []),

    r"সব\s+টেবিলের\s+তালিকা\s+দেখান":
        ("SELECT name FROM sqlite_master WHERE type='table'", []),

    r"সমস্ত\s+(\w+)\s+দেখান\s+(\w+)\s+অনুযায়ী\s+সাজানো":
        ("SELECT * FROM {0} ORDER BY {1}", []),

    r"প্রথম\s+(\d+)\s+টি\s+(\w+)\s+দেখান":
        ("SELECT * FROM {0} LIMIT ?", [1]),

    r"শীর্ষ\s+(\d+)\s+টি\s+(\w+)\s+দেখান":
        ("SELECT * FROM {0} LIMIT ?", [1]),
}
