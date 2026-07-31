"""
modules/ai_copilot.py
---------------------
เชื่อมต่อ LLM (Gemini 3.5 Flash) ด้วย Google GenAI SDK (อัปเดต 2026)
"""
import streamlit as st
from google import genai
from google.genai import types

def get_ai_analysis(ticker: str, summary_data: dict, prompt: str) -> str:
    """ส่งข้อมูลทางการเงินให้ AI วิเคราะห์พร้อมคำถามจากผู้ใช้"""
    try:
        # 1. เช็ค API Key (กุญแจ AQ... ของคุณใช้ได้กับ SDK ใหม่นี้ครับ)
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            return "⚠️ กรุณาตั้งค่า GEMINI_API_KEY ใน Streamlit Secrets ก่อนใช้งาน"

        # 2. สร้าง Client ตามแบบฉบับปี 2026
        client = genai.Client(api_key=api_key)

        # 3. เตรียม Context ให้ AI (เป็น System Instruction)
        system_instruction = f"""
        คุณคือนักวิเคราะห์หุ้น Value Investing ระดับโลก เน้นความปลอดภัยของเงินทุน (Capital Protection) 
        และชื่นชอบบริษัทที่มี 'คูเมืองทางธุรกิจ' (Moat) โดยเฉพาะกลุ่ม Healthcare และ Technology
        
        ข้อมูลปัจจัยพื้นฐานปัจจุบันของ {ticker}:
        - ราคาปัจจุบัน: {summary_data.get('current_price')}
        - P/E Ratio: {summary_data.get('pe_ratio')}
        - D/E Ratio: {summary_data.get('debt_to_equity')}
        - Gross Margin (%): {summary_data.get('gross_margin')}
        - จุดประเมินมูลค่า (Valuation): {summary_data.get('valuation_zone')}
        """

        # 4. เรียกใช้โมเดลล่าสุด (gemini-3.5-flash)
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3,
            )
        )
        
        return response.text

    except Exception as e:
        return f"เกิดข้อผิดพลาดในการเชื่อมต่อ AI: {str(e)}"
