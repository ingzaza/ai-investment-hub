"""
modules/data_engine.py
------------------------
รับผิดชอบการดึงข้อมูลตลาดทุนทั้งหมดจาก yfinance:
  1. ตรวจสอบว่า ticker มีอยู่จริง (validate_ticker)
  2. ราคาเรียลไทม์ + ข้อมูลราคาย้อนหลัง (get_realtime_price, get_price_history)
  3. งบการเงินย้อนหลัง 5 ปี: Income Statement + Balance Sheet (get_financials)
"""

from __future__ import annotations

import pandas as pd
import requests
import streamlit as st
import yfinance as yf

from config import PRICE_CACHE_TTL, FINANCIALS_CACHE_TTL, FINANCIALS_LOOKBACK_YEARS

# สร้าง session พร้อมกำหนด User-Agent เพื่อป้องกันโดน Yahoo Finance บล็อกบน Streamlit Cloud
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
})


# ============================================================================
# 1) Validation
# ============================================================================
@st.cache_data(ttl=PRICE_CACHE_TTL, show_spinner=False)
def validate_ticker(ticker: str) -> bool:
    """เช็คว่า ticker นี้มีข้อมูลจริงบน Yahoo Finance หรือไม่"""
    try:
        tk = yf.Ticker(ticker, session=session)
        fi = tk.fast_info
        return fi.get("last_price") is not None
    except Exception:
        return False


# ============================================================================
# 2) ราคาเรียลไทม์ / ราคาย้อนหลัง
# ============================================================================
@st.cache_data(ttl=PRICE_CACHE_TTL, show_spinner=False)
def get_realtime_price(ticker: str) -> dict:
    """ดึงราคาล่าสุด + ข้อมูล snapshot สั้น ๆ ของหุ้น 1 ตัว"""
    try:
        tk = yf.Ticker(ticker, session=session)
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
    """ดึงราคาย้อนหลังแบบ time series"""
    try:
        df = yf.Ticker(ticker, session=session).history(period=period, interval=interval)
        return df
    except Exception:
        return pd.DataFrame()


# ============================================================================
# 3) งบการเงินย้อนหลัง 5 ปี
# ============================================================================
@st.cache_data(ttl=FINANCIALS_CACHE_TTL, show_spinner=False)
def get_financials(ticker: str) -> dict:
    """ดึงงบการเงินรายปีย้อนหลัง"""
    result = {
        "ticker": ticker,
        "ok": False,
        "income_statement": pd.DataFrame(),
        "balance_sheet": pd.DataFrame(),
        "years_available": 0,
        "error": None,
    }
    try:
        tk = yf.Ticker(ticker, session=session)

        income_stmt = tk.financials
        balance_sheet = tk.balance_sheet

        if income_stmt is None:
            income_stmt = pd.DataFrame()
        if balance_sheet is None:
            balance_sheet = pd.DataFrame()

        income_stmt = income_stmt.iloc[:, :FINANCIALS_LOOKBACK_YEARS]
        balance_sheet = balance_sheet.iloc[:, :FINANCIALS_LOOKBACK_YEARS]

        result["income_statement"] = income_stmt
        result["balance_sheet"] = balance_sheet
        result["years_available"] = income_stmt.shape[1]
        result["ok"] = not income_stmt.empty or not balance_sheet.empty

        if not result["ok"]:
            result["error"] = "ไม่พบข้อมูลงบการเงินสำหรับ ticker นี้"

    except Exception as e:
        result["error"] = str(e)

    return result


def clear_all_cache() -> None:
    """ล้าง cache ทั้งหมดของ data_engine"""
    validate_ticker.clear()
    get_realtime_price.clear()
    get_price_history.clear()
    get_financials.clear()
