import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import google.generativeai as genai

# --- 1. إعدادات الصفحة والذكاء الاصطناعي ---
st.set_page_config(page_title="منصة السُّنَن الرقمية", page_icon="🕌", layout="wide")

# محاولة جلب مفتاح Gemini بأكثر من طريقة لضمان العمل
api_key = st.secrets.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

# --- 2. التصميم الشامل (CSS) - النسخة الأصلية المحمية للسلايدر ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Cairo', sans-serif; 
        text-align: right; 
        background-color: #f8f9fa;
    }
    .stApp { direction: ltr; }
    .stMarkdown, p, h1, h2, h3, h4, .stAlert { text-align: right !important; direction: rtl !important; }
    
    /* تثبيت تصميم السلايدر المطور (الأخضر والذهبي) */
    div[data-baseweb="slider"] > div:first-child > div:first-child {
        background: linear-gradient(90deg, #c9a44c 0%, #1e5631 100%) !important;
        height: 12px !important;
        border-radius: 6px !important;
    }
    div[role="slider"] {
        background-color: #1e5631 !important;
        border: 3px solid #c9a44c !important;
        height: 24px !important;
        width: 24px !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
    }
    .stSlider label { color: #1e5631 !important; font-weight: 900 !important; font-size: 1.1em !important; }

    /* صناديق النتائج والتحدي */
    .ai-analysis-card {
        background: white; border-right: 10px solid #c9a44c; border-radius: 20px;
        padding: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); margin-top: 20px;
    }
    .challenge-box {
        background-color: #fcf3cf; border-radius: 15px; padding: 25px;
        border: 2px solid #c9a44c; margin-top: 20px; margin-bottom: 20px; color: #1b4f72;
    }
    .stButton>button {
        background: linear-gradient(135deg, #1e5631 0%, #2d8a4e 100%) !important;
        color: white !important; border-radius: 12px !important; font-weight: 900 !important; padding: 15px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. الدوال البرمجية ---
def get_google_sheet():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        # قراءة البيانات من هيكل السيكرت الخاص بك
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

def load_history_data():
    sheet = get_google_sheet()
    if sheet:
        try:
            data = sheet.get_all_values()
            if len(data) > 1:
                df = pd.DataFrame(data[1:], columns=['Name', 'Date', 'Score_Eff', 'Score_Def', 'Score_Coh', 'Diagnosis'])
                for c in ['Score_Eff', 'Score_Def', 'Score_Coh']:
                    df[c] = pd.to_numeric(df[c].str.replace(',', '.'), errors='coerce').fillna(0)
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                return df
        except: pass
    return pd.DataFrame()

def get_gemini_analysis(name, diag, eff, def_s, coh):
    if model:
        prompt = f"حلل أداء {name} (تشخيص: {diag}) بدرجات: فعالية {eff}%، مناعة {def_s}%، تماسك {coh}%. قدم تحليلاً حضارياً وتحدياً من 4 أسابيع."
        try:
            return model.generate_content(prompt).text
        except: return "خطأ في الاتصال بالذكاء الاصطناعي."
    return "⚠️ يرجى التأكد من وضع GEMINI_API_KEY في ملف Secrets."

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

# --- 4. واجهة المستخدم ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2331/2331718.png", width=80)
    user_name = st.text_input("اسم المبادر", "مبادر")
    st.markdown("---")
    d_hours = st.slider("ساعات التصفح", 0.0, 16.0, 4.0)
    p_ratio = st.slider("نسبة الإنتاج", 0.0, 1.0, 0.2)
    projects = st.number_input("مشاريع منجزة", 0, 50, 0)
    quality = st.select_slider("جودة المخرج", [1, 2, 3, 4, 5], value=3)
    orig = st.number_input("منشورات أصلية", 0, 50, 1)
    replies = st.number_input("ردود", 0, 100, 5)
    emotion = st.slider("الاتزان", 0, 10, 5)
    align = st.slider("وضوح الغاية", 0, 10, 5)
    team = st.checkbox("عمل جماعي")
    calc_btn = st.button("🔍 تحليل واستشارة ذكية")

st.title("🕌 منصة السُّنَن الرقمية")

if calc_btn:
    vals = {'hours': d_hours, 'p_ratio': p_ratio, 'projects': projects, 'quality': quality, 'orig': orig, 'replies': replies, 'emotion': emotion, 'align': align, 'team': team}
    eff, def_s, coh, diag = calculate_scores(vals)
    
    with st.spinner('جاري طلب التحليل من Gemini...'):
        report = get_gemini_analysis(user_name, diag, eff, def_s, coh)
    
    # عرض التحدي المخصص (الصندوق الذهبي)
    st.markdown(f'<div class="challenge-box"><h3>🚀 مسار الـ 30 يوماً المخصص</h3>{report}</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1.5, 1])
    with col1:
        fig = go.Figure(go.Scatterpolar(r=[eff, def_s, coh, eff], theta=['الفعالية', 'المناعة', 'التماسك', 'الفعالية'], fill='toself', fillcolor='rgba(30, 86, 49, 0.2)', line=dict(color='#c9a44c', width=4)))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown(f'<div class="ai-analysis-card"><h2>{user_name}</h2><h4>التشخيص: {diag}</h4></div>', unsafe_allow_html=True)
        if st.button("💾 حفظ النتيجة"):
            sheet = get_google_sheet()
            if sheet:
                sheet.append_row([user_name, datetime.now().strftime("%Y-%m-%d %H:%M"), str(eff), str(def_s), str(coh), diag])
                st.balloons()

# --- 5. الإحصائيات (تظهر دائماً) ---
st.markdown("---")
df_all = load_history_data()
if not df_all.empty:
    ca, cb = st.columns([1.5, 1])
    with ca:
        st.subheader("📈 مسار تطورك")
        st.line_chart(df_all[df_all['Name'] == user_name].set_index('Date')['Score_Eff'])
    with cb:
        st.subheader("🏆 المتصدرون")
        st.table(df_all.groupby('Name')['Score_Eff'].max().sort_values(ascending=False).head(5))
