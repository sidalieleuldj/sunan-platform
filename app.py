import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import google.generativeai as genai

# --- 1. إعدادات الصفحة والتصميم ---
st.set_page_config(page_title="منصة السُّنَن الرقمية", page_icon="🕌", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .stApp { direction: ltr; }
    .stMarkdown, p, h1, h2, h3, h4, h5, div[data-testid="stMetricValue"] { text-align: right !important; direction: rtl !important; }
    .ai-box { background-color: #f0f8ff; border-right: 5px solid #1F618D; padding: 20px; border-radius: 10px; color: #000; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 2. وظائف قاعدة البيانات ---
def get_google_sheet():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_dict = st.secrets["service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        # تأكد من أن هذا الـ ID هو الصحيح لملفك
        return client.open_by_key("1uXX-R40l8JQrPX8lcAxWbzxeeSs8Q5zaMF_DZ-R8TmE").sheet1
    except: return None

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

def save_to_google_sheet(name, eff, def_score, coh, diagnosis):
    sheet = get_google_sheet()
    if sheet:
        try:
            row = [name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), str(eff), str(def_score), str(coh), diagnosis]
            sheet.append_row(row)
            return True
        except: return False
    return False

# --- 3. المستشار الذكي ---
def get_ai_consultation(name, eff, def_s, coh, diag, history_df):
    try:
        api_key = st.secrets.get("gemini_key")
        genai.configure(api_key=api_key)
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model = genai.GenerativeModel(available_models[0])
        
        hist_text = ""
        if not history_df.empty:
            user_hist = history_df[history_df['Name'].str.strip() == name.strip()].tail(3)
            hist_text = f"سجله السابق: {user_hist[['Date', 'Score_Eff']].to_string()}"

        prompt = f"أنت مستشار سنني. حلل مسار {name}. النتائج: فعالية {eff}، مناعة {def_s}، تماسك {coh}. التشخيص: {diag}. {hist_text}. قدم نصيحة في 3 أسطر."
        return model.generate_content(prompt).text
    except: return "🤖 عذراً، تعذر جلب النصيحة حالياً."

# --- 4. المحرك الحسابي ---
def calculate_sunan_scores(data):
    eff = max(min(round((data['p_ratio'] * 80) + (data['projects'] * 5) - (data['hours'] * 2), 2), 100), 5)
    def_s = round(((data['orig'] / (data['orig'] + data['replies'] + 0.1)) * 60) + (data['emotion'] * 4), 2)
    coh = min(round(data['align'] * 10 * (1.2 if data['team'] else 1.0), 2), 100)
    
    if eff < 45: diag = "🛑 ركود حضاري"
    elif def_s < 45: diag = "⚠️ جهد مكشوف"
    elif coh < 45: diag = "🧩 تشتت الجهد"
    else: diag = "🌟 استواء حضاري"
    return eff, def_s, coh, diag

# --- 5. الواجهة الرئيسية ---
st.title("🕌 منصة السُّنَن الرقمية")
df_history = load_history_data()

with st.sidebar:
    st.header("🎛️ المدخلات")
    u_name = st.text_input("اسم المبادرة/المبادر", "مبادر")
    p_ratio = st.slider("نسبة الإنتاج", 0.0, 1.0, 0.5)
    hours = st.slider("ساعات الهدر", 0, 16, 4)
    projects = st.number_input("مشاريع منجزة", 0, 10, 1)
    orig = st.number_input("بصمة خاصة (تغريدات/منشورات أصيلة)", 0, 100, 10)
    replies = st.number_input("ردود وتفاعل", 0, 100, 20)
    emotion = st.slider("استقرار نفسي/هدوء", 0, 10, 5)
    align = st.slider("وضوح الهدف", 0, 10, 5)
    team = st.checkbox("عمل ضمن فريق")
    calc_btn = st.button("🔍 تحليل النتائج")

# حفظ النتائج في Session State لتبقى ظاهرة
if 'current_res' not in st.session_state: st.session_state.current_res = None

if calc_btn:
    st.session_state.current_res = calculate_sunan_scores({
        'p_ratio':p_ratio, 'hours':hours, 'projects':projects, 
        'orig':orig, 'replies':replies, 'emotion':emotion, 
        'align':align, 'team':team
    })

if st.session_state.current_res:
    eff, def_s, coh, diag = st.session_state.current_res
    
    col1, col2 = st.columns([1.5, 1])
    with col1:
        fig = go.Figure(go.Scatterpolar(r=[eff, def_s, coh], theta=['الفعالية','المناعة','التماسك'], fill='toself'))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader(f"التشخيص: {diag}")
        st.metric("مستوى الفعالية", f"{eff}%")
        
        # أزرار الإجراءات
        if st.button("✨ استشارة المرشد الذكي (AI)"):
            advice = get_ai_consultation(u_name, eff, def_s, coh, diag, df_history)
            st.markdown(f'<div class="ai-box">{advice}</div>', unsafe_allow_html=True)
            
        if st.button("💾 حفظ النتيجة في السجل"):
            if save_to_google_sheet(u_name, eff, def_s, coh, diag):
                st.success("✅ تم الحفظ بنجاح!")
                st.rerun()

# --- 6. عرض النتائج التاريخية (التي كانت مختفية) ---
st.divider()
c_hist, c_top = st.columns([2, 1])

with c_hist:
    st.subheader("📈 المسار الزمني")
    if not df_history.empty:
        u_data = df_history[df_history['Name'].str.strip() == u_name.strip()]
        if not u_data.empty:
            u_data['Date'] = pd.to_datetime(u_data['Date'])
            st.line_chart(u_data.set_index('Date')[['Score_Eff', 'Score_Def', 'Score_Coh']])
        else:
            st.info("لا توجد بيانات سابقة لهذا الاسم.")
    else:
        st.warning("قاعدة البيانات فارغة حالياً.")

with c_top:
    st.subheader("🏆 لوحة المتصدرين")
    if not df_history.empty:
        top_scores = df_history.groupby('Name')['Score_Eff'].max().sort_values(ascending=False).head(5)
        st.table(top_scores)
