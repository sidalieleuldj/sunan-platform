import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import google.generativeai as genai

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="منصة السُّنَن الرقمية", page_icon="🕌", layout="wide")

# --- 2. التصميم (CSS) لضمان ظهور الأقسام والخطوط ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .stApp { direction: ltr; }
    .stMarkdown, p, h1, h2, h3, h4, h5, div[data-testid="stMetricValue"], .stAlert { text-align: right !important; direction: rtl !important; }
    .ai-box { background-color: #f0f8ff; border-right: 5px solid #1F618D; padding: 20px; border-radius: 10px; color: #000; margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #1F618D; color: white; }
</style>
""", unsafe_allow_html=True)

# --- 3. وظائف البيانات ---
def get_google_sheet():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_dict = st.secrets["service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        return client.open_by_key("1uXX-R40l8JQrPX8lcAxWbzxeeSs8Q5zaMF_DZ-R8TmE").sheet1
    except: return None

@st.cache_data(ttl=60)
def load_history_data():
    sheet = get_google_sheet()
    if sheet:
        try:
            data = sheet.get_all_values()
            if len(data) < 2: return pd.DataFrame()
            df = pd.DataFrame(data[1:], columns=['Name', 'Date', 'Score_Eff', 'Score_Def', 'Score_Coh', 'Diagnosis'])
            for c in ['Score_Eff', 'Score_Def', 'Score_Coh']:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            return df
        except: return pd.DataFrame()
    return pd.DataFrame()

# --- 4. المحرك الحسابي ---
def calculate_sunan_scores(data):
    eff = max(min(round((data['p_ratio'] * 70) + (data['projects'] * 15) - (data['hours'] * 2) + (data['quality'] * 3), 2), 100), 5)
    total_inter = data['orig'] + data['replies'] + 0.1
    def_s = round(((data['orig'] / total_inter) * 60) + (data['emotion'] * 4), 2)
    coh = min(round(data['align'] * 10 * (1.2 if data['team'] else 1.0), 2), 100)
    
    if eff < 45: diag = "🛑 ركود حضاري"
    elif def_s < 45: diag = "⚠️ جهد مكشوف"
    elif coh < 45: diag = "🧩 تشتت الجهد"
    else: diag = "🌟 استواء حضاري"
    return eff, def_s, coh, diag

# --- 5. المستشار الذكي ---
def get_ai_consultation(name, eff, def_s, coh, diag, history_df):
    try:
        api_key = st.secrets.get("gemini_key")
        genai.configure(api_key=api_key)
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model = genai.GenerativeModel(models[0])
        
        hist_context = "لا توجد بيانات سابقة."
        if not history_df.empty:
            user_hist = history_df[history_df['Name'].str.strip() == name.strip()].tail(3)
            if not user_hist.empty:
                hist_context = f"نتائجه السابقة: {user_hist[['Date', 'Score_Eff']].to_string()}"

        prompt = f"أنت مستشار سنني. حلل مسار {name}. النتائج: فعالية {eff}%، مناعة {def_s}%، تماسك {coh}%. التشخيص: {diag}. {hist_context}. وجه نصيحة حضارية في 3 أسطر."
        return model.generate_content(prompt).text
    except: return "🤖 تعذر جلب البصيرة حالياً."

# --- 6. الواجهة البرمجية ---
df_history = load_history_data()

with st.sidebar:
    st.header("🎛️ لوحة القياس")
    u_name = st.text_input("الاسم", "مبادر")
    
    st.subheader("⏱️ الفعالية")
    p_ratio = st.slider("الإنتاجية", 0.0, 1.0, 0.5)
    projects = st.number_input("مشاريع", 0, 10, 1)
    hours = st.slider("هدر الوقت", 0, 16, 4)
    quality = st.select_slider("الجودة", [1,2,3,4,5], 3)
    
    st.subheader("🛡️ المناعة")
    orig = st.number_input("أصالة", 0, 100, 10)
    replies = st.number_input("تفاعل", 0, 100, 20)
    emotion = st.slider("ثبات", 0, 10, 5)
    
    st.subheader("🤝 التماسك")
    align = st.slider("وضوح هدف", 0, 10, 5)
    team = st.checkbox("فريق")
    
    analyze_btn = st.button("🔍 تحليل الموقف")

st.title("🕌 منصة السُّنَن الرقمية")

if 'res' not in st.session_state: st.session_state.res = None

if analyze_btn:
    st.session_state.res = calculate_sunan_scores({
        'p_ratio':p_ratio, 'projects':projects, 'hours':hours, 'quality':quality,
        'orig':orig, 'replies':replies, 'emotion':emotion, 'align':align, 'team':team
    })

if st.session_state.res:
    eff, def_s, coh, diag = st.session_state.res
    col1, col2 = st.columns([1.5, 1])
    with col1:
        fig = go.Figure(go.Scatterpolar(r=[eff, def_s, coh], theta=['الفعالية','المناعة','التماسك'], fill='toself'))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.success(f"التشخيص: {diag}")
        if st.button("✨ استشارة الذكاء الاصطناعي"):
            advice = get_ai_consultation(u_name, eff, def_s, coh, diag, df_history)
            st.markdown(f'<div class="ai-box">{advice}</div>', unsafe_allow_html=True)
        
        if st.button("💾 حفظ النتيجة"):
            sheet = get_google_sheet()
            if sheet:
                row = [u_name, datetime.now().strftime("%Y-%m-%d %H:%M"), str(eff), str(def_s), str(coh), diag]
                sheet.append_row(row)
                st.success("تم الحفظ!")
                st.cache_data.clear()

# --- 7. التاريخ والمتصدرون ---
st.divider()
t1, t2 = st.tabs(["📈 المسار التاريخي", "🏆 المتصدرون"])
with t1:
    if not df_history.empty:
        user_data = df_history[df_history['Name'].str.strip() == u_name.strip()]
        if not user_data.empty:
            user_data['Date'] = pd.to_datetime(user_data['Date'])
            st.line_chart(user_data.set_index('Date')[['Score_Eff', 'Score_Def', 'Score_Coh']])
with t2:
    if not df_history.empty:
        st.table(df_history.groupby('Name')['Score_Eff'].max().sort_values(ascending=False).head(10))
