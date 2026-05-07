from datetime import datetime

def format_deadline(date_str):
    if not date_str:
        return ""

    formats_to_try = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%Y-%m-%d",
        "%d/%m/%y"
    ]

    date_str = str(date_str).strip()

    for fmt in formats_to_try:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            
            return parsed_date.strftime("%d/%m/%Y")
        except ValueError:
            continue

    print(f"[CẢNH BÁO] Không thể nhận diện định dạng ngày: {date_str}")
    return date_str
