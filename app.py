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
    st.subheader(f"🔍 รายละเอียดเจาะลึก: {ticker}")

    # ดึงข้อมูลมาเตรียมไว้
    price_data = data_engine.get_realtime_price(ticker)
    fin_data = data_engine.get_financials(ticker)
    history_df = data_engine.get_price_history(ticker, period="5y")
    
    if not price_data.get("ok"):
        st.error(f"ไม่สามารถดึงข้อมูลราคาของ {ticker} ได้")
        return

    # คำนวณ Analytics & Valuation (Phase 2)
    summary = analytics_engine.get_stock_summary(price_data, fin_data)
    
    # ---------------------------------------------------------
    # จัด Layout แบบ 2 ฝั่ง (ฝั่งซ้าย = Data, ฝั่งขวา = AI Chat)
    # ---------------------------------------------------------
    col_data, col_ai = st.columns([7, 3], gap="large")

    with col_data:
        # --- แถบสรุปราคา ---
        currency = price_data.get("currency", "")
        m1, m2, m3 = st.columns(3)
        m1.metric("ราคาล่าสุด", fmt_money(price_data.get("last_price"), currency), fmt_pct(price_data.get("change_pct")))
        m2.metric("P/E Ratio", f"{summary.get('pe_ratio', 0):.2f}x" if summary.get('pe_ratio') else "N/A")
        m3.metric("Valuation Zone", summary.get('valuation_zone', 'N/A'))
        st.divider()

        # --- สร้าง 3 Tabs สำหรับดูข้อมูล ---
        tab_price, tab_value, tab_scenario = st.tabs(["📈 ราคา & งบการเงิน", "📊 Value & Moat Analysis", "🔮 DCA & Stress Test"])
        
        with tab_price:
            if not history_df.empty:
                st.line_chart(history_df["Close"], height=250)
            st.markdown("##### 🧾 งบการเงินแบบย่อ")
            if fin_data["ok"]:
                st.dataframe(fin_data["income_statement"].head(5), use_container_width=True)
            else:
                st.warning("ไม่พบข้อมูลงบการเงิน")
                
        with tab_value:
            st.markdown("#### การประเมินมูลค่า และ ความแข็งแกร่ง (Phase 2)")
            v1, v2, v3 = st.columns(3)
            v1.metric("Graham Number (มูลค่าที่เหมาะสม)", fmt_money(summary.get("graham_number"), currency))
            v2.metric("Margin of Safety (%)", fmt_pct(summary.get("margin_of_safety")))
            v3.metric("Debt to Equity (หนี้สินต่อทุน)", f"{summary.get('debt_to_equity', 0):.2f}x" if summary.get('debt_to_equity') else "N/A")
            st.info("💡 กฎสาย Value: พยายามซื้อหุ้นที่มี Margin of Safety เป็นบวก (ราคาตลาดถูกกว่า Graham Number) และ D/E ต่ำๆ")

        with tab_scenario:
            st.markdown("#### ทดสอบความเสี่ยง & DCA (Phase 3)")
            max_dd = scenario_engine.calculate_max_drawdown(history_df)
            st.error(f"📉 **Max Drawdown (5 ปีหลังสุด):** หุ้นตัวนี้เคยร่วงหนักสุด **{max_dd}%** จากจุดสูงสุด (รับความเสี่ยงนี้ได้หรือไม่?)")
            
            st.markdown("##### 💰 เครื่องมือจำลอง DCA")
            c1, c2, c3 = st.columns(3)
            monthly_inv = c1.number_input("ลงทุนต่อเดือน", value=5000, step=1000)
            years_inv = c2.number_input("ระยะเวลา (ปี)", value=10, min_value=1, max_value=30)
            expected_return = c3.number_input("ผลตอบแทนคาดหวัง (% ต่อปี)", value=8.0)
            
            dca_df = scenario_engine.simulate_dca(monthly_inv, years_inv, expected_return)
            st.area_chart(dca_df)

    with col_ai:
        # --- AI Co-Pilot Chat (Phase 4) ---
        st.subheader("🤖 AI Co-Pilot")
        st.caption("สอบถามความเห็นการลงทุน")
        
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
            
        # แสดงประวัติแชท
        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(msg["text"])
            
        # ช่องพิมพ์ถาม AI
        user_ask = st.chat_input(f"วิเคราะห์ {ticker} ให้หน่อย...")
        if user_ask:
            st.session_state.chat_history.append({"role": "user", "text": user_ask})
            st.chat_message("user").write(user_ask)
            
            with st.spinner("AI กำลังวิเคราะห์ปัจจัยพื้นฐาน..."):
                answer = ai_copilot.get_ai_analysis(ticker, summary, user_ask)
                st.session_state.chat_history.append({"role": "assistant", "text": answer})
                st.chat_message("assistant").write(answer)


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
