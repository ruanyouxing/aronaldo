from utils.format_deadline import format_deadline

def update_commission(sheet, stt, name=None, link=None, deadline=None, price=None, translator=None, editor=None, ratio=None, is_completed=None):
    col_a_values = sheet.col_values(1)
    stt_str = str(stt) 
    
    if stt_str not in col_a_values:
        print(f"[LỖI] Không tìm thấy Commission có Số thứ tự: {stt}")
        return
        
    # Tính toán vị trí dòng (+1 vì Google Sheets bắt đầu từ dòng 1, còn list Python bắt đầu từ 0)
    row_index = col_a_values.index(stt_str) + 1
    
    # 2. Lấy dữ liệu hiện tại của dòng đó
    current_row = sheet.row_values(row_index)
    
    # Đảm bảo danh sách có đủ 9 phần tử (Google Sheets đôi khi cắt bỏ các ô trống ở cuối)
    while len(current_row) < 9:
        current_row.append("")
        
    # 3. Cập nhật dữ liệu mới nếu có truyền tham số vào
    if name is not None: current_row[1] = name
    if link is not None: current_row[2] = link
    if deadline is not None: 
        current_row[3] = format_deadline(deadline)  # Gọi hàm chuẩn hóa ngày tháng
    if price is not None: current_row[4] = price
    if translator is not None: current_row[5] = translator
    if editor is not None: current_row[6] = editor
    if ratio is not None: current_row[7] = ratio
    if is_completed is not None: 
        current_row[8] = is_completed  # Cập nhật giá trị Checkbox (True/False)
    
    range_to_update = f"A{row_index}:I{row_index}"
    sheet.update(values=[current_row], range_name=range_to_update)
    
    print(f"[SUCCESS] Đã cập nhật thông tin cho Commission STT {stt} tại dòng {row_index}.")
