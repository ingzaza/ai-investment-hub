"""
modules/data_engine.py
------------------------
รับผิดชอบการดึงข้อมูลตลาดทุนทั้งหมดจาก yfinance:
  1. ตรวจสอบว่า ticker มีอยู่จริง (validate_ticker)
  2. ราคาเรียลไทม์ + ข้อมูลราคาย้อนหลัง (get_realtime_price, get_price_history)
  3. งบการเงินย้อนหลัง 5 ปี: Income Statement + Balance Sheet (get_financials)

ทุกฟังก์ชันที่ยิง network ออกไปหา Yahoo Finance ถูกครอบด้วย @st.cache_data
เพื่อ (ก) ลดความหน่วงเวลาโหลดหน้าเว็บซ้ำ ๆ (ข) ลดความเสี่ยงโดน Yahoo rate-limit
TTL ถูกกำหนดจาก config.py แยกกันระหว่าง "ราคา" (สดบ่อย) กับ "งบการเงิน" (นิ่ง)
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
import yfinance as yf

from config import PRICE_CACHE_TTL, FINANCIALS_CACHE_TTL, FINANCIALS_LOOKBACK_YEARS


# ============================================================================
# 1) Validation
# ============================================================================
@st.cache_data(ttl=PRICE_CACHE_TTL, show_spinner=False)
def validate_ticker(ticker: str) -> bool:
    """
    เช็คว่า ticker นี้มีข้อมูลจริงบน Yahoo Finance หรือไม่
    ใช้ตอน Add ticker ใหม่ เพื่อกันผู้ใช้พิมพ์ผิด (เช่น "NVDAA")
    """
    try:
        info = yf.Ticker(ticker).fast_info
        # fast_info.last_price จะ raise หรือเป็น None ถ้า ticker ไม่มีอยู่จริง
        return info.get("last_price") is not None
    except Exception:
        return False


# ============================================================================
# 2) ราคาเรียลไทม์ / ราคาย้อนหลัง
# ============================================================================
@st.cache_data(ttl=PRICE_CACHE_TTL, show_spinner=False)
def get_realtime_price(ticker: str) -> dict:
    """
    ดึงราคาล่าสุด + ข้อมูล snapshot สั้น ๆ ของหุ้น 1 ตัว
    คืนค่าเป็น dict ที่พร้อมโชว์บน UI การ์ดสรุป

    หมายเหตุ: ใช้ fast_info เป็นหลักเพราะเร็วกว่า .info มาก (ไม่ scrape หน้าเว็บทั้งหน้า)
    """
    try:
        tk = yf.Ticker(ticker)
        fi = tk.fast_info

        last_price = fi.get("last_price")
        prev_close = fi.get("previous_close")
        change = None
        change_pct = None
        if last_price is not None and prev_close:
            change = last_price - prev_close
            change_pct = (change / prev_close) * 100

        return {
            "ticker": ticker,
            "ok": last_price is not None,
            "last_price": last_price,
            "previous_close": prev_close,
            "change": change,
            "change_pct": change_pct,
            "currency": fi.get("currency"),
            "day_high": fi.get("day_high"),
            "day_low": fi.get("day_low"),
            "year_high": fi.get("year_high"),
            "year_low": fi.get("year_low"),
            "market_cap": fi.get("market_cap"),
            "volume": fi.get("last_volume"),
        }
    except Exception as e:
        return {"ticker": ticker, "ok": False, "error": str(e)}


@st.cache_data(ttl=PRICE_CACHE_TTL, show_spinner=False)
def get_price_history(ticker: str, period: str = "5y", interval: str = "1d") -> pd.DataFrame:
    """
    ดึงราคาย้อนหลังแบบ time series (ใช้ต่อยอดใน Module 2: Growth / Max Drawdown / กราฟ)
    period ตัวอย่าง: "1mo", "3mo", "1y", "5y"
    """
    try:
        df = yf.Ticker(ticker).history(period=period, interval=interval)
        return df
    except Exception:
        return pd.DataFrame()


# ============================================================================
# 3) งบการเงินย้อนหลัง 5 ปี: Income Statement + Balance Sheet
# ============================================================================
@st.cache_data(ttl=FINANCIALS_CACHE_TTL, show_spinner=False)
def get_financials(ticker: str) -> dict:
    """
    ดึงงบการเงินรายปีย้อนหลัง (สูงสุดตามที่ yfinance ให้ฟรี ปกติ ~4 ปี)
    คืนค่า dict ที่มี 2 DataFrame หลัก: income_statement, balance_sheet
    คอลัมน์ = ปีงบการเงิน (วันที่ปิดงบ), แถว = รายการบัญชี

    หมายเหตุ: yfinance เวอร์ชันฟรีมักให้งบการเงินรายปีย้อนหลังจริงแค่ ~4 ปี
    (ไม่ครบ 5 ปีเป๊ะเสมอไป) จึงตัด (slice) เท่าที่มีจริง แล้วส่ง flag
    `years_available` กลับไปด้วย เพื่อให้ UI แจ้งผู้ใช้ตามจริงแทนที่จะ error
    """
    result = {
        "ticker": ticker,
        "ok": False,
        "income_statement": pd.DataFrame(),
        "balance_sheet": pd.DataFrame(),
        "years_available": 0,
        "error": None,
    }
    try:
        tk = yf.Ticker(ticker)

        income_stmt = tk.financials          # รายปี, คอลัมน์เรียงจากปีล่าสุด -> เก่าสุด
        balance_sheet = tk.balance_sheet

        if income_stmt is None:
            income_stmt = pd.DataFrame()
        if balance_sheet is None:
            balance_sheet = pd.DataFrame()

        # จำกัดจำนวนปีตาม config (กันกรณี yfinance คืนมาเกินความจำเป็น)
        income_stmt = income_stmt.iloc[:, :FINANCIALS_LOOKBACK_YEARS]
        balance_sheet = balance_sheet.iloc[:, :FINANCIALS_LOOKBACK_YEARS]

        result["income_statement"] = income_stmt
        result["balance_sheet"] = balance_sheet
        result["years_available"] = income_stmt.shape[1]
        result["ok"] = not income_stmt.empty or not balance_sheet.empty

        if not result["ok"]:
            result["error"] = "ไม่พบข้อมูลงบการเงินสำหรับ ticker นี้ (อาจเป็นหุ้นที่ yfinance ไม่รองรับงบเต็มรูปแบบ)"

    except Exception as e:
        result["error"] = str(e)

    return result


def clear_all_cache() -> None:
    """ล้าง cache ทั้งหมดของ data_engine (ใช้ตอนผู้ใช้กด 'Refresh ข้อมูล' บน UI)"""
    validate_ticker.clear()
    get_realtime_price.clear()
    get_price_history.clear()
    get_financials.clear()
