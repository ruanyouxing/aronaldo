import gspread
import json
from functools import partial
from google.oauth2.service_account import Credentials
from gspread.exceptions import WorksheetNotFound

from .add_commission import add_new_commission
# from .edit_commission import update_commission

with open("./variables.json", "r") as var:
    data = json.load(var)

scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_file("credentials.json", scopes=scopes)
client = gspread.authorize(credentials)

spreadsheet = client.open_by_key(data["spreadsheet_id"])
main_sheet = spreadsheet.worksheet("Commission")
try:
    members_sheet = spreadsheet.worksheet("Members")
except WorksheetNotFound:
    members_sheet = spreadsheet.add_worksheet(title="Members", rows=100, cols=3)
    members_sheet.append_row(["ID", "Tên", "Tổng thu nhập"])

try:
    customers_sheet = spreadsheet.worksheet("Customers")
except WorksheetNotFound:
    customers_sheet = spreadsheet.add_worksheet(title="Customers", rows=100, cols=2)
    customers_sheet.append_row(["ID/Name", "Tổng project đã nhận"])

headers = main_sheet.row_values(1)
if not headers or len(headers) < 2 or headers[1] != "Khách hàng":
    main_sheet.insert_cols([["Khách hàng"]], 2)
    print("Đã tự động chèn cột Customer vào Spreadsheet!")
if len(headers) > 5 and headers[6] != "Phụ phí Editor":
    main_sheet.insert_cols([["Phụ phí Editor"]], 7)
    print("Đã tự động chèn cột Phụ phí Editor!")

print("Đã kết nối và thiết lập cấu trúc Google Spreadsheet thành công!\n")

upload_to_spreadsheet = partial(add_new_commission, main_sheet, members_sheet, customers_sheet)
