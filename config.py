"""
config.py
---------
ศูนย์รวมการตั้งค่า (settings) ของทั้งระบบ AI Investment Analyst Hub
แยกออกมาต่างหากเพื่อให้ Module อื่น ๆ (Data Engine, Analytics Engine, AI Co-Pilot)
เรียกใช้ค่าคงที่ร่วมกันได้ โดยไม่ต้อง hardcode กระจายอยู่หลายไฟล์
"""

import os

# ----------------------------------------------------------------------
# Path หลักของโปรเจกต์
# ----------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# ไฟล์เก็บ Watchlist แบบ Dynamic (Module 1)
WATCHLIST_FILE = os.path.join(DATA_DIR, "watchlist.json")

# ไฟล์เก็บ Portfolio ของผู้ใช้ (จะใช้งานจริงใน Phase ถัดไป)
PORTFOLIO_FILE = os.path.join(DATA_DIR, "portfolio.json")

# โฟลเดอร์ cache ข้อมูลงบการเงิน/ราคาย้อนหลัง เพื่อลดการยิง yfinance ซ้ำ ๆ
CACHE_DIR = os.path.join(DATA_DIR, "cache")

# ----------------------------------------------------------------------
# ค่า TTL (วินาที) สำหรับ st.cache_data — ใช้ควบคุมความสด (freshness) ของข้อมูล
# ----------------------------------------------------------------------
PRICE_CACHE_TTL = 60          # ราคาเรียลไทม์: cache 1 นาที
FINANCIALS_CACHE_TTL = 60 * 60 * 12   # งบการเงิน: cache 12 ชั่วโมง (งบไม่ได้เปลี่ยนบ่อย)

# ----------------------------------------------------------------------
# ค่าตั้งต้นของ Watchlist (กรณีไฟล์ยังไม่เคยถูกสร้าง)
# ----------------------------------------------------------------------
DEFAULT_WATCHLIST = ["NVDA", "TSM", "TISCO.BK"]

# จำนวนปีย้อนหลังของงบการเงินที่ต้องการ (ใช้จำกัดขอบเขตตอนแสดงผล
# เพราะ yfinance ฟรีมักให้ข้อมูลงบการเงินรายปีย้อนหลังสูงสุดจริง ๆ ประมาณ 4-5 ปี)
FINANCIALS_LOOKBACK_YEARS = 5

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
