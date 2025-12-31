import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import google.generativeai as genai

# --- 1. CONFIGURATION & IA ---
st.set_page_config(page_title="منصة السُّنَن الرقمية", page_icon="🕌", layout="wide")

# Connexion Gemini
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

# --- 2. DESIGN CSS (STRICTEMENT MAINTENU) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; background-color: #f8f9fa; }
    .stApp { direction: ltr; }
    .stMarkdown, p, h1, h2, h3, h4, .stAlert { text-align: right !important; direction: rtl !important; }
    
    /* SLIDERS VERT ET OR */
    div[data-baseweb="slider"] > div:first-child > div:first-child {
        background: linear-gradient(90deg, #c9a44c 0%, #1e5631 100%) !important;
    }
    div[role="slider"] {
        background-color: #1e5631 !important;
        border: 3px solid #c9a44c !important;
    }
    .stSlider label { color: #1e5631 !important; font-weight: bold; }

    /* BOITES DE RESULTATS */
    .ai-analysis-card {
        background: white; border-right: 10px solid #1e5631; border-radius: 20px;
        padding: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); margin-top: 20px;
    }
    .challenge-box {
        background-color: #fcf3cf; border-radius: 15px; padding: 25px;
        border: 2px solid #c9a44c; margin-top: 20px; margin-bottom: 20px; color: #1b4f72;
    }
    .task-item { 
        background: rgba(255,255,255,0.8); padding: 12px; border-radius: 10px; 
        margin-bottom: 10px; border-right: 5px solid #1e5631; font-weight: bold; 
    }
</style>
""", unsafe_allow_html=True)

# --- 3. FONCTIONS ---
def get_google_sheet():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_dict = {
            "type": st.secrets["service_account"]["type"],
            "project_id": st.secrets["service_account"]["project_id"],
            "private_key_id": st.secrets["service_account"]["private_key_id"],
            "private_key": st.secrets["service_account"]["private_key"].replace("\\n", "\n"),
            "client_email": st.secrets["service_account"]["client_email"],
            "client_id": st.secrets["service_account"]["client_id"],
            "auth_uri": st.secrets["service_account"]["auth_uri"],
            "token_uri": st.secrets["service_account"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["service_account"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["service_account"]["client_x509_cert_url"]
        }
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client.open_by_key("1uXX-R40l8JQrPX8lcAxWbzxeeSs8Q5zaMF_DZ-R8TmE").sheet1
    except: return None

def get_gemini_response(user_name, diag, eff, def_s, coh):
    if model:
        prompt = f"""
        En tant qu'expert en stratégie de productivité, analyse ce profil :
        Nom: {user_name}, Diagnostic: {diag}, Efficacité: {eff}%, Défense: {def_s}%, Cohérence: {coh}%.
        1. Donne une analyse percutante en arabe (1 paragraphe).
        2. Propose un plan de 4 semaines (une tâche par semaine) pour s'améliorer.
        Réponds uniquement en Arabe.
        """
        try:
            response = model.generate_content(prompt)
            return response.text
        except: return "L'IA est temporairement indisponible."
    return "Veuillez configurer votre clé API Gemini."

def calculate_scores(data):
    raw_points = (data['p_ratio'] * 80) + (data['projects'] * 20)
    eff = (raw_points * (data['quality'] / 5)) - (data['hours'] * 3) + 15
    eff = max(min(round(eff, 2), 100), 5)
    total = data['orig'] + data['replies'] + 0.1
    def_s = round(((data['orig'] / total) * 60) + ((data['emotion'] / 10) * 40), 2)
    coh = min(round((data['align'] * 10) * (1.2 if data['team'] else 1.0), 2), 100)
    
    if eff < 45: diag = "🛑 ركود حضاري"
    elif def_s < 45: diag = "⚠️ جهد مكشوف"
    elif coh < 45: diag = "🧩 تشتت الجهد"
    else: diag = "🌟 استواء حضاري"
    return eff, def_s, coh, diag

# --- 4. INTERFACE ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2331/2331718.png", width=80)
    user_name = st.text_input("اسم المستخدم", "مبادر")
    st.markdown("---")
    d_hours = st.slider("ساعات التصفح", 0.0, 16.0, 4.0)
    p_ratio = st.slider("نسبة الإنتاج", 0.0, 1.0, 0.2)
    projects = st.number_input("مشاريع منجزة", 0, 50, 0)
    quality = st.select_slider("جودة المخرج", [1, 2, 3, 4, 5], value=3)
    orig = st.number_input("بصمة أصلية", 0, 50, 1)
    replies = st.number_input("ردود", 0, 100, 5)
    emotion = st.slider("الاتزان", 0, 10, 5)
    align = st.slider("وضوح الغاية", 0, 10, 5)
    team = st.checkbox("عمل جماعي")
    calc_btn = st.button("🔍 تحليل وبناء الخطة")

st.title("🕌 منصة السُّنَن الرقمية")

if calc_btn:
    vals = {'hours': d_hours, 'p_ratio': p_ratio, 'projects': projects, 'quality': quality, 'orig': orig, 'replies': replies, 'emotion': emotion, 'align': align, 'team': team}
    eff, def_s, coh, diag = calculate_scores(vals)
    
    with st.spinner('جاري استشارة الذكاء الاصطناعي...'):
        ai_full_text = get_gemini_response(user_name, diag, eff, def_s, coh)
    
    # AFFICHAGE DU PLAN DE 30 JOURS (Bloc Jaune)
    st.markdown(f"""
    <div class="challenge-box">
        <h3 style="margin-top:0; color:#d35400;">🚀 مسار الـ 30 يوماً المخصص (حسب تحليل Gemini)</h3>
        <p>{ai_full_text}</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_left, col_right = st.columns([1.5, 1])
    with col_left:
        fig = go.Figure(go.Scatterpolar(r=[eff, def_s, coh, eff], theta=['الفعالية', 'المناعة', 'التماسك', 'الفعالية'], fill='toself', fillcolor='rgba(30, 86, 49, 0.2)', line=dict(color='#c9a44c', width=4)))
        st.plotly_chart(fig, use_container_width=True)
    with col_right:
        st.markdown(f"""
            <div class="ai-analysis-card">
                <h2 style="color: #1e5631;">{user_name}</h2>
                <h4 style="color: #c9a44c;">التشخيص الحالي: {diag}</h4>
                <hr>
                <p>تم تحديث التحليل بناءً على بياناتك اللحظية عبر Gemini 1.5 Pro.</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("💾 حفظ النتيجة"):
            sheet = get_google_sheet()
            if sheet:
                sheet.append_row([user_name, datetime.now().strftime("%Y-%m-%d %H:%M"), str(eff), str(def_s), str(coh), diag])
                st.balloons()
