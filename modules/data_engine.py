"""
modules/data_engine.py
------------------------
รับผิดชอบการดึงข้อมูลตลาดทุนทั้งหมดจาก yfinance (ใช้ history() แทน fast_info เพื่อความเสถียรบน Cloud)
"""

from __future__ import annotations

import pandas as pd
import requests
import streamlit as st
import yfinance as yf

from config import PRICE_CACHE_TTL, FINANCIALS_CACHE_TTL, FINANCIALS_LOOKBACK_YEARS

# สร้าง session พร้อมกำหนด User-Agent เพื่อป้องกันโดน Yahoo Finance บล็อก
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
})


# ============================================================================
# 1) Validation
# ============================================================================
@st.cache_data(ttl=PRICE_CACHE_TTL, show_spinner=False)
def validate_ticker(ticker: str) -> bool:
    """เช็คว่า ticker นี้มีข้อมูลจริงบน Yahoo Finance หรือไม่ โดยเช็คจาก history"""
    try:
        tk = yf.Ticker(ticker, session=session)
        df = tk.history(period="5d")
        return not df.empty
    except Exception:
        return False


# ============================================================================
# 2) ราคาเรียลไทม์ / ราคาย้อนหลัง
# ============================================================================
@st.cache_data(ttl=PRICE_CACHE_TTL, show_spinner=False)
def get_realtime_price(ticker: str) -> dict:
    """ดึงราคาล่าสุด + ข้อมูล snapshot จาก history (เสถียร ไม่พังง่าย)"""
    try:
        tk = yf.Ticker(ticker, session=session)
        hist = tk.history(period="5d")

        if hist.empty or len(hist) < 1:
            return {"ticker": ticker, "ok": False, "error": "ไม่พบข้อมูลราคาจาก Yahoo Finance"}

        last_price = float(hist["Close"].iloc[-1])
        prev_close = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else last_price
        change = last_price - prev_close
        change_pct = (change / prev_close) * 100 if prev_close else 0.0

        # ดึงข้อมูลเสริมจาก .info (ถ้าไม่ได้ ให้ข้ามไป)
        info = {}
        try:
            info = tk.info
        except Exception:
            pass

        return {
            "ticker": ticker,
            "ok": True,
            "last_price": last_price,
            "previous_close": prev_close,
            "change": change,
            "change_pct": change_pct,
            "currency": info.get("currency", ""),
            "day_high": float(hist["High"].iloc[-1]) if "High" in hist.columns else None,
            "day_low": float(hist["Low"].iloc[-1]) if "Low" in hist.columns else None,
            "year_high": info.get("fiftyTwoWeekHigh"),
            "year_low": info.get("fiftyTwoWeekLow"),
            "market_cap": info.get("marketCap"),
            "volume": int(hist["Volume"].iloc[-1]) if "Volume" in hist.columns else None,
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
