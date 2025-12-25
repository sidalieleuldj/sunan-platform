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

# --- 2. التصميم (CSS) - الحل الذكي (Fix) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* 1. ضبط الخط العام */
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
    }

    /* 2. الحفاظ على الهيكل LTR لمنع تكسر السلايدر، ولكن محاذاة النصوص لليمين */
    .stMarkdown, .stTextInput > label, .stNumberInput > label, .stSlider > label, .stSelectbox > label, p, h1, h2, h3, h4, h5 {
        text-align: right !important;
        direction: rtl !important;
    }

    /* 3. إصلاح خاص للـ Sliders (المشكلة التي في الصورة) */
    /* نجعل الحاوية LTR لكي لا تطير الأرقام، ولكن النص فوقها يمين */
    div[data-testid="stSlider"] {
        direction: ltr !important; 
    }
    /* محاذاة التسمية (Label) لليمين */
    div[data-testid="stSlider"] > label {
        text-align: right !important;
        width: 100%;
        display: block;
        direction: rtl !important;
    }
    
    /* 4. القائمة الجانبية: تبقى يساراً، ولكن محتواها يمين */
    section[data-testid="stSidebar"] {
        left: 0 !important;
        right: auto !important;
    }
    /* محاذاة النصوص داخل القائمة الجانبية */
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] h1 {
        text-align: right !important;
    }

    /* 5. تنسيق الأزرار وحقول الإدخال */
    .stButton>button {
        width: 100%;
        background-color: #1F618D;
        color: white;
        border-radius: 8px;
    }
    input {
        text-align: right !important;
    }
    
    /* 6. تحسين شكل التنبيهات */
    .stAlert {
        direction: rtl !important;
        text-align: right !important;
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
        # تأكد من الـ ID الصحيح
        sheet_id = "1uXX-R40l8JQrPX8lcAxWbzxeeSs8Q5zaMF_DZ-R8TmE" 
        return client.open_by_key(sheet_id).sheet1
    except:
        return None

def save_to_google_sheet(name, eff, def_score, coh, diagnosis):
    sheet = get_google_sheet()
    if sheet:
        try:
            row = [name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), eff, def_score, coh, diagnosis]
            sheet.append_row(row)
            return True
        except: return False
    return False

def load_history_data():
    sheet = get_google_sheet()
    if sheet:
        try:
            data = sheet.get_all_records()
            return pd.DataFrame(data)
        except: pass
    return pd.DataFrame()

# --- 4. محرك السنن ---
def calculate_sunan_scores(data):
    raw_points = (data['production_ratio'] * 80) + (data['completed_projects'] * 20)
    quality_factor = data['quality_score'] / 5
    eff = (raw_points * quality_factor) - (data['daily_hours'] * 3) + 15
    eff = max(min(round(eff, 2), 100), 5)
    
    total = data['original_posts'] + data['replies'] + 0.1
    def_s = round(((data['original_posts'] / total) * 60) + ((data['emotional_stability'] / 10) * 40), 2)
    
    coh = min(round((data['task_alignment'] * 10) * (1.2 if data['is_team'] else 1.0), 2), 100)
    
    if eff < 45: 
        diag = "🛑 ركود حضاري: تستهلك أكثر مما تنتج."
        acts = ["خصص ساعة عمل مركزة.", "قلل التصفح."]
    elif def_s < 45: 
        diag = "⚠️ جهد مكشوف: مستنزف في ردود الأفعال."
        acts = ["توقف عن الجدال.", "ابنِ محتواك الخاص."]
    elif coh < 45: 
        diag = "🧩 تشتت الجهد: ذرة قوية لكن منعزلة."
        acts = ["ابحث عن شريك.", "اربط عملك بهدف."]
    else: 
        diag = "🌟 حالة متوازنة (الاستواء الحضاري): استمر."
        acts = []
        
    return eff, def_s, coh, diag, acts

# --- 5. واجهة المستخدم ---
if 'res' not in st.session_state: st.session_state['res'] = None

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2331/2331718.png", width=60)
    st.header("🎛️ لوحة التحكم")
    
    st.markdown("### 👤 بيانات المستخدم")
    user_name = st.text_input("سجل اسمك هنا", "مبادر")
    st.markdown("---")
    
    with st.expander("⏱️ 1. محور الفعالية", expanded=True):
        d_hours = st.slider("ساعات التصفح", 0.0, 16.0, 4.0)
        p_ratio = st.slider("نسبة الإنتاج", 0.0, 1.0, 0.2)
        projects = st.number_input("مشاريع مكتملة", 0, 50, 0)
        quality = st.select_slider("جودة الأثر", options=[1, 2, 3, 4, 5], value=3)
        
    with st.expander("🛡️ 2. محور المناعة"):
        orig = st.number_input("بصمتك (أصلي)", 0, 50, 1)
        replies = st.number_input("ردود أفعال", 0, 100, 5)
        emotion = st.slider("الهدوء النفسي", 0, 10, 5)
        
    with st.expander("🤝 3. محور التماسك"):
        align = st.slider("وضوح الهدف", 0, 10, 5)
        team = st.checkbox("عمل جماعي")
        
    calc_btn = st.button("🔍 تحليل الموقف")

st.title("🕌 منصة السُّنَن الرقمية")

if calc_btn:
    vals = {
        'daily_hours': d_hours, 'production_ratio': p_ratio, 'completed_projects': projects,
        'quality_score': quality, 'original_posts': orig, 'replies': replies,
        'emotional_stability': emotion, 'task_alignment': align, 'is_team': team
    }
    st.session_state['res'] = calculate_sunan_scores(vals)

if st.session_state['res']:
    eff, def_s, coh, diag, acts = st.session_state['res']
    
    col_chart, col_info = st.columns([1.5, 1])
    with col_chart:
        fig = go.Figure(go.Scatterpolar(r=[eff, def_s, coh], theta=['الفعالية', 'المناعة', 'التماسك'], fill='toself', line_color='#1F618D'))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), margin=dict(t=40, b=40))
        st.plotly_chart(fig, use_container_width=True)
        
    with col_info:
        st.subheader(f"نتيجة: {user_name}")
        st.info(diag)
        if acts:
            for a in acts: st.warning
