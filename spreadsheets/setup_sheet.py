import gspread
import json
from google.oauth2.service_account import Credentials
def is_format_already_applied(sheet, sheet_id):
    metadata = sheet.spreadsheet.fetch_sheet_metadata()
    for s in metadata.get('sheets', []):
        if s.get('properties', {}).get('sheetId') == sheet_id:
            conditional_formats = s.get('conditionalFormats', [])
            for rule in conditional_formats:
                boolean_rule = rule.get('booleanRule', {})
                condition = boolean_rule.get('condition', {})
                if condition.get('type') == 'CUSTOM_FORMULA':
                    values = condition.get('values', [])
                    if values and values[0].get('userEnteredValue') == '=$K2=TRUE':
                        return True
    return False

def checkbox_setup(override:bool):
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_file("credentials.json", scopes=scopes)
    client = gspread.authorize(credentials)
    
    with open("./variables.json", "r") as var:
        data = json.load(var)
    spreadsheet_id = data["spreadsheet_id"] 
    sheet = client.open_by_key(spreadsheet_id).sheet1
    sheet_id = sheet.id

    if not override:
        if is_format_already_applied(sheet, sheet_id):
            print("[SKIP] Định dạng Checkbox và Quy tắc màu đã được áp dụng trước đó. Bỏ qua.")
            return

    print("Chưa có định dạng. Đang tải cấu hình từ rules_template.json...")
    try:
        with open("spreadsheets/rules_template.json", "r", encoding="utf-8") as f:
            requests = json.load(f)
    except FileNotFoundError:
        print("[LỖI] Không tìm thấy file rules_template.json.")
        return

    for req in requests:
        if "setDataValidation" in req:
            req["setDataValidation"]["range"]["sheetId"] = sheet_id
        elif "addConditionalFormatRule" in req:
            req["addConditionalFormatRule"]["rule"]["ranges"][0]["sheetId"] = sheet_id
        elif "repeatCell" in req:
            req["repeatCell"]["range"]["sheetId"] = sheet_id

    print("Đang áp dụng cài đặt lên Google Sheets...")
    sheet.spreadsheet.batch_update({"requests": requests})
    print("[SUCCESS] Đã cài đặt xong Checkbox và tính năng đổi màu tự động!")

if __name__ == "__main__":
    checkbox_setup(override=False)
