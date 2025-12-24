import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="منصة السُّنَن الرقمية",
    page_icon="🕌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. التصميم (CSS) - النسخة التي تضمن بقاء اللوحة يساراً ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* جعل الصفحة والخطوط تدعم العربية دون قلب مكان القائمة */
    body, .main, .stMarkdown, p, h1, h2, h3, h4, h5, span, div {
        font-family: 'Cairo', sans-serif !important;
        text-align: right !important;
        direction: rtl !important;
    }

    /* إجبار القائمة الجانبية على البقاء في اليسار وعدم قلبها */
    section[data-testid="stSidebar"] {
        left: 0 !important;
        right: auto !important;
        text-align: right !important;
    }

    /* تصحيح اتجاه السلايدرز داخل القائمة */
    .stSlider, .stCheckbox, .stNumberInput {
        direction: rtl !important;
        text-align: right !important;
    }

    /* تحسين شكل الأزرار */
    .stButton>button {
        width: 100%;
        background-color: #1F618D;
        color: white;
        border-radius: 8px;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. الاتصال بقاعدة البيانات ---
def get_google_sheet():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_dict = st.secrets["service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet_id = "1uXX-R40l8JQrPX8lcAxWbzxeeSs8Q5zaMF_DZ-R8TmE" 
        return client.open_by_key(sheet_id).sheet1
    except:
        return None

def save_to_google_sheet(eff, def_score, coh, diagnosis):
    sheet = get_google_sheet()
    if sheet:
        try:
            row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), eff, def_score, coh, diagnosis]
            sheet.append_row(row)
            return True
        except: return False
    return False

# --- 4. محرك السنن ---
def calculate_sunan_scores(data):
    # معادلة الفعالية المحدثة لتتأثر فورياً بالتغيير
    eff = ((data['production_ratio'] * 70) + (data['completed_projects'] * 15)) * (data['quality_score'] / 5) - (data['daily_hours'] * 2) + 15
    eff = max(min(round(eff, 2), 100), 5)
    
    total = data['original_posts'] + data['replies'] + 0.1
    def_s = round(((data['original_posts'] / total) * 60) + ((data['emotional_stability'] / 10) * 40), 2)
    coh = min(round((data['task_alignment'] * 10) * (1.2 if data['is_team'] else 1.0), 2), 100)
    
    if eff < 45: diag = "🛑 ركود حضاري: استهلاكك يطغى على إنتاجك."
    elif def_s < 45: diag = "⚠️ جهد مكشوف: أنت مستنزف في ردود الأفعال."
    else: diag = "🌟 حالة متوازنة: أنت تسيطر على أدواتك الرقمية."
    return eff, def_s, coh, diag

# --- 5. واجهة المستخدم ---
if 'res' not in st.session_state: st.session_state['res'] = None

with st.sidebar:
    st.header("🎛️ لوحة التحكم")
    d_hours = st.slider("ساعات التصفح", 0.0, 16.0, 4.0)
    p_ratio = st.slider("نسبة الإنتاج", 0.0, 1.0, 0.2)
    projects = st.number_input("مشاريع مكتملة", 0, 50, 0)
    quality = st.select_slider("جودة الأثر", options=[1, 2, 3, 4, 5], value=3)
    st.markdown("---")
    orig = st.number_input("بصمتك (أصلي)", 0, 50, 1)
    replies = st.number_input("ردود أفعال", 0, 100, 5)
    emotion = st.slider("الهدوء النفسي", 0, 10, 5)
    st.markdown("---")
    align = st.slider("وضوح الهدف", 0, 10, 5)
    team = st.checkbox("عمل جماعي")
    calc_btn = st.button("🔍 تحليل الموقف")

st.title("🕌 منصة السُّنَن الرقمية")

if calc_btn:
    st.session_state['res'] = calculate_sunan_scores({
        'daily_hours': d_hours, 'production_ratio': p_ratio, 'completed_projects': projects,
        'quality_score': quality, 'original_posts': orig, 'replies': replies,
        'emotional_stability': emotion, 'task_alignment': align, 'is_team': team
    })

if st.session_state['res']:
    eff, def_s, coh, diag = st.session_state['res']
    col_chart, col_info = st.columns([1.5, 1])
    with col_chart:
        fig = go.Figure(go.Scatterpolar(r=[eff, def_s, coh], theta=['الفعالية', 'المناعة', 'التماسك'], fill='toself', line_color='#1F618D'))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), margin=dict(t=40, b=40))
        st.plotly_chart(fig, use_container_width=True)
    with col_info:
        st.info(diag)
        if st.button("💾 حفظ النتيجة"):
            if save_to_google_sheet(eff, def_s, coh, diag):
                st.balloons(); st.success("✅ تم الحفظ")
