"""
modules/watchlist_manager.py
-----------------------------
รับผิดชอบการจัดการ "Watchlist แบบ Dynamic" ของผู้ใช้
- โหลด/บันทึก watchlist ลงไฟล์ JSON (เบื้องต้น — สลับไป SQLite ได้ในภายหลัง
  โดยไม่ต้องแก้ไฟล์อื่นที่เรียกใช้ฟังก์ชันชุดนี้)
- ทำ Normalize ticker (ตัดช่องว่าง, ทำเป็นตัวพิมพ์ใหญ่) เพื่อกัน bug จากผู้ใช้พิมพ์ผิดรูปแบบ
- ตรวจสอบว่า ticker มีอยู่จริงก่อน add (เรียกผ่าน data_engine)

หมายเหตุสถาปัตยกรรม:
เราตั้งใจแยก "การจัดการรายการ watchlist" (ไฟล์นี้) ออกจาก
"การดึงข้อมูลราคา/งบการเงินจาก yfinance" (data_engine.py)
เพื่อให้ทั้งสองส่วนทดสอบและแก้ไขแยกจากกันได้ (Single Responsibility)
"""

import json
import os
from datetime import datetime, timezone

from config import WATCHLIST_FILE, DEFAULT_WATCHLIST


def _ensure_file_exists() -> None:
    """สร้างไฟล์ watchlist.json ตั้งต้น หากยังไม่มีไฟล์อยู่จริง"""
    if not os.path.exists(WATCHLIST_FILE):
        _save_raw({"tickers": DEFAULT_WATCHLIST.copy(), "last_updated": None})


def _load_raw() -> dict:
    """อ่านไฟล์ watchlist.json แบบ raw dict"""
    _ensure_file_exists()
    try:
        with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        # ไฟล์เสีย/หาย -> reset กลับเป็นค่าตั้งต้น กันแอปพังทั้งระบบ
        fallback = {"tickers": DEFAULT_WATCHLIST.copy(), "last_updated": None}
        _save_raw(fallback)
        return fallback


def _save_raw(data: dict) -> None:
    """เขียนไฟล์ watchlist.json"""
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    os.makedirs(os.path.dirname(WATCHLIST_FILE), exist_ok=True)
    with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_ticker(raw_ticker: str) -> str:
    """
    ทำความสะอาด ticker ที่ผู้ใช้พิมพ์เข้ามา
    เช่น "  tsm " -> "TSM", "tisco.bk" -> "TISCO.BK"
    """
    return raw_ticker.strip().upper()


def get_watchlist() -> list[str]:
    """คืนค่ารายชื่อ ticker ทั้งหมดใน watchlist ปัจจุบัน"""
    data = _load_raw()
    return data.get("tickers", [])


def add_ticker(raw_ticker: str) -> tuple[bool, str]:
    """
    เพิ่ม ticker เข้า watchlist

    Returns:
        (success: bool, message: str) — message ใช้แสดงผลใน UI (st.success/st.error)
    """
    ticker = normalize_ticker(raw_ticker)
    if not ticker:
        return False, "กรุณาพิมพ์ชื่อหุ้น (Ticker) ก่อนเพิ่ม"

    data = _load_raw()
    tickers = data.get("tickers", [])

    if ticker in tickers:
        return False, f"'{ticker}' อยู่ใน Watchlist อยู่แล้ว"

    tickers.append(ticker)
    data["tickers"] = tickers
    _save_raw(data)
    return True, f"เพิ่ม '{ticker}' เข้า Watchlist สำเร็จ"


def remove_ticker(raw_ticker: str) -> tuple[bool, str]:
    """ลบ ticker ออกจาก watchlist"""
    ticker = normalize_ticker(raw_ticker)
    data = _load_raw()
    tickers = data.get("tickers", [])

    if ticker not in tickers:
        return False, f"ไม่พบ '{ticker}' ใน Watchlist"

    tickers.remove(ticker)
    data["tickers"] = tickers
    _save_raw(data)
    return True, f"ลบ '{ticker}' ออกจาก Watchlist แล้ว"
