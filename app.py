import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import google.generativeai as genai

# --- 1. إعدادات الصفحة والذكاء الاصطناعي ---
st.set_page_config(page_title="منصة السُّنَن الرقمية", page_icon="🕌", layout="wide")

# إعداد Gemini API باستخدام المفتاح من Secrets
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

# --- 2. التصميم الشامل (CSS) - النسخة الأصلية المطورة (السلايدر محمي) ---
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
    
    /* تصميم السلايدر المطور (الأخضر والذهبي) - ثابت ومحمي */
    div[data-baseweb="slider"] > div:first-child > div:first-child {
        background: linear-gradient(90deg, #c9a44c 0%, #1e5631 100%) !important;
        height: 10px !important;
    }
    div[role="slider"] {
        background-color: #1e5631 !important;
        border: 3px solid #c9a44c !important;
        height: 22px !important;
        width: 22px !important;
    }
    .stSlider label { color: #1e5631 !important; font-weight: bold; font-size: 1.1em; }

    /* الأزرار العصرية */
    .stButton>button {
        background: linear-gradient(135deg, #1e5631 0%, #2d8a4e 100%) !important;
        color: white !important; border-radius: 12px !important; border: none !important;
        padding: 15px 30px !important; font-weight: 900 !important; transition: 0.3s;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(30, 86, 49, 0.4); }

    /* صناديق التقرير والتحدي */
    .ai-response-box {
        background: white; border-right: 10px solid #c9a44c; border-radius: 20px;
        padding: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); margin-top: 20px;
    }
    .challenge-box {
        background-color: #fcf3cf; border-radius: 15px; padding: 20px;
        border: 2px solid #c9a44c; margin-top: 20px; color: #1b4f72;
    }
    .task-item { background: rgba(255,255,255,0.7); padding: 10px; border-radius: 8px; margin-bottom: 8px; border-right: 5px solid #1e5631; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 3. الدوال البرمجية (الربط بجوجل شيت) ---
def get_google_sheet():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        # قراءة البيانات مباشرة من هيكل السيكرت الخاص بك
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
        # تأكد من أن ID الملف صحيح
        return client.open_by_key("1uXX-R40l8JQrPX8lcAxWbzxeeSs8Q5zaMF_DZ-R8TmE").sheet1
    except Exception as e:
        st.sidebar.error(f"خطأ في الاتصال بجوجل شيت: {e}")
        return None

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

# دالة Gemini الذكية
def get_gemini_report(user_name, diag, eff, def_s, coh):
    if model:
        prompt = f"""أنت مستشار رقمي. المستخدم {user_name} لديه تشخيص {diag}. 
        النتائج: فعالية {eff}%، مناعة {def_s}%، تماسك {coh}%. 
        قدم تحليلاً ملهماً في فقرة، ثم تحدي من 4 نقاط للأربع أسابيع القادمة باللغة العربية الفصحى."""
        try:
            response = model.generate_content(prompt)
            return response.text
        except: pass
    return f"🤖 التقرير: حالتك هي {diag}. فعاليتك المرتفعة ({eff}%) تدل على زخم جيد."

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
if 'res' not in st.session_state: st.session_state['res'] = None

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2331/2331718.png", width=80)
    st.header("🎛️ المدخلات")
    user_name = st.text_input("اسم المستخدم", "مبادر")
    st.markdown("---")
    with st.expander("⏱️ الفعالية", expanded=True):
        d_hours = st.slider("ساعات التصفح", 0.0, 16.0, 4.0)
        p_ratio = st.slider("نسبة الإنتاج", 0.0, 1.0, 0.2)
        projects = st.number_input("مشاريع منجزة", 0, 50, 0)
        quality = st.select_slider("جودة المخرج", [1, 2, 3, 4, 5], value=3)
    with st.expander("🛡️ المناعة"):
        orig = st.number_input("بصمة أصلية", 0, 50, 1)
        replies = st.number_input("ردود", 0, 100, 5)
        emotion = st.slider("الاتزان", 0, 10, 5)
    with st.expander("🤝 التماسك"):
        align = st.slider("وضوح الغاية", 0, 10, 5)
        team = st.checkbox("عمل جماعي")
    calc_btn = st.button("🚀 تحليل واستشارة Gemini")

st.title("🕌 منصة السُّنَن الرقمية")

if calc_btn:
    vals = {'hours': d_hours, 'p_ratio': p_ratio, 'projects': projects, 'quality': quality, 'orig': orig, 'replies': replies, 'emotion': emotion, 'align': align, 'team': team}
    st.session_state['res'] = calculate_scores(vals)

if st.session_state['res']:
    eff, def_s, coh, diag = st.session_state['res']
    with st.spinner('يتم الآن استشارة Gemini 1.5...'):
        report = get_gemini_report(user_name, diag, eff, def_s, coh)
    
    # عرض تقرير Gemini
    st.markdown(f'<div class="ai-response-box"><h3>🤖 التقرير الحضاري (Gemini AI)</h3>{report}</div>', unsafe_allow_html=True)
    
    col_main, col_data = st.columns([1.5, 1])
    with col_main:
        fig = go.Figure(go.Scatterpolar(r=[eff, def_s, coh, eff], theta=['الفعالية', 'المناعة', 'التماسك', 'الفعالية'], fill='toself', fillcolor='rgba(30, 86, 49, 0.2)', line=dict(color='#c9a44c', width=4)))
        st.plotly_chart(fig, use_container_width=True)
    with col_data:
        st.success(f"الاسم: {user_name} | التشخيص: {diag}")
        if st.button("💾 حفظ النتيجة"):
            sheet = get_google_sheet()
            if sheet:
                sheet.append_row([user_name, datetime.now().strftime("%Y-%m-%d %H:%M"), str(eff), str(def_s), str(coh), diag])
                st.balloons(); st.success("تم الحفظ!")

# --- 5. الإحصائيات التاريخية ---
st.markdown("---")
df_all = load_history_data()
if not df_all.empty:
    ca, cb = st.columns([1.5, 1])
    with ca:
        st.subheader("📈 مسار التطور")
        u_df = df_all[df_all['Name'] == user_name].sort_values('Date')
        if not u_df.empty: st.line_chart(u_df.set_index('Date')['Score_Eff'])
    with cb:
        st.subheader("🏆 المتصدرون")
        st.table(df_all.groupby('Name')['Score_Eff'].max().sort_values(ascending=False).head(5))
