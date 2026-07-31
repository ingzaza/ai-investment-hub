"""
modules/scenario_engine.py
--------------------------
ทดสอบความทนทาน (Stress Test) และจำลองการลงทุนแบบถัวเฉลี่ย (DCA Simulation)
"""
import pandas as pd
import numpy as np

def calculate_max_drawdown(history_df: pd.DataFrame) -> float:
    """คำนวณการร่วงลงที่หนักที่สุดจากจุดสูงสุด (Max Drawdown)"""
    if history_df is None or history_df.empty or "Close" not in history_df.columns:
        return 0.0
    
    roll_max = history_df["Close"].cummax()
    drawdown = history_df["Close"] / roll_max - 1.0
    max_drawdown = drawdown.min() * 100
    return round(max_drawdown, 2)

def simulate_dca(monthly_investment: float, years: int, annual_return_pct: float) -> pd.DataFrame:
    """จำลองพอร์ต DCA ตามระยะเวลาและผลตอบแทนคาดหวัง"""
    months = years * 12
    monthly_rate = (annual_return_pct / 100) / 12
    
    data = []
    total_invested = 0
    portfolio_value = 0
    
    for month in range(1, months + 1):
        total_invested += monthly_investment
        portfolio_value = (portfolio_value + monthly_investment) * (1 + monthly_rate)
        
        if month % 12 == 0:  # เก็บข้อมูลรายปีเพื่อเอาไปพล็อตกราฟ
            data.append({
                "Year": f"Year {month//12}",
                "Total Invested (Capital)": round(total_invested, 2),
                "Portfolio Value": round(portfolio_value, 2)
            })
            
    return pd.DataFrame(data).set_index("Year")
