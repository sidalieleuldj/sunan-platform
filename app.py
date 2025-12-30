import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="منصة السُّنَن الرقمية", page_icon="🕌", layout="wide")

# --- 2. CONNEXION GOOGLE SHEETS ---
def get_google_sheet():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        
        # تحويل Secrets إلى قاموس عادي
        creds_info = {
            "type": st.secrets["service_account"]["type"],
            "project_id": st.secrets["service_account"]["project_id"],
            "private_key_id": st.secrets["service_account"]["private_key_id"],
            "private_key": st.secrets["service_account"]["private_key"].replace("\\n", "\n"), # أهم سطر
            "client_email": st.secrets["service_account"]["client_email"],
            "client_id": st.secrets["service_account"]["client_id"],
            "auth_uri": st.secrets["service_account"]["auth_uri"],
            "token_uri": st.secrets["service_account"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["service_account"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["service_account"]["client_x509_cert_url"]
        }
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)
        sheet_id = "1uXX-R40l8JQrPX8lcAxWbzxeeSs8Q5zaMF_DZ-R8TmE" 
        return client.open_by_key(sheet_id).sheet1
    except Exception as e:
        # هذا سيطبع لك الخطأ بالتفصيل في الشريط الجانبي لتشخيص المشكلة
        st.sidebar.error(f"تفاصيل الخطأ: {str(e)}")
        return None
        
# --- 3. LOGIQUE DE CALCUL ---
def calculate_sunan_scores(data):
    # (Votre logique de calcul reste la même)
    raw_points = (data['production_ratio'] * 80) + (data['completed_projects'] * 20)
    quality_factor = data['quality_score'] / 5
    eff = (raw_points * quality_factor) - (data['daily_hours'] * 3) + 15
    eff = max(min(round(eff, 2), 100), 5)
    
    total = data['original_posts'] + data['replies'] + 0.1
    def_s = round(((data['original_posts'] / total) * 60) + ((data['emotional_stability'] / 10) * 40), 2)
    coh = min(round((data['task_alignment'] * 10) * (1.2 if data['is_team'] else 1.0), 2), 100)
    
    if eff < 45: diag, acts = "🛑 ركود حضاري", ["خصص ساعة عمل مركزة.", "قلل التصفح."]
    elif def_s < 45: diag, acts = "⚠️ جهد مكشوف", ["توقف عن الجدال.", "ابنِ محتواك الخاص."]
    elif coh < 45: diag, acts = "🧩 تشتت الجهد", ["ابحث عن شريك.", "اربط عملك بهدف."]
    else: diag, acts = "🌟 استواء حضاري", ["زكاة العلم تعليمه.", "وثّق تجربتك."]
    return eff, def_s, coh, diag, acts

# --- 4. INTERFACE ---
if 'res' not in st.session_state: st.session_state['res'] = None

with st.sidebar:
    st.header("🎛️ لوحة التحكم")
    user_name = st.text_input("الاسم", "مبادر")
    d_hours = st.slider("ساعات التصفh", 0.0, 16.0, 4.0)
    p_ratio = st.slider("نسبة الإنتاج", 0.0, 1.0, 0.2)
    projects = st.number_input("مشاريع", 0, 50, 0)
    quality = st.select_slider("الجودة", [1, 2, 3, 4, 5], value=3)
    orig = st.number_input("بصمتك", 0, 50, 1)
    replies = st.number_input("ردود", 0, 100, 5)
    emotion = st.slider("الهدوء", 0, 10, 5)
    align = st.slider("وضوح الهدف", 0, 10, 5)
    team = st.checkbox("عمل جماعي")
    
    if st.button("🔍 تحليل"):
        vals = {'daily_hours': d_hours, 'production_ratio': p_ratio, 'completed_projects': projects,
                'quality_score': quality, 'original_posts': orig, 'replies': replies,
                'emotional_stability': emotion, 'task_alignment': align, 'is_team': team}
        st.session_state['res'] = calculate_sunan_scores(vals)

st.title("🕌 منصة السُّنَن الرقمية")

# AFFICHAGE DES RÉSULTATS
if st.session_state['res']:
    # ON EXTRAIT LES VALEURS DEPUIS LE SESSION STATE POUR ÉVITER LE NAMERROR
    eff, def_s, coh, diag, acts = st.session_state['res']
    
    c1, c2 = st.columns([1.5, 1])
    with c1:
        fig = go.Figure(go.Scatterpolar(r=[eff, def_s, coh, eff], theta=['الفعالية', 'المناعة', 'التماسك', 'الفعالية'], fill='toself'))
        st.plotly_chart(fig)
    with c2:
        st.info(f"النتيجة: {user_name}\n\n{diag}")
        for a in acts: st.warning(f"💡 {a}")
    
    # LE BOUTON DE SAUVEGARDE EST ICI, À L'INTÉRIEUR DU IF
    if st.button("💾 حفظ النتيجة"):
        if user_name != "مبادر":
            success = save_to_google_sheet(user_name, eff, def_s, coh, diag)
            if success:
                st.success("تم الحفظ!")
                st.balloons()
            else:
                st.error("خطأ في الحفظ")
        else:
            st.error("الرجاء إدخال الاسم")

