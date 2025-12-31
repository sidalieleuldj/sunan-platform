import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="منصة السُّنَن الرقمية", page_icon="🕌", layout="wide")

# --- 2. التصميم (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .stApp { direction: ltr; }
    
    /* صندوق التحدي الذهبي */
    .challenge-box {
        background-color: #fcf3cf; 
        border-right: 10px solid #c9a44c;
        padding: 20px;
        border-radius: 15px;
        margin-top: 20px;
        color: #1b4f72;
    }
    .task-item { margin-bottom: 10px; font-weight: bold; border-bottom: 1px solid #d4ac0d; padding-bottom: 5px; }
    
    .stButton>button {
        background: linear-gradient(135deg, #1e5631 0%, #2d8a4e 100%) !important;
        color: white !important; border-radius: 10px !important; width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. الدوال البرمجية ---
def get_google_sheet():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_info = dict(st.secrets["service_account"])
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
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

def calculate_sunan_scores(data):
    raw_points = (data['production_ratio'] * 80) + (data['completed_projects'] * 20)
    eff = (raw_points * (data['quality_score'] / 5)) - (data['daily_hours'] * 3) + 15
    eff = max(min(round(eff, 2), 100), 5)
    total = data['original_posts'] + data['replies'] + 0.1
    def_s = round(((data['original_posts'] / total) * 60) + ((data['emotional_stability'] / 10) * 40), 2)
    coh = min(round((data['task_alignment'] * 10) * (1.2 if data['is_team'] else 1.0), 2), 100)
    
    if eff < 45: diag = "🛑 ركود حضاري"
    elif def_s < 45: diag = "⚠️ جهد مكشوف"
    elif coh < 45: diag = "🧩 تشتت الجهد"
    else: diag = "🌟 استواء حضاري"
    return eff, def_s, coh, diag

# --- 4. القائمة الجانبية ---
with st.sidebar:
    st.header("🎛️ المدخلات")
    user_name = st.text_input("اسم المستخدم", "مبادر")
    d_hours = st.slider("ساعات التصفح", 0.0, 16.0, 4.0)
    p_ratio = st.slider("نسبة الإنتاج", 0.0, 1.0, 0.2)
    projects = st.number_input("مشاريع منجزة", 0, 50, 0)
    quality = st.select_slider("جودة المخرج", [1, 2, 3, 4, 5], value=3)
    orig = st.number_input("منشورات أصلية", 0, 50, 1)
    replies = st.number_input("ردود", 0, 100, 5)
    emotion = st.slider("الاتزان", 0, 10, 5)
    align = st.slider("وضوح الغاية", 0, 10, 5)
    team = st.checkbox("عمل جماعي")
    calc_btn = st.button("🔍 تحليل وبناء التحدي")

st.title("🕌 منصة السُّنَن الرقمية")

# --- 5. العرض الرئيسي (هنا يظهر كل شيء) ---
if calc_btn:
    # 1. الحساب
    vals = {'daily_hours': d_hours, 'production_ratio': p_ratio, 'completed_projects': projects,
            'quality_score': quality, 'original_posts': orig, 'replies': replies,
            'emotional_stability': emotion, 'task_alignment': align, 'is_team': team}
    eff, def_s, coh, diag = calculate_sunan_scores(vals)
    
    # 2. تقسيم الصفحة للعرض
    col_g, col_t = st.columns([1.5, 1])
    
    with col_g:
        # الرسم البياني
        fig = go.Figure(go.Scatterpolar(r=[eff, def_s, coh, eff], theta=['الفعالية', 'المناعة', 'التماسك', 'الفعالية'], fill='toself', fillcolor='rgba(45, 138, 78, 0.2)', line=dict(color='#c9a44c', width=4)))
        st.plotly_chart(fig, use_container_width=True)
        
        # صندوق التحدي (The Action Plan)
        st.markdown(f"""
        <div class="challenge-box">
            <h3>🚀 تحدي الـ 30 يوماً لرفع مستوى: {diag}</h3>
            <div class="task-item">📅 الأسبوع 1: ركز على تقليل المشتتات بنسبة 30%.</div>
            <div class="task-item">📅 الأسبوع 2: ابدأ بإنتاج محتوى أصلي واحد يومياً.</div>
            <div class="task-item">📅 الأسبوع 3: اربط أعمالك بهدفك الاستراتيجي.</div>
            <div class="task-item">📅 الأسبوع 4: شارك تجربتك ووثق تقدمك.</div>
        </div>
        """, unsafe_allow_html=True)

    with col_t:
        st.success(f"المبادر: {user_name}")
        st.info(f"التشخيص الحالي: {diag}")
        
        if st.button("💾 حفظ النتيجة"):
            sheet = get_google_sheet()
            if sheet:
                sheet.append_row([user_name, datetime.now().strftime("%Y-%m-%d %H:%M"), str(eff), str(def_s), str(coh), diag])
                st.balloons()

# --- 6. الإحصائيات التاريخية (دائماً ظاهرة) ---
st.markdown("---")
df_all = load_history_data()
if not df_all.empty:
    c_a, c_b = st.columns(2)
    with c_a:
        st.subheader("🏆 المتصدرون")
        st.table(df_all.groupby('Name')['Score_Eff'].max().sort_values(ascending=False).head(5))
    with c_b:
        st.subheader("📈 سجل أداءك")
        u_df = df_all[df_all['Name'] == user_name]
        if not u_df.empty: st.line_chart(u_df.set_index('Date')['Score_Eff'])
