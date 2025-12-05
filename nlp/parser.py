import re
import unicodedata
from datetime import datetime, timedelta
import dateparser

# ============ NORMALIZE ============

def normalize_text(s):
    s = s.lower().strip()

    s = re.sub(r'\bgiwof\b|\bgiwo\b|\bgio\b', 'giờ', s)

    s = re.sub(r'(\d+)\s*h\s*(\d+)', r'\1h\2', s)
    s = re.sub(r'(\d+)\s*h\b', r'\1h', s)

    return s


# ============ REGEX DEFINITIONS ============

TIME_REGEX = re.compile(r'(?P<h>\d{1,2})\s*(?:h|giờ|:)\s*(?P<m>\d{1,2})?', re.I)

MIN_REL = re.compile(r'(?P<n>\d+)\s*(phút|p|min)', re.I)
HOUR_REL = re.compile(r'(?P<n>\d+)\s*(giờ|h)\b', re.I)

REMINDER_REGEX = re.compile(r'nhắc[^0-9]*(?P<m>\d{1,3})\s*(p|phút|min)', re.I)

# ngày DD/MM hoặc DD-MM
DATE_REGEX = re.compile(r'(?:ngày)?\s*(?P<d>\d{1,2})[/-](?P<m>\d{1,2})', re.I)

# chỉ nhận phòng khi có số hoặc tên
ROOM_REGEX = re.compile(
    r"\b(?:phòng|p\.? )\s*([^,\.\n;]+)",
    re.IGNORECASE
)



# địa chỉ số + chữ
ADDRESS_REGEX = re.compile(
    r"(?:tại|ở|đến|qua|tới)\s+(?P<addr>\d+\s+[A-Za-zÀ-Ỵà-ỹ0-9\s\.]+)",
    re.IGNORECASE
)

TIME_STOPWORDS = r"(phòng|khoa|bệnh viện|trường|sở|công ty|chi nhánh|phòng ban|trung tâm)"


GENERIC_PLACE_REGEX = re.compile(
    r"(?:tại|ở|đến|tới)\s+"
    r"(?P<place>[A-Za-zÀ-Ỵà-ỹ0-9\s\.]+?)"
    r"(?=\s*" + TIME_STOPWORDS + r"|$)",
    re.IGNORECASE
)

PROVINCE_REGEX = re.compile(
    r"\b(?P<place>(bình thuận|đồng nai|vũng tàu|hà nội|hồ chí minh|quảng nam|đà nẵng|hải phòng|cần thơ|an giang|long an|bến tre|bình dương|bình phước|kiên giang|đắk lắk|daklak|lâm đồng|đà lạt))\b",
    re.IGNORECASE
)



# weekday map
WEEKDAY_MAP = {
    "thứ 2": 0, "thứ hai": 0,
    "thứ 3": 1, "thứ ba": 1,
    "thứ 4": 2, "thứ tư": 2,
    "thứ 5": 3, "thứ năm": 3,
    "thứ 6": 4, "thứ sáu": 4,
    "thứ 7": 5, "thứ bảy": 5,
    "chủ nhật": 6, "cn": 6,
}


# ============ WEEKDAY PARSER ============

def detect_weekday(text, now):
    # cuối tuần = thứ 7
    if "cuối tuần" in text:
        diff = (5 - now.weekday() + 7) % 7
        return now + timedelta(days=diff)

    # chủ nhật
    if "chủ nhật" in text or "cn" in text:
        diff = (6 - now.weekday() + 7) % 7
        return now + timedelta(days=diff)

    # thứ N
    for key, target in WEEKDAY_MAP.items():
        if key in text:

            diff = (target - now.weekday() + 7) % 7

            # thứ N tới / tuần sau
            if "tới" in text or "tuần sau" in text:
                if diff == 0:
                    diff = 7
                if diff < 2:
                    diff += 7

            return now + timedelta(days=diff)

    return None



# ============ RELATIVE TIME ============

def detect_relative_time(text, now):
    if "nữa" in text:

        m = MIN_REL.search(text)
        if m:
            return now + timedelta(minutes=int(m.group("n")))

        h = HOUR_REL.search(text)
        if h:
            return now + timedelta(hours=int(h.group("n")))

    return None


# ============ ABSOLUTE DATE (DD/MM) ============

def detect_absolute_date(text, now):
    """Bắt ngày tháng như 'ngày 12/12' và convert sang năm hiện tại"""
    m = DATE_REGEX.search(text)
    if m:
        day = int(m.group("d"))
        month = int(m.group("m"))
        try:
            # mặc định năm hiện tại
            dt = datetime(now.year, month, day)
            # nếu ngày này đã qua, dùng năm sau
            if dt < now:
                dt = datetime(now.year + 1, month, day)
            return dt
        except ValueError:
            # ngày không hợp lệ (vd: 2/30)
            pass
    return None


# ============ PART-OF-DAY ============

def detect_part_of_day(text):
    if "sáng" in text:
        return (9, 0)
    if "trưa" in text:
        return (12, 0)
    if "chiều" in text:
        return (15, 0)
    if "tối" in text:
        return (19, 0)
    return None


# ============ CLOCK ============

def extract_clock(text):
    m = TIME_REGEX.search(text)
    if not m:
        return None
    h = int(m.group("h"))
    m2 = int(m.group("m") or 0)
    return h, m2


# ============ LOCATION ============

def extract_location(text):
    s = text.lower()

    # 1) ROOM (phòng với số hoặc tên)
    m = ROOM_REGEX.search(s)
    if m:
        room = m.group(1).strip()
        if room:
            # Định dạng lại: "Phòng XXX"
            room_formatted = " ".join(w.capitalize() for w in room.split())
            return "Phòng " + room_formatted

    # 2) PROVINCE / CITY
    m = PROVINCE_REGEX.search(s)
    if m:
        return m.group("place").title()

    # 3) ADDRESS có số
    m2 = ADDRESS_REGEX.search(text)
    if m2:
        addr = m2.group("addr").strip()
        # cắt ngay trước từ khóa thời gian
        addr = re.split(r"\b(lúc|vào|sáng|chiều|tối|mai|nay|ngày)\b", addr, 1, flags=re.I)[0].strip()
        addr = " ".join(w.capitalize() for w in addr.split())
        return addr

    # 4) GENERIC PLACE
    m3 = GENERIC_PLACE_REGEX.search(text)
    if m3:
        loc = m3.group("place").strip()
        if len(loc.split()) >= 2:
            loc = " ".join(w.capitalize() for w in loc.split())
            return loc

    return None




# ============ EVENT NAME ============

def extract_event_name(original):
    # Tách theo keyword nhưng KHÔNG dùng re.split
    m = re.search(r"\b(lúc|vào|tại|ở)\b", original, flags=re.I)
    if m:
        name = original[:m.start()]
    else:
        name = original

    name = name.strip(" ,.")

    # bỏ từ vô nghĩa
    name = re.sub(r"^(nhắc tôi|hãy|ghi chú|đặt|tạo)\s*", "", name, flags=re.I)

    return name.strip()



# ============ MAIN PARSER ============

def parse_event(text, now=None):
    now = now or datetime.now()
    orig = text
    norm = normalize_text(text)

    # reminder
    m = REMINDER_REGEX.search(norm)
    reminder = int(m.group("m")) if m else 0

    # location
    location = extract_location(orig)

    # datetime
    dt = None

    # relative: X phút/giờ nữa
    dt = detect_relative_time(norm, now)

    # absolute date: ngày DD/MM
    if not dt:
        dt = detect_absolute_date(norm, now)

    # weekday
    if not dt:
        dt = detect_weekday(norm, now)
    
    # dateparser fallback
    if not dt:
        dt = dateparser.parse(
            orig,
            languages=["vi"],
            settings={"PREFER_DATES_FROM": "future", "RELATIVE_BASE": now}
        )

    if not dt:
        dt = now

    # giờ
    clock = extract_clock(norm)
    if clock:
        dt = dt.replace(hour=clock[0], minute=clock[1], second=0)
    else:
        pod = detect_part_of_day(norm)
        if pod:
            dt = dt.replace(hour=pod[0], minute=pod[1], second=0)

    # event
    event = extract_event_name(orig)

    return {
        "event": event,
        "start_time": dt.isoformat(),
        "end_time": None,
        "location": location or "",
        "reminder_minutes": reminder
    }


if __name__ == "__main__":
    # basic smoke test
    s = "Lên lịch phỏng vấn thực tập lúc 15h ngày 12/12 tại phòng nhân sự, nhắc trước 20 phút."
    print(parse_event(s))
