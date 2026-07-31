"""
modules/ai_copilot.py
---------------------
เชื่อมต่อ LLM (Gemini) เพื่อวิเคราะห์หุ้นจาก Context ข้อมูลที่มี (ใช้ API ฟรีของ Google)
"""
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

def get_ai_analysis(ticker: str, summary_data: dict, prompt: str) -> str:
    """ส่งข้อมูลทางการเงินให้ AI วิเคราะห์พร้อมคำถามจากผู้ใช้"""
    try:
        # เช็คว่ามี API Key ไหม
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            return "⚠️ กรุณาตั้งค่า GEMINI_API_KEY ใน Streamlit Secrets ก่อนใช้งาน"

        # แก้ไขชื่อโมเดลเติม -latest เพื่อแก้ปัญหา 404 NOT FOUND
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", google_api_key=api_key, temperature=0.3)
        
        # ปั้น Context ยัดใส่สมอง AI
        context = f"""
        คุณคือนักวิเคราะห์หุ้น Value Investing ระดับโลก เน้นความปลอดภัยของเงินทุน (Capital Protection) 
        และชื่นชอบบริษัทที่มี 'คูเมืองทางธุรกิจ' (Moat) โดยเฉพาะกลุ่ม Healthcare และ Technology
        
        ข้อมูลปัจจัยพื้นฐานปัจจุบันของ {ticker}:
        - ราคาปัจจุบัน: {summary_data.get('current_price')}
        - P/E Ratio: {summary_data.get('pe_ratio')}
        - D/E Ratio: {summary_data.get('debt_to_equity')}
        - Gross Margin (%): {summary_data.get('gross_margin')}
        - จุดประเมินมูลค่า (Valuation): {summary_data.get('valuation_zone')}
        """

        messages = [
            SystemMessage(content=context),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        return response.content

    except Exception as e:
        return f"เกิดข้อผิดพลาดในการเชื่อมต่อ AI: {str(e)}"
