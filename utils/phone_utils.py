# ---------------- PHONE NUMBER CLEAN ----------------


def clean_phone(phone):

    if not phone:
        return ""

    phone = str(phone).strip().replace(" ", "")

    if phone.startswith("+91"):
        phone = phone[3:]

    if phone.startswith("0"):
        phone = phone[1:]

    return phone
