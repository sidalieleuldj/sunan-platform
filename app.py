import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import google.generativeai as genai

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="منصة السُّنَن الرقمية",
    page_icon="🕌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. التصميم الجمالي (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; }
    .stApp { direction: ltr; }
    .stMarkdown, p, h1, h2, h3, h4, h5, span, div[data-testid="stMetricValue"], .stAlert, .stDataFrame {
        text-align: right !important; direction: rtl !important;
    }
    div[data-testid="stTable"] { direction: rtl; text-align: right; }
    .stButton>button { width: 100%; background-color: #1F618D; color: white; border-radius: 8px; font-weight: bold; }
    .ai-box { background-color: #f0f8ff; border-right: 5px solid #1F618D; padding: 20px; border-radius: 10px; margin-top: 20px; color: #000; text-align: right; }
</style>
""", unsafe_allow_html=True)

# --- 3. وظائف قاعدة البيانات ---
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

def load_history_data():
    sheet = get_google_sheet()
    if sheet:
        try:
            data = sheet.get_all_values()
            df = pd.DataFrame(data)
            if df.empty or len(df.columns) < 6: return pd.DataFrame()
            df = df.iloc[:, :6]
            df.columns = ['Name', 'Date', 'Score_Eff', 'Score_Def', 'Score_Coh', 'Diagnosis']
            df = df[df['Name'] != 'Name']
            for c in ['Score_Eff', 'Score_Def', 'Score_Coh']:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            return df
        except: return pd.DataFrame()
    return pd.DataFrame()

def save_to_google_sheet(name, eff, def_score, coh, diagnosis):
    sheet = get_google_sheet()
    if sheet:
        try:
            row = [name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), str(eff), str(def_score), str(coh), diagnosis]
            sheet.append_row(row)
            return True
        except: return False
    return False

# --- 4. المستشار الذكي (Gemini) ---
def get_ai_consultation(name, eff, def_s, coh, diag, history_df):
    try:
        api_key = st.secrets.get("gemini_key")
        if not api_key: return "⚠️ مفتاح AI مفقود."
        genai.configure(api_key=api_key)
        
        # جلب أول موديل متاح (تجنب خطأ 404)
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model = genai.GenerativeModel(available_models[0])
        
        hist_context = ""
        if not history_df.empty:
            user_hist = history_df[history_df['Name'].str.strip() == name.strip()].tail(3)
            if not user_hist.empty:
                hist_context = f"تاريخه القريب: {user_hist[['Date', 'Score_Eff']].to_string()}"

        prompt = f"أنت مستشار سنني خبير. حلل مسار {name}. النتائج: فعالية {eff}، مناعة {def_s}، تماسك {coh}. التشخيص: {diag}. {hist_context}. وجه له نصيحة حضارية في 3 أسطر."
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ تعذر الاتصال بالذكاء الاصطناعي: {str(e)}"

# --- 5. المحرك الحسابي ---
def calculate_sunan_scores(data):
    raw_points = (data['p_ratio'] * 80) + (data['projects'] * 20)
    eff = (raw_points * (data['quality']/5)) - (data['hours'] * 3) + 15
    eff = max(min(round(eff, 2), 100), 5)
    
    total = data['orig'] + data['replies'] + 0.1
    def_s = round(((data['orig'] / total) * 60) + ((data['emotion'] / 10) * 40), 2)
    coh = min(round((data['align'] * 10) * (1.2 if data['team'] else 1.0), 2), 100)
    
    if eff < 45: diag = "🛑 ركود حضاري"
    elif def_s < 45: diag = "⚠️ جهد مكشوف"
    elif coh < 45: diag = "🧩 تشتت الجهد"
    else: diag = "🌟 استواء حضاري"
    return eff, def_s, coh, diag

# --- 6. الواجهة البرمجية ---
df_history = load_history_data()

with st.sidebar:
    st.header("🎛️ لوحة التحكم")
    u_name = st.text_input("الاسم", "مبادر")
    st.markdown("---")
    with st.expander("⏱️ الفعالية", expanded=True):
        p_ratio = st.slider("نسبة الإنتاج", 0.0, 1.0, 0.5)
        hours = st.slider("ساعات الهدر", 0, 16, 4)
        projects = st.number_input("مشاريع", 0, 50, 1)
        quality = st.select_slider("الجودة", [1,2,3,4,5], 3)
    with st.expander("🛡️ المناعة"):
        orig = st.number_input("بصمة خاصة", 0, 100, 10)
        replies = st.number_input("ردود", 0, 100, 20)
        emotion = st.slider("هدوء", 0, 10, 5)
    with st.expander("🤝 التماسك"):
        align = st.slider("وضوح هدف", 0, 10, 5)
        team = st.checkbox("عمل جماعي")
    
    calc_btn = st.button("🔍 تحليل الموقف")

st.title("🕌 منصة السُّنَن الرقمية")

if 'res' not in st.session_state: st.session_state.res = None

if calc_btn:
    st.session_state.res = calculate_sunan_scores({
        'p_ratio':p_ratio, 'hours':hours, 'projects':projects, 'quality':quality,
        'orig':orig, 'replies':replies, 'emotion':emotion, 'align':align, 'team':team
    })

if st.session_state.res:
    eff, def_s, coh, diag = st.session_state.res
    c1, c2 = st.columns([1.5, 1])
    with c1:
        fig = go.Figure(go.Scatterpolar(r=[eff, def_s, coh], theta=['الفعالية','المناعة','التماسك'], fill='toself'))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.info(f"النتيجة الحالية: {diag}")
        if st.button("✨ استشارة المرشد السنني (AI)"):
            with st.spinner('جاري التحليل...'):
                advice = get_ai_consultation(u_name, eff, def_s, coh, diag, df_history)
                st.markdown(f'<div class="ai-box">{advice}</div>', unsafe_allow_html=True)
        if st.button("💾 حفظ النتيجة"):
            if save_to_google_sheet(u_name, eff, def_s, coh, diag):
                st.success("تم الحفظ!")
                st.rerun()

# --- 7. التاريخ ---
if not df_history.empty:
    user_data = df_history[df_history['Name'].str.strip() == u_name.strip()]
    if not user_data.empty:
        st.divider()
        st.subheader(f"📈 المسار التاريخي لـ {u_name}")
        user_data['Date'] = pd.to_datetime(user_data['Date'])
        st.line_chart(user_data.set_index('Date')[['Score_Eff', 'Score_Def', 'Score_Coh']])
