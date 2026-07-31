import pandas as pd
import streamlit as st

# --- นำเข้า Module 1 ถึง 4 ---
from modules import data_engine, watchlist_manager
from modules import analytics_engine, scenario_engine, ai_copilot
"""
app.py
------
Entry point ของ AI Investment Analyst Hub (Streamlit)

Phase 1 ของโปรเจกต์ — โฟกัสที่ Module 1: Data & Watchlist Engine
  - Sidebar: ช่อง Search เพิ่ม/ลบหุ้นใน Watchlist แบบ Dynamic
  - Main area: การ์ดราคาเรียลไทม์ของทุกหุ้นใน Watchlist
              + Tab แสดงงบการเงินย้อนหลัง (Income Statement / Balance Sheet)
              ของหุ้นที่เลือก

Module 2 (Analytics), 3 (Scenario/Feedback AI), 4 (Chat Co-Pilot) จะต่อยอด
เข้ากับโครงนี้ใน Phase ถัดไป โดยไม่ต้องรื้อโครงสร้างไฟล์นี้ใหม่
"""

import pandas as pd
import streamlit as st

from modules import data_engine, watchlist_manager

# ----------------------------------------------------------------------
# Page config — ต้องเป็นคำสั่ง Streamlit คำสั่งแรกของไฟล์
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="AI Investment Analyst Hub",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================================
# Helper: formatting
# ============================================================================
def fmt_money(value, currency="") -> str:
    if value is None:
        return "N/A"
    try:
        return f"{value:,.2f} {currency}".strip()
    except (TypeError, ValueError):
        return "N/A"


def fmt_pct(value) -> str:
    if value is None:
        return "N/A"
    try:
        return f"{value:+.2f}%"
    except (TypeError, ValueError):
        return "N/A"


def fmt_large_number(value) -> str:
    """แปลงตัวเลขใหญ่ (market cap, volume) ให้อ่านง่าย เช่น 1.2B, 850M"""
    if value is None:
        return "N/A"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "N/A"
    for unit, threshold in [("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)]:
        if abs(value) >= threshold:
            return f"{value / threshold:,.2f}{unit}"
    return f"{value:,.0f}"


# ============================================================================
# Sidebar: Watchlist Search + Management (Module 1)
# ============================================================================
def render_sidebar() -> str | None:
    """
    วาด Sidebar ทั้งหมด: ช่อง add ticker, ปุ่ม refresh, และรายการ watchlist
    ที่กดเลือกได้ (radio) เพื่อดูรายละเอียดในหน้าหลัก

    Returns:
        ticker ที่ผู้ใช้เลือกดูรายละเอียดอยู่ ณ ขณะนี้ (หรือ None ถ้า watchlist ว่าง)
    """
    st.sidebar.title("📊 AI Investment Analyst Hub")
    st.sidebar.caption("DCA & Value Investing Co-Pilot")

    st.sidebar.divider()

    # --- ฟอร์มเพิ่มหุ้นใหม่ ---
    st.sidebar.subheader("➕ เพิ่มหุ้นเข้า Watchlist")
    with st.sidebar.form(key="add_ticker_form", clear_on_submit=True):
        new_ticker_input = st.text_input(
            "พิมพ์ Ticker",
            placeholder="เช่น NVDA, TSM, TISCO.BK",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("เพิ่มหุ้น", use_container_width=True)

    if submitted and new_ticker_input:
        ticker = watchlist_manager.normalize_ticker(new_ticker_input)
        with st.spinner(f"กำลังตรวจสอบ '{ticker}' กับ Yahoo Finance..."):
            is_valid = data_engine.validate_ticker(ticker)

        if not is_valid:
            st.sidebar.error(f"ไม่พบ '{ticker}' บน Yahoo Finance กรุณาตรวจสอบชื่อ Ticker อีกครั้ง")
        else:
            success, message = watchlist_manager.add_ticker(ticker)
            if success:
                st.sidebar.success(message)
            else:
                st.sidebar.warning(message)
            st.rerun()

    st.sidebar.divider()

    # --- ปุ่ม refresh ข้อมูลทั้งหมด ---
    if st.sidebar.button("🔄 Refresh ข้อมูลทั้งหมด", use_container_width=True):
        data_engine.clear_all_cache()
        st.rerun()

    st.sidebar.divider()

    # --- รายการ watchlist ปัจจุบัน ---
    st.sidebar.subheader("👁️ Watchlist ของคุณ")
    tickers = watchlist_manager.get_watchlist()

    if not tickers:
        st.sidebar.info("Watchlist ว่างอยู่ — เพิ่มหุ้นตัวแรกของคุณด้านบนได้เลย")
        return None

    selected_ticker = st.session_state.get("selected_ticker")
    if selected_ticker not in tickers:
        selected_ticker = tickers[0]

    for ticker in tickers:
        col_select, col_remove = st.sidebar.columns([4, 1])
        with col_select:
            is_active = ticker == selected_ticker
            if st.button(
                f"{'▶ ' if is_active else ''}{ticker}",
                key=f"select_{ticker}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state["selected_ticker"] = ticker
                st.rerun()
        with col_remove:
            if st.button("🗑️", key=f"remove_{ticker}", help=f"ลบ {ticker} ออกจาก Watchlist"):
                watchlist_manager.remove_ticker(ticker)
                if st.session_state.get("selected_ticker") == ticker:
                    st.session_state.pop("selected_ticker", None)
                st.rerun()

    return selected_ticker


# ============================================================================
# Main area: Price snapshot cards (สรุปทุกหุ้นใน watchlist)
# ============================================================================
def render_watchlist_overview(tickers: list[str]) -> None:
    st.subheader("📋 ภาพรวม Watchlist")

    if not tickers:
        st.info("ยังไม่มีหุ้นใน Watchlist — เริ่มเพิ่มหุ้นได้จากแถบด้านซ้าย")
        return

    cols = st.columns(min(len(tickers), 4)) if len(tickers) <= 4 else st.columns(4)

    for idx, ticker in enumerate(tickers):
        price_data = data_engine.get_realtime_price(ticker)
        col = cols[idx % len(cols)]

        with col:
            with st.container(border=True):
                st.markdown(f"**{ticker}**")
                if not price_data.get("ok"):
                    st.caption("⚠️ ดึงราคาไม่สำเร็จ")
                    continue

                last_price = price_data.get("last_price")
                currency = price_data.get("currency", "")
                change_pct = price_data.get("change_pct")

                st.metric(
                    label=fmt_large_number(price_data.get("market_cap")) + f" {currency} Cap",
                    value=fmt_money(last_price, currency),
                    delta=fmt_pct(change_pct),
                )


# ============================================================================
# Main area: รายละเอียดหุ้นที่เลือก (Price detail + งบการเงิน 5 ปี)
# ============================================================================
def render_ticker_detail(ticker: str) -> None:
    st.subheader(f"🔍 รายละเอียด: {ticker}")

    price_data = data_engine.get_realtime_price(ticker)

    if not price_data.get("ok"):
        st.error(f"ไม่สามารถดึงข้อมูลราคาของ {ticker} ได้ ({price_data.get('error', 'unknown error')})")
        return

    currency = price_data.get("currency", "")

    # --- แถบสรุปราคา ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("ราคาล่าสุด", fmt_money(price_data.get("last_price"), currency),
              fmt_pct(price_data.get("change_pct")))
    m2.metric("ราคาปิดก่อนหน้า", fmt_money(price_data.get("previous_close"), currency))
    m3.metric("สูงสุด/ต่ำสุด (วัน)",
              f"{fmt_money(price_data.get('day_high'), '')} / {fmt_money(price_data.get('day_low'), '')}")
    m4.metric("สูงสุด/ต่ำสุด (52 สัปดาห์)",
              f"{fmt_money(price_data.get('year_high'), '')} / {fmt_money(price_data.get('year_low'), '')}")

    st.caption(f"Market Cap: {fmt_large_number(price_data.get('market_cap'))} {currency}"
               f"  |  Volume: {fmt_large_number(price_data.get('volume'))}")

    st.divider()

    # --- กราฟราคาย้อนหลัง ---
    st.markdown("##### 📈 ราคาย้อนหลัง")
    period_choice = st.select_slider(
        "ช่วงเวลา",
        options=["1mo", "3mo", "1y", "5y"],
        value="1y",
        label_visibility="collapsed",
    )
    history_df = data_engine.get_price_history(ticker, period=period_choice)
    if history_df is not None and not history_df.empty:
        st.line_chart(history_df["Close"], height=280)
    else:
        st.info("ไม่มีข้อมูลราคาย้อนหลังสำหรับช่วงเวลานี้")

    st.divider()

    # --- งบการเงินย้อนหลัง 5 ปี ---
    st.markdown("##### 🧾 งบการเงินย้อนหลัง")
    with st.spinner("กำลังดึงงบการเงิน..."):
        fin = data_engine.get_financials(ticker)

    if not fin["ok"]:
        st.warning(fin.get("error") or "ไม่พบข้อมูลงบการเงิน")
        return

    st.caption(f"พบข้อมูลย้อนหลัง {fin['years_available']} ปีงบการเงิน (ตามที่ Yahoo Finance เปิดให้ใช้งานฟรี)")

    tab_income, tab_balance = st.tabs(["Income Statement", "Balance Sheet"])

    with tab_income:
        if fin["income_statement"].empty:
            st.info("ไม่มีข้อมูล Income Statement")
        else:
            df = fin["income_statement"].copy()
            df.columns = [c.strftime("%Y-%m-%d") if hasattr(c, "strftime") else str(c) for c in df.columns]
            st.dataframe(df, use_container_width=True)

    with tab_balance:
        if fin["balance_sheet"].empty:
            st.info("ไม่มีข้อมูล Balance Sheet")
        else:
            df = fin["balance_sheet"].copy()
            df.columns = [c.strftime("%Y-%m-%d") if hasattr(c, "strftime") else str(c) for c in df.columns]
            st.dataframe(df, use_container_width=True)


# ============================================================================
# Main
# ============================================================================
def main() -> None:
    selected_ticker = render_sidebar()

    st.title("📈 AI Investment Analyst Hub")
    st.caption("ผู้ช่วยนักลงทุนระยะยาว — Capital Protection • Margin of Safety • DCA & Value Investing")

    tickers = watchlist_manager.get_watchlist()

    render_watchlist_overview(tickers)
    st.divider()

    if selected_ticker:
        st.session_state["selected_ticker"] = selected_ticker
        render_ticker_detail(selected_ticker)


if __name__ == "__main__":
    main()
