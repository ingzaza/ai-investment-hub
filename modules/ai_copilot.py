"""
modules/ai_copilot.py
---------------------
เชื่อมต่อ LLM (Gemini) แบบ Native SDK เพื่อวิเคราะห์หุ้น
พร้อมระบบค้นหาโมเดลอัตโนมัติ ป้องกัน Error 404
"""
import streamlit as st
import google.generativeai as genai

def get_ai_analysis(ticker: str, summary_data: dict, prompt: str) -> str:
    """ส่งข้อมูลทางการเงินให้ AI วิเคราะห์พร้อมคำถามจากผู้ใช้"""
    try:
        # 1. เช็ค API Key
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            return "⚠️ กรุณาตั้งค่า GEMINI_API_KEY ใน Streamlit Secrets ก่อนใช้งาน"

        genai.configure(api_key=api_key)

        # 2. ค้นหาโมเดลทั้งหมดที่ API Key นี้มีสิทธิ์ใช้งานได้จริง (สแกนสดๆ)
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        if not available_models:
            return "⚠️ กุญแจ API ของคุณยังไม่มีสิทธิ์ใช้งานโมเดลใดๆ เลย (อาจต้องสร้าง Project ใหม่ใน AI Studio)"

        # 3. เลือกใช้โมเดลตระกูล flash ก่อน ถ้าไม่มีให้หยิบตัวแรกสุดที่มันเจอมาใช้เลย
        target_model = next((m for m in available_models if 'flash' in m), available_models[0])
        model_name = target_model.replace("models/", "") # จัดฟอร์แมตชื่อให้ถูกต้อง

        # 4. สร้างสมอง AI จากโมเดลที่หาเจอ
        model = genai.GenerativeModel(model_name)
        
        # 5. ปั้น Context ยัดใส่สมอง AI
        context = f"""
        คุณคือนักวิเคราะห์หุ้น Value Investing ระดับโลก เน้นความปลอดภัยของเงินทุน (Capital Protection) 
        และชื่นชอบบริษัทที่มี 'คูเมืองทางธุรกิจ' (Moat) โดยเฉพาะกลุ่ม Healthcare และ Technology
        
        ข้อมูลปัจจัยพื้นฐานปัจจุบันของ {ticker}:
        - ราคาปัจจุบัน: {summary_data.get('current_price')}
        - P/E Ratio: {summary_data.get('pe_ratio')}
        - D/E Ratio: {summary_data.get('debt_to_equity')}
        - Gross Margin (%): {summary_data.get('gross_margin')}
        - จุดประเมินมูลค่า (Valuation): {summary_data.get('valuation_zone')}
        
        คำถามจากผู้ใช้: {prompt}
        """

        # 6. ส่งคำถามตรงเข้า Google
        response = model.generate_content(context)
        
        # คืนค่าคำตอบพร้อมแอบบอกชื่อโมเดลที่มันดึงมาใช้ได้จริง
        return f"*(Auto-selected: {model_name})*\n\n{response.text}"

    except Exception as e:
        return f"เกิดข้อผิดพลาดในการเชื่อมต่อ AI: {str(e)}"
