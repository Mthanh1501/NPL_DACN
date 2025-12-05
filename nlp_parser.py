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

# chỉ nhận phòng khi có số
# ROOM_REGEX = re.compile(r'\b(phòng|p\.?)\s*(?P<room>[a-zA-Z]?\d[\w\-]*)', re.I)
ROOM_REGEX = re.compile(
    r"\b(?:phòng|p\.?)\s+(?P<room>[A-Za-z]?\d{2,4})\b",
    re.IGNORECASE
)



# địa chỉ số + chữ
# ADDRESS_REGEX = re.compile(
#     r'(?:ở|tại|đến)\s+(?P<addr>\d+\s+[a-zA-ZÀ-Ỵà-ỹ0-9\s\-]+)',
#     re.I
# )

ADDRESS_REGEX = re.compile(
    r"(?:tại|ở|đến|qua|tới)\s+(?P<addr>\d+\s+[A-Za-zÀ-Ỵà-ỹ0-9\s\.]+)",
    re.IGNORECASE
)

TIME_STOPWORDS = r"(lúc|vào|trước|sau|sáng|trưa|chiều|tối|mai|nay|hôm nay|tuần|ngày|đêm)"


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


# ============ LOCATION (FIXED 100%) ============

# def extract_location(original):
#     # phòng — chỉ hợp lệ khi có số
#     m = ROOM_REGEX.search(original)
#     if m:
#         room = m.group("room").upper()
#         return f"Phòng {room}"

#     # địa chỉ
#     m2 = ADDRESS_REGEX.search(original)
#     if m2:
#         addr = m2.group("addr").strip()
#         addr = " ".join(w.capitalize() for w in addr.split())
#         return addr

#     return None

# def extract_location(text):
#     # Không bắt nếu không có từ khóa location
#     if not any(x in text.lower() for x in ["tại", "ở", "đến", "tới", "qua", "ghé"]):
#         return None

#     # Regex bắt cụm sau "tại / ở / đến / tới / qua / ghé"
#     m = re.search(r"(?:tại|ở|đến|tới|qua|ghé)\s+(.+)", text, re.IGNORECASE)
#     if not m:
#         return None

#     loc = m.group(1).strip()

#     # Cắt câu sau địa điểm nếu có từ khóa thời gian phía sau
#     loc = re.split(r"lúc|vào|khi|trước|sau|hôm|mai|nay|tuần", loc)[0].strip(" ,.")

#     # Định dạng chữ hoa đầu câu
#     loc = " ".join([w.capitalize() for w in loc.split()])

#     # Nếu cụm quá ngắn (vd: "cô", "anh", "em"), bỏ
#     if len(loc.split()) == 1 and len(loc) <= 2:
#         return None

#     return loc

def extract_location(text):
    s = text.lower()

    # 1) ROOM (loại phòng 1 chữ số)
    m = ROOM_REGEX.search(s)
    if m:
        num = m.group("room")
        if len(num) >= 2:
            return "Phòng " + num.upper()

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




# ============ EVENT NAME (FIX SPLIT BUG) ============

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

    # weekday
    if not dt:
        dt = detect_weekday(norm, now)
        weekday_fixed = True
    else:
        weekday_fixed = False

    # dateparser fallback
    if not dt:
        dt = dateparser.parse(
            norm,
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


# ============ TEST ============

if __name__ == "__main__":
    tests = [
    "Xem phim sáng chủ nhật",
    "Gặp cô Lan lúc 8h thứ 5 tuần này",
    "2 phút nữa học dự án, nhắc tôi trước 1p",
    "Học trí tuệ nhân tạo tại phòng A1 lúc 9h",
    "Lấy hồ sơ lúc 11 giờ trưa tại phòng A2",
    "Tập hát ở phòng 101 lúc 18h tối nay",
    "Đi khám bệnh lúc 9h ngày 12/12, nhắc trước 30 phút",
    "Họp nhóm 14h tại phòng B203",
    "Sáng mai họp lúc 10h tại phòng 302",
    "Gặp khách 8h30 hôm nay",
    "Họp trưa nay 12h ở phòng A5",
    "Đi ăn với bạn lúc 19h tối nay",
    "Chạy bộ 6h sáng mai",
    "Đi spa 16h tại 21 nguyen trai",
    "Mua trà sữa 3 phút nữa",
    "Nộp bài 2 giờ nữa, nhắc trước 10p",
    "Đi tập gym 1 giờ nữa",
    "Đi họp lớp vào lúc 10h ở phòng B203",
    "Làm báo cáo thứ 2 tới lúc 15h",
    "Trực lab 17h ngày mai ở tầng 5",
    "Đi công chứng giấy tờ lúc 9h sáng thứ 4",
    "Thi cuối tuần 9h",
    "Học nhóm cuối tuần ở phòng 101",
    "Tập thể dục cuối tuần 6h sáng",
    "Lấy thuốc ở bệnh viện Chợ Rẫy lúc 7h30 sáng mai",
    "Dạy kèm 19h tối thứ 6",
    "Ăn cưới lúc 11h ngày 25/12",
    "Họp đồ án tại phòng A12 vào lúc 14h",
    "Thuyết trình 13h chiều mai",
    "Đá banh 20h tối nay",
    "Dọn phòng 3 giờ nữa",
    "Đi siêu thị 2 giờ nữa",
    "Nộp báo cáo thứ 3 tới trước 23h",
    "Khám bệnh thứ 4 tuần sau lúc 9h",
    "Lịch bảo trì hệ thống tại 90 Nguyễn Du lúc 8h",
    "Tập hát 18h ở phòng 101 tối nay",
    "Gặp thầy ở phòng A6 lúc 15h",
    "Ôn thi 7h sáng ngày mai",
    "Check mail sau 15 phút nữa",
    "Đi xem phim lúc 21h tối thứ 7",
    "Làm bài kiểm tra lúc 8h sáng thứ hai",
    "Đi ăn cưới 10h ngày mai",
    "Họp công ty 9h sáng thứ 3 tuần này",
    "Tới 217 Hồng Bàng lúc 8h30 sáng mai",
    "Đi học võ 18h thứ 5",
    "Họp khoa tại phòng A201 lúc 13h",
    "Đi gặp sếp lúc 16h chiều nay",
    "Dạy thêm 7h sáng chủ nhật tới",
    "Đi nhận hàng tại 145 Lê Lợi lúc 10h",
    "9h sáng mai lên xe đi bình thuận",
    "25/12 thi tiếng anh tại Trường Đại Học Sài Gòn",
    ]

    for t in tests:
        print("INPUT:", t)
        print(parse_event(t))
        print("---------------------------")
