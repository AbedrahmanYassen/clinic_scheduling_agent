import re
import dateparser
from datetime import datetime, timedelta

# ─── Weekday Maps ─────────────────────────────────────────────────────────────

WEEKDAYS_AR_MAP = {
    'الأحد':    6,
    'الاثنين':  0,
    'الثلاثاء': 1,
    'الأربعاء': 2,
    'الخميس':   3,
    'الجمعة':   4,
    'السبت':    5,
}

WEEKDAYS_AR  = r'الأحد|الاثنين|الثلاثاء|الأربعاء|الخميس|الجمعة|السبت'
NEXT_SUFFIX  = r'الجاي[ةى]?|الجاى[ة]?|القادم[ة]?'

# ─── Dialect / Relative-date rules ────────────────────────────────────────────

DIALECT_MAP = [
    (r'بعد بكرة|بعد بكره',             lambda _: datetime.now() + timedelta(days=2)),
    (r'بكرة|بكره',                      lambda _: datetime.now() + timedelta(days=1)),
    (r'الأسبوع الجاي|الأسبوع الجاى',   lambda _: datetime.now() + timedelta(weeks=1)),
    (r'الشهر الجاي|الشهر الجاى',
        lambda _: (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1)),
    (r'نهاية الأسبوع|نهاية الاسبوع|آخر الأسبوع|آخر الاسبوع',
        lambda _: _next_weekday(3)),   

    (r'بداية الأسبوع|بداية الاسبوع|أول الأسبوع|أول الاسبوع',
        lambda _: _next_weekday(5)),   

    (r'منتصف الأسبوع|منتصف الاسبوع|نص الأسبوع|نص الاسبوع',
        lambda _: _next_weekday(2)),   

    (r'نهاية الشهر|آخر الشهر',
        lambda _: (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)),

    (r'أول الشهر|بداية الشهر',
        lambda _: (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1)),
]

WORD_TO_NUM = {
    'يوم': 1, 'يومين': 2, 'ثلاثة': 3, 'أربعة': 4,
    'خمسة': 5, 'ستة': 6, 'سبعة': 7,
}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _next_weekday(weekday_num: int) -> datetime:
    """Return the date of the next occurrence of a weekday (never today)."""
    today = datetime.now()
    days_ahead = (weekday_num - today.weekday() + 7) % 7
    days_ahead = days_ahead if days_ahead != 0 else 7
    return today + timedelta(days=days_ahead)


def _resolve_weekday(text: str) -> datetime | None:
    """
    Detect an Arabic weekday name (optionally preceded by a preposition prefix
    like لـ/يوم/في and optionally followed by a next suffix) and return the
    corresponding datetime, or None if no weekday is found.
    """
    # Optional preposition prefixes: لـ، يوم، ليوم، في
    PREFIX = r'(?:(?:لل|لـ?|يوم\s+|ليوم\s+|في\s+|بـ?))?'

    # weekday + next suffix  →  always next occurrence
    match = re.search(rf'{PREFIX}({WEEKDAYS_AR})\s+({NEXT_SUFFIX})', text)
    if match:
        return _next_weekday(WEEKDAYS_AR_MAP[match.group(1)])

    match = re.search(rf'{PREFIX}({WEEKDAYS_AR})', text)
    if match:
        result = dateparser.parse(
            match.group(1),
            languages=['ar'],
            settings={'PREFER_DATES_FROM': 'future'},
        )
        return result  

    return None


def _resolve_dialect(text: str) -> datetime | None:
    """
    Handle dialect / relative expressions that dateparser doesn't know.
    Returns a datetime or None.
    """
    # "بعد N أيام"
    m = re.search(r'بعد (\w+) أيام', text)
    if m:
        n = WORD_TO_NUM.get(m.group(1))
        if n:
            return datetime.now() + timedelta(days=n)

    # Fixed dialect patterns
    for pattern, resolver in DIALECT_MAP:
        if re.search(pattern, text):
            return resolver(None)

    return None



def parse_arabic_date(text: str) -> datetime | None:
    """
    Parse an Arabic date/time expression and return a datetime (or None).

    Priority order
    ──────────────
    1. Dialect / relative expressions  (بكرة، بعد بكرة، الأسبوع الجاي …)
    2. Arabic weekday names             (الخميس القادم، الجمعة الجاية، السبت …)
    3. dateparser fallback              (handles absolute dates, times, etc.)
    """
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)        # collapse non-breaking / extra spaces
    text = text.replace('\u0649', '\u064a') # ى → ي  (unify alef maqsura)
    text = re.sub(r'لل(\w)', r'ال\1', text) # للخميس → الخميس (Arabic def. article after لـ)

    result = _resolve_dialect(text)
    if result:
        return result

    result = _resolve_weekday(text)
    if result:
        return result

    # Strip "next" suffixes so dateparser doesn't misread them
    normalized = re.sub(
        rf'({WEEKDAYS_AR})\s+({NEXT_SUFFIX})',
        r'\1',
        text,
    )
    return dateparser.parse(
        normalized,
        languages=['ar'],
        settings={'PREFER_DATES_FROM': 'future'},
    )


# ─── Tests ────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    tests = [
        # weekday + next suffix (ي / ى / ة variants)
        'الخميس القادم الساعة 10',
    'موعد يوم الجمعة الجاية',
    'الأحد القادمة الساعة 3',
    'عندي موعد الاثنين الجاي الساعة 2 المسا',
    'السبت الجاي',
    'الأربعاء القادمة الساعة 6 المسا',
    'الثلاثاء الجاى الساعة 9 الصبح',

    # prepositional prefixes (لل / يوم / في / ليوم)
    'أريد تغيير موعدي للخميس الجاي الساعة 11 صباحا',
    'للجمعة الجاية الساعة 2',
    'يوم الاثنين الجاي الساعة 4',
    'في الأحد القادم الساعة 10 الصبح',
    'ليوم الأربعاء القادم',
    'ودي أحجز ليوم الأربعاء القادمة إن شاء الله الساعة 9 الصبح',

    # bare weekday
    'السبت',
    'يوم الجمعة',
    'عندي موعد الثلاثاء',

    # dialect / relative
    'أبي موعد بكرة',
    'بكره الساعة 10',
    'بعد بكرة الساعة 4',
    'بعد بكره',

    # بعد N أيام
    'بعد يومين',
    'بعد ثلاثة أيام',
    'بعد خمسة أيام',
    'بعد سبعة أيام',

    # week / month relative
    'الأسبوع الجاي',
    'الأسبوع الجاى',
    'الشهر الجاي',
    'الشهر الجاى',

    # whitespace edge cases
    'الخميس  الجاي الساعة 11 صباحا',       # double space
    'الخميس\u00a0الجاي الساعة 11 صباحا',   # non-breaking space

    # long real-world sentences
    'أريد حجز موعد ليوم الخميس الجاي الساعة 11 صباحا',
    'ممكن تغير موعدي للسبت الجاي الساعة 3 العصر',
    'أبغى موعد بكرة الساعة 9 الصبح إن أمكن',
    'عندي موعد بعد ثلاثة أيام الساعة 2 الظهر',
    ]
    print(f"Today: {datetime.now().strftime('%A %Y-%m-%d')}\n")

    for text in tests:
        dt = parse_arabic_date(text)
        date_str = dt.strftime('%Y-%m-%d') if dt else None
        print(f"  Input : {text}")
        print(f"  Result: {date_str}")
        print()