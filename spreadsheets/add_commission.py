from utils import format_deadline
def upsert_entity(sheet, entity_id, entity_name, value_to_add, is_member=True):
    ids = sheet.col_values(1)
    str_id = str(entity_id)

    if str_id in ids:
        row_num = ids.index(str_id) + 1
        col_to_update = 3 if is_member else 2
        current_val = sheet.cell(row_num, col_to_update).value
        current_num = float(current_val.replace(',', '') if current_val else 0)
        sheet.update_cell(row_num, col_to_update, current_num + value_to_add)
    else:
        if is_member:
            sheet.append_row([str_id, entity_name, value_to_add])
        else:
            sheet.append_row([str_id, value_to_add]) # Customer lưu số project (1)
        row_num = len(ids) + 1
    return f'=HYPERLINK("#gid={sheet.id}&range=A{row_num}"; "{entity_name}")'

def add_new_commission(main_sheet, members_sheet, customers_sheet, name, link, customer_id, customer_name, deadline, total_price_str, surcharge_str, trans_id, trans_name, edit_id, edit_name, ratio):
    col_a_values = main_sheet.col_values(1)
    next_stt = len(col_a_values)
    next_row_index = len(col_a_values) + 1
    try:
        total_price = float(total_price_str.replace(",", ""))
        surcharge = float(surcharge_str.replace(",", "") or 0)
        base_commission = total_price - surcharge
        
        if base_commission < 0:
            return ["Lỗi: Phụ phí không được lớn hơn tổng giá tiền."]

        # 1. Tính toán tỷ lệ dựa trên base_commission
        parts = [float(p) for p in ratio.split("/")]
        sum_parts = sum(parts)
        
        # Translator nhận tiền dựa trên tỷ lệ của base_commission
        trans_money = (parts[0] / sum_parts) * base_commission
        
        # Editor nhận tiền dựa trên tỷ lệ của base_commission + TOÀN BỘ phụ phí
        edit_share_from_base = (parts[1] / sum_parts) * base_commission if len(parts) > 1 else 0
        edit_money = edit_share_from_base + surcharge

        # 2. Xử lý lưu trữ và lấy Link (Giữ nguyên hàm upsert_entity từ trước)
        trans_link = upsert_entity(members_sheet, trans_id, trans_name, trans_money, is_member=True)
        edit_link = upsert_entity(members_sheet, edit_id, edit_name, edit_money, is_member=True)
        cust_link = upsert_entity(customers_sheet, customer_id, customer_name, 1, is_member=False)

        new_row = [next_stt, cust_link, name, link, deadline, total_price, surcharge, trans_link, edit_link, ratio]
        
        range_to_update = f"A{next_row_index}:J{next_row_index}"
        main_sheet.update(values = [new_row], value_input_option='USER_ENTERED', range_name=range_to_update)

        return [trans_money, edit_money, surcharge]

    except Exception as e:
        return [f"Lỗi hệ thống: {e}"]
