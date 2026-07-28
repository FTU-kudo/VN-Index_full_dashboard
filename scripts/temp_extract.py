import pandas as pd
import json

def get_val(df, field, col):
    row = df[df['field_name'] == field]
    if row.empty: return 0
    val = row[col].values[0]
    return float(val) if pd.notna(val) else 0

def extract(ticker, f_out):
    f_out.write(f"\n================ {ticker} ================\n")
    df = pd.read_parquet(f'data/raw/financials/{ticker}.parquet')
    df_cstc = pd.read_parquet(f'data/raw/cstc/{ticker}.parquet')

    # Fields
    f_dtt = "Doanh thu thuần về bán hàng và cung cấp dịch vụ"
    f_gpm = "Lợi nhuận gộp về bán hàng và cung cấp dịch vụ"
    f_cogs = "Giá vốn hàng bán"
    f_banhang = "Chi phí bán hàng"
    f_qldn = "Chi phí quản lý doanh nghiệp"
    f_dttc = "Doanh thu hoạt động tài chính"
    f_cptc = "Chi phí tài chính"
    f_lntt = "Tổng lợi nhuận kế toán trước thuế"
    f_lnst = "Lợi nhuận sau thuế của cổ đông của Công ty mẹ"
    f_tsnh = "TÀI SẢN NGẮN HẠN"
    f_tien = "Tiền và các khoản tương đương tiền"
    f_dttcnh = "Đầu tư tài chính ngắn hạn"
    f_vayngan = "Vay và nợ thuê tài chính ngắn hạn"
    f_vaydai = "Vay và nợ thuê tài chính dài hạn"
    f_nongan = "Nợ ngắn hạn"
    f_vcsh = "Vốn chủ sở hữu"
    
    # 6T2026
    dtt_26q2 = get_val(df, f_dtt, '2026_Q2')
    dtt_26q1 = get_val(df, f_dtt, '2026_Q1')
    dtt_25q2 = get_val(df, f_dtt, '2025_Q2')
    dtt_25q1 = get_val(df, f_dtt, '2025_Q1')
    
    dtt_6t26 = (dtt_26q2 + dtt_26q1) / 1000  # tỷ
    dtt_6t25 = (dtt_25q2 + dtt_25q1) / 1000
    dtt_6t_yoy = (dtt_6t26 / dtt_6t25 - 1) * 100 if dtt_6t25 else 0

    lntt_26q2 = get_val(df, f_lntt, '2026_Q2')
    lntt_26q1 = get_val(df, f_lntt, '2026_Q1')
    lntt_25q2 = get_val(df, f_lntt, '2025_Q2')
    lntt_25q1 = get_val(df, f_lntt, '2025_Q1')
    
    lntt_6t26 = (lntt_26q2 + lntt_26q1) / 1000
    lntt_6t25 = (lntt_25q2 + lntt_25q1) / 1000
    lntt_6t_yoy = (lntt_6t26 / lntt_6t25 - 1) * 100 if lntt_6t25 else 0

    lnst_26q2 = get_val(df, f_lnst, '2026_Q2')
    lnst_26q1 = get_val(df, f_lnst, '2026_Q1')
    lnst_25q2 = get_val(df, f_lnst, '2025_Q2')
    lnst_25q1 = get_val(df, f_lnst, '2025_Q1')
    
    lnst_6t26 = (lnst_26q2 + lnst_26q1) / 1000
    lnst_6t25 = (lnst_25q2 + lnst_25q1) / 1000
    lnst_6t_yoy = (lnst_6t26 / lnst_6t25 - 1) * 100 if lnst_6t25 else 0

    f_out.write(f"[Luy ke 6T2026]\n")
    f_out.write(f"DTT: {dtt_6t26:.2f} ty ({dtt_6t_yoy:+.1f}% YoY)\n")
    f_out.write(f"LNTT: {lntt_6t26:.2f} ty ({lntt_6t_yoy:+.1f}% YoY)\n")
    f_out.write(f"LNST: {lnst_6t26:.2f} ty ({lnst_6t_yoy:+.1f}% YoY)\n")

    # Q2
    dtt_q2 = dtt_26q2 / 1000
    lnst_q2 = lnst_26q2 / 1000
    dtt_q2_yoy = (dtt_q2 / (dtt_25q2 / 1000) - 1) * 100 if dtt_25q2 else 0
    lnst_q2_yoy = (lnst_q2 / (lnst_25q2 / 1000) - 1) * 100 if lnst_25q2 else 0
    
    gpm_q2 = get_val(df, f_gpm, '2026_Q2') / dtt_26q2 * 100 if dtt_26q2 else 0
    gpm_q2_25 = get_val(df, f_gpm, '2025_Q2') / dtt_25q2 * 100 if dtt_25q2 else 0
    cogs_q2 = get_val(df, f_cogs, '2026_Q2') / dtt_26q2 * 100 if dtt_26q2 else 0
    
    bh = get_val(df, f_banhang, '2026_Q2') / dtt_26q2 * 100 if dtt_26q2 else 0
    qldn = get_val(df, f_qldn, '2026_Q2') / dtt_26q2 * 100 if dtt_26q2 else 0
    
    bh_25 = get_val(df, f_banhang, '2025_Q2') / dtt_25q2 * 100 if dtt_25q2 else 0
    qldn_25 = get_val(df, f_qldn, '2025_Q2') / dtt_25q2 * 100 if dtt_25q2 else 0
    
    net_fin = (get_val(df, f_dttc, '2026_Q2') - get_val(df, f_cptc, '2026_Q2')) / 1000
    
    f_out.write(f"\n[Q2/2026]\n")
    f_out.write(f"DTT: {dtt_q2:.2f} ty ({dtt_q2_yoy:+.2f}% YoY)\n")
    f_out.write(f"LNST cty me: {lnst_q2:.2f} ty ({lnst_q2_yoy:+.2f}% YoY)\n")
    f_out.write(f"GPM: {gpm_q2:.2f}% (Q2/25: {gpm_q2_25:.2f}%)\n")
    f_out.write(f"COGS/DTT: {cogs_q2:.2f}% (+ {cogs_q2 - (100 - gpm_q2_25):.1f} diem svck)\n")
    f_out.write(f"Chi phi BH/DTT: {bh:.2f}%\n")
    f_out.write(f"Chi phi QLDN/DTT: {qldn:.2f}%\n")
    f_out.write(f"Tong CP hd/DTT: {bh+qldn:.2f}% (+ {(bh+qldn) - (bh_25+qldn_25):.1f} diem svck)\n")
    f_out.write(f"Thu nhap TC rong: {net_fin:.2f} ty\n")
    
    lai_vay = get_val(df, "Chi phí lãi vay", '2026_Q2') / 1000
    f_out.write(f"Chi phi lai vay/DTT: {lai_vay/(dtt_q2+0.001)*100:.2f}%\n")
    
    vayngan = get_val(df, f_vayngan, '2026_Q2')
    vaydai = get_val(df, f_vaydai, '2026_Q2')
    vcsh = get_val(df, f_vcsh, '2026_Q2')
    nongan = get_val(df, f_nongan, '2026_Q2')
    tsnh = get_val(df, f_tsnh, '2026_Q2')
    tien = get_val(df, f_tien, '2026_Q2') + get_val(df, f_dttcnh, '2026_Q2')
    
    f_out.write(f"\n[Balance Sheet Q2/2026]\n")
    f_out.write(f"No vay: {(vayngan+vaydai)/1000:.2f} ty\n")
    f_out.write(f"No vay/VCSH: {(vayngan+vaydai)/vcsh*100 if vcsh else 0:.2f}%\n")
    f_out.write(f"Tien mat & DTNH: {tien/1000:.2f} ty (chiem {tien/tsnh*100 if tsnh else 0:.2f}% TSNH)\n")
    f_out.write(f"He so TT hien hanh: {tsnh/nongan if nongan else 0:.2f} lan\n")
    
    f_out.write(f"\n[CSTC]\n")
    pe = get_val(df_cstc, "P/E", "2026_Q2")
    pb = get_val(df_cstc, "P/B", "2026_Q2")
    roe = get_val(df_cstc, "ROE", "2026_Q2") * 100
    roa = get_val(df_cstc, "ROA", "2026_Q2") * 100
    
    f_out.write(f"PE TTM: {pe:.2f}x\n")
    f_out.write(f"PB: {pb:.2f}x\n")
    f_out.write(f"ROE TTM: {roe:.2f}%\n")
    f_out.write(f"ROA TTM: {roa:.2f}%\n")

with open('output_dtp.txt', 'w', encoding='utf-8') as f_out:
    extract('DTP', f_out)
    extract('DMC', f_out)
