import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="منصة السُّنَن الرقمية", page_icon="🕌", layout="wide")

# --- 2. CSS المطور والقوي جداً للتصميم ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* الخطوط والخلفية */
    html, body, [class*="css"] { 
        font-family: 'Cairo', sans-serif; 
        text-align: right; 
        background-color: #f8f9fa;
    }

    /* --- تحسين السلايدر (أهم جزء) --- */
    /* تغيير لون الدائرة المتحركة */
    div[role="slider"] {
        background-color: #1e5631 !important; 
        border: 3px solid #c9a44c !important;
        box-shadow: 0px 0px 8px rgba(30, 86, 49, 0.4) !important;
    }

    /* استهداف شريط التمرير النشط (تغيير الأحمر للأخضر والذهبي) */
    div[data-baseweb="slider"] > div:first-child > div:first-child {
        background: linear-gradient(90deg, #c9a44c 0%, #1e5631 100%) !important;
    }

    /* تحسين العناوين فوق السلايدر */
    .stSlider label {
        color: #1e5631 !important;
        font-weight: 700 !important;
        font-size: 1.1em !important;
    }

    /* --- تحسين الأزرار --- */
    .stButton>button {
        background: linear-gradient(135deg, #1e5631 0%, #2d8a4e 100%) !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        padding: 15px !important;
        font-weight: bold !important;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 10px 20px rgba(45, 138, 78, 0.3) !important;
    }

    /* --- تنسيق الحاويات والبطاقات --- */
    div[data-testid="stExpander"] {
        background-color: white !important;
        border-radius: 15px !important;
        border: 1px solid #e0e0e0 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }

    h1 { color: #1e5631; border-bottom: 3px solid #c9a44c; padding-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 3. وظائف قاعدة البيانات ---
def get_google_sheet():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_info = dict(st.secrets["service_account"])
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)
        return client.open_by_key("1uXX-R40l8JQrPX8lcAxWbzxeeSs8Q5zaMF_DZ-R8TmE").sheet1
    except: return None

def calculate_sunan_scores(data):
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

# --- 4. واجهة المستخدم (Sidebar) ---
if 'res' not in st.session_state: st.session_state['res'] = None

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2331/2331718.png", width=80)
    st.header("لوحة التحكم")
    user_name = st.text_input("اسم المستخدم", "مبادر")
    st.markdown("---")
    
    with st.expander("⏱️ الفعالية", expanded=True):
        d_hours = st.slider("ساعات التصفح اليومي", 0.0, 16.0, 4.0)
        p_ratio = st.slider("نسبة الإنتاج الحقيقي", 0.0, 1.0, 0.2)
        projects = st.number_input("المشاريع المنجزة", 0, 50, 0)
        quality = st.select_slider("جودة المخرجات", [1, 2, 3, 4, 5], value=3)
        
    with st.expander("🛡️ المناعة الرقمية"):
        orig = st.number_input("المنشورات الأصلية", 0, 50, 1)
        replies = st.number_input("التفاعلات والردود", 0, 100, 5)
        emotion = st.slider("الهدوء النفسي", 0, 10, 5)
        
    with st.expander("🤝 التماسك"):
        align = st.slider("وضوح الهدف", 0, 10, 5)
        team = st.checkbox("عمل جماعي")
    
    calc_btn = st.button("🔍 تحليل البيانات")

# --- 5. العرض الرئيسي ---
st.title("🕌 منصة السُّنَن الرقمية")

if calc_btn:
    vals = {'daily_hours': d_hours, 'production_ratio': p_ratio, 'completed_projects': projects,
            'quality_score': quality, 'original_posts': orig, 'replies': replies,
            'emotional_stability': emotion, 'task_alignment': align, 'is_team': team}
    st.session_state['res'] = calculate_sunan_scores(vals)

if st.session_state['res']:
    eff, def_s, coh, diag, acts = st.session_state['res']
    c1, c2 = st.columns([1.5, 1])
    
    with c1:
        # الرسم البياني بألوان ذهبية وخضراء
        fig = go.Figure(go.Scatterpolar(
            r=[eff, def_s, coh, eff], 
            theta=['الفعالية', 'المناعة', 'التماسك', 'الفعالية'], 
            fill='toself', fillcolor='rgba(45, 138, 78, 0.2)',
            line=dict(color='#c9a44c', width=3)
        ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), margin=dict(t=40, b=40))
        st.plotly_chart(fig, use_container_width=True)
    
    with c2:
        st.markdown(f"""
            <div style="background-color: white; padding: 25px; border-radius: 15px; border-right: 8px solid #c9a44c; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                <h3 style="color: #1e5631; margin-top: 0;">{user_name}</h3>
                <p style="font-size: 1.4em; font-weight: bold; color: #2d8a4e;">{diag}</p>
            </div>
        """, unsafe_allow_html=True)
        st.write("")
        for a in acts: st.success(f"💡 {a}")
    
    if st.button("💾 حفظ النتيجة"):
        sheet = get_google_sheet()
        if sheet and user_name != "مبادر":
            sheet.append_row([user_name, datetime.now().strftime("%Y-%m-%d %H:%M"), str(eff), str(def_s), str(coh), diag])
            st.balloons()
            st.success("تم الحفظ بنجاح!")
