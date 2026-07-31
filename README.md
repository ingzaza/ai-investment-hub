# AI Investment Analyst Hub — Phase 1

ระบบผู้ช่วยนักลงทุนระยะยาว (DCA & Value Investing) เน้น Capital Protection และ Margin of Safety
**Phase 1 นี้ครอบคลุม Module 1: Data & Watchlist Engine** พร้อม UI พื้นฐานของ Streamlit

## 📁 โครงสร้างไฟล์ (Directory Structure)

```
ai_investment_hub/
├── app.py                      # Entry point — หน้า UI หลักของ Streamlit
├── config.py                   # ค่า setting กลาง (path, cache TTL, ค่าตั้งต้น)
├── requirements.txt            # Dependencies ทั้งหมด (รวมของ Phase หลังไว้ล่วงหน้า)
├── .env.example                # ตัวอย่างไฟล์ env (ใช้จริงตอน Phase 4 - AI Co-Pilot)
├── .gitignore
│
├── modules/                    # โค้ด Logic หลัก แยกตามความรับผิดชอบ (Single Responsibility)
│   ├── __init__.py
│   ├── watchlist_manager.py    # Module 1a: CRUD ของ Watchlist (Add/Remove/Persist)
│   └── data_engine.py          # Module 1b: ดึงราคาเรียลไทม์ + งบการเงิน 5 ปีจาก yfinance
│
├── data/                       # เก็บข้อมูลถาวรของผู้ใช้ (แทน Database ในเบื้องต้น)
│   ├── watchlist.json          # รายชื่อหุ้นใน Watchlist (Dynamic, เขียนทับเวลา Add/Remove)
│   ├── portfolio.json          # (เตรียมไว้สำหรับ Phase ถัดไป)
│   └── cache/                  # (เตรียมไว้สำหรับ cache เพิ่มเติมในอนาคต)
│
└── utils/                      # (เตรียมไว้สำหรับ helper functions ใน Phase 2-4)
```

**แนวคิดสถาปัตยกรรม:** แยก `watchlist_manager.py` (จัดการรายชื่อหุ้น) ออกจาก
`data_engine.py` (ดึงข้อมูลตลาด) เพื่อให้ทั้งสองไฟล์ทดสอบ/แก้ไขแยกกันได้
และเมื่อ Phase 2 (Math & Analytics Engine) เข้ามา จะเพิ่มไฟล์ `modules/analytics_engine.py`
ที่เรียกใช้ `data_engine.get_price_history()` และ `get_financials()` ต่อยอดได้ทันที
โดยไม่ต้องแก้โค้ดของ Phase 1

## ✅ ฟีเจอร์ที่ทำเสร็จใน Phase 1

- [x] Sidebar ช่อง Search เพิ่ม/ลบ Ticker แบบ Dynamic (เช่น `NVDA`, `TSM`, `TISCO.BK`)
- [x] ตรวจสอบความถูกต้องของ Ticker กับ Yahoo Finance ก่อนเพิ่มเข้า Watchlist
- [x] Persist Watchlist ลงไฟล์ JSON (`data/watchlist.json`) — ข้อมูลไม่หายเมื่อรีเฟรชหน้า
- [x] ดึงราคาเรียลไทม์ (ราคาล่าสุด, % เปลี่ยนแปลง, สูงสุด/ต่ำสุด, Market Cap, Volume)
- [x] ดึงงบการเงินย้อนหลัง (Income Statement + Balance Sheet ตามจำนวนปีที่ Yahoo Finance เปิดให้ฟรี)
- [x] กราฟราคาย้อนหลัง ปรับช่วงเวลาได้ (1mo / 3mo / 1y / 5y)
- [x] Cache ข้อมูล (ราคา 1 นาที, งบการเงิน 12 ชม.) ผ่าน `st.cache_data` + ปุ่ม Refresh ล้าง cache เอง
- [x] Layout แบบ `wide` ที่ปรับตัวได้ทั้งจอ PC และมือถือ (คอลัมน์ยุบอัตโนมัติบนจอแคบ)

## 🚀 วิธีติดตั้งและรัน

```bash
# 1) สร้างและเปิดใช้งาน virtual environment (แนะนำ)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2) ติดตั้ง dependencies
pip install -r requirements.txt

# 3) รันแอป
streamlit run app.py
```

จากนั้นเปิดเบราว์เซอร์ที่ `http://localhost:8501`

## 🔜 Phase ถัดไป

| Phase | เนื้อหา |
|---|---|
| Phase 2 | Math & Analytics Engine — Growth (1M/3M/1Y/5Y CAGR), EPS Growth, D/E, Gross Margin, Max Drawdown, Valuation Zone |
| Phase 3 | Scenario Analysis (Bull/Base/Bear) + Backtesting Win Rate + AI Feedback Loop (ปรับน้ำหนักจาก error ของการคาดการณ์วันก่อนหน้า) |
| Phase 4 | AI Co-Pilot Chat (LangChain + Claude) ฝั่งขวาของจอ + วิเคราะห์ข่าว Macro แบบเรียลไทม์ |

พิมพ์บอกได้เลยเมื่อพร้อมให้เริ่ม Phase 2 ครับ 🚀
