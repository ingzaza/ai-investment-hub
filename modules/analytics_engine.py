"""
modules/analytics_engine.py
---------------------------
คำนวณตัวชี้วัดทางการเงิน (Financial Health, Profitability) และประเมินมูลค่า (Valuation)
เน้น Margin of Safety สำหรับสาย Value Investing และ DCA
"""
import pandas as pd
import numpy as np

def calculate_graham_number(eps: float, bvps: float) -> float | None:
    """คำนวณราคาที่เหมาะสมตามสูตร Benjamin Graham (22.5 * EPS * BVPS)"""
    if eps is None or bvps is None or eps <= 0 or bvps <= 0:
        return None
    return np.sqrt(22.5 * eps * bvps)

def get_stock_summary(price_data: dict, fin_data: dict) -> dict:
    """ประมวลผลข้อมูลดิบให้ออกมาเป็นตัวเลขวิเคราะห์เชิงลึก"""
    summary = {
        "ok": False,
        "current_price": price_data.get("last_price"),
        "pe_ratio": None,
        "pb_ratio": None,
        "debt_to_equity": None,
        "gross_margin": None,
        "graham_number": None,
        "margin_of_safety": None,
        "valuation_zone": "N/A"
    }

    if not price_data.get("ok") or not fin_data.get("ok"):
        return summary

    try:
        bs = fin_data["balance_sheet"]
        inc = fin_data["income_statement"]
        
        # ป้องกันกรณีหุ้นบางตัวงบไม่ครบ
        total_debt = bs.loc["Total Debt"].iloc[0] if "Total Debt" in bs.index else 0
        total_equity = bs.loc["Stockholders Equity"].iloc[0] if "Stockholders Equity" in bs.index else 1
        shares_out = bs.loc["Ordinary Shares Number"].iloc[0] if "Ordinary Shares Number" in bs.index else None
        
        net_income = inc.loc["Net Income"].iloc[0] if "Net Income" in inc.index else 0
        gross_profit = inc.loc["Gross Profit"].iloc[0] if "Gross Profit" in inc.index else 0
        total_revenue = inc.loc["Total Revenue"].iloc[0] if "Total Revenue" in inc.index else 1

        # 1. Financial Health & Profitability
        summary["debt_to_equity"] = total_debt / total_equity if total_equity > 0 else None
        summary["gross_margin"] = (gross_profit / total_revenue) * 100 if total_revenue > 0 else None

        # 2. Valuation (EPS, BVPS)
        if shares_out and shares_out > 0:
            eps = net_income / shares_out
            bvps = total_equity / shares_out
            
            if summary["current_price"]:
                summary["pe_ratio"] = summary["current_price"] / eps if eps > 0 else None
                summary["pb_ratio"] = summary["current_price"] / bvps if bvps > 0 else None
                
            # Graham Number & Margin of Safety
            summary["graham_number"] = calculate_graham_number(eps, bvps)
            
            if summary["graham_number"] and summary["current_price"]:
                mos = ((summary["graham_number"] - summary["current_price"]) / summary["graham_number"]) * 100
                summary["margin_of_safety"] = mos
                
                if mos > 20:
                    summary["valuation_zone"] = "🟢 Undervalued (มี Margin of Safety)"
                elif mos > -10:
                    summary["valuation_zone"] = "🟡 Fair Value (ราคาเหมาะสม)"
                else:
                    summary["valuation_zone"] = "🔴 Overvalued (ราคาแพงกว่าพื้นฐาน)"

        summary["ok"] = True
    except Exception as e:
        summary["error"] = str(e)
        
    return summary
