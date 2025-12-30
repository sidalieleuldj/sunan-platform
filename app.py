import streamlit as st
import pandas as pd
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

# --- 2. CSS لتحسين المظهر ودعم اللغة العربية ---
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
</style>
""", unsafe_allow_html=True)

# --- 3. الاتصال بقاعدة البيانات (Google Sheets) ---
def get_google_sheet():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        
        # جلب البيانات من Secrets
        creds_dict = dict(st.secrets["service_account"])
        # إصلاح مشكلة مفتاح التشفير في السيرفرات
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # معرف الجدول الخاص بك
        sheet_id = "1uXX-R40l8JQrPX8lcAxWbzxeeSs8Q5zaMF_DZ-R8TmE" 
        return client.open_by_key(sheet_id).sheet1
    except Exception as e:
        st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
        return None

def save_to_google_sheet(name, eff, def_score, coh, diagnosis):
    sheet = get_google_sheet()
    if sheet:
        try:
            row = [name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), str(eff), str(def_score), str(coh), diagnosis]
            sheet.append_row(row)
            return True
        except: return False
    return False

def smart_fix_score(val):
    try:
        s_val = str(val).replace(',', '.')
        score = float(s_val)
        if score > 100: score = score / 10
        return min(max(score, 0), 100)
    except: return 0.0

def load_history_data():
    sheet = get_google_sheet()
    if sheet:
        try:
            data = sheet.get_all_values()
            if len(data) <= 1: return pd.DataFrame() # فارغ أو يحتوي عناوين فقط
            
            df = pd.DataFrame(data[1:], columns=['Name', 'Date', 'Score_Eff', 'Score_Def', 'Score_Coh', 'Diagnosis'])
            
            # تنظيف وتحويل البيانات
            for col in ['Score_Eff', 'Score_Def', 'Score_Coh']:
                df[col] = df[col].apply(smart_fix_score)
            
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            return df.dropna(subset=['Name'])
        except Exception as e:
            st.error(f"خطأ أثناء تحميل البيانات: {e}")
    return pd.DataFrame()

# --- 4. محرك السنن (المنطق الحسابي) ---
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

# --- 5. واجهة المستخدم ---
if 'res' not in st.session_state: st.session_state['res'] = None

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2331/2331718.png", width=60)
    st.header("🎛️ لوحة التحكم")
    user_name = st.text_input("الاسم", "مبادر")
    st.markdown("---")
    with st.expander("⏱️ الفعالية", expanded=True):
        d_hours = st.slider("ساعات التصفح", 0.0, 16.0, 4.0)
        p_ratio = st.slider("نسبة الإنتاج", 0.0, 1.0, 0.2)
        projects = st.number_input("مشاريع", 0, 50, 0)
        quality = st.select_slider("الجودة", [1, 2, 3, 4, 5], value=3)
    with st.expander("🛡️ المناعة"):
        orig = st.number_input("بصمتك", 0, 50, 1)
        replies = st.number_input("ردود", 0, 100, 5)
        emotion = st.slider("الهدوء", 0, 10, 5)
    with st.expander("🤝 التماسك"):
        align = st.slider("وضوح الهدف", 0, 10, 5)
        team = st.checkbox("عمل جماعي")
    
    calc_btn = st.button("🔍 تحليل النتائج")

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
        fig = go.Figure(go.Scatterpolar(r=[eff, def_s, coh, eff], theta=['الفعالية', 'المناعة', 'التماسك', 'الفعالية'], fill='toself', line_color='#1F618D'))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), margin=dict(t=40, b=40))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.info(f"النتيجة: {user_name}\n\n{diag}")
        for a in acts: st.warning(f"💡 {a}")
    
    if st.button("💾 حفظ النتيجة في السجل"):
        if user_name != "مبادر":
            if save_to_google_sheet(user_name, eff, def_s, coh, diag):
                st.balloons()
                st.success("تم الحفظ بنجاح!")
            else: st.error("فشل الحفظ، تحقق من الاتصال.")
        else: st.error("يرجى إدخال اسمك أولاً")

# --- 6. عرض التاريخ والمتصدرين ---
st.markdown("---")
if user_name and user_name != "مبادر":
    st.header(f"📈 المسار التاريخي لـ {user_name}")
    df_h = load_history_data()
    if not df_h.empty:
        user_hist = df_h[df_h['Name'].str.strip() == user_name.strip()].sort_values('Date')
        if not user_hist.empty:
            fig_h = go.Figure()
            fig_h.add_trace(go.Scatter(x=user_hist['Date'], y=user_hist['Score_Eff'], name='الفعالية'))
            fig_h.add_trace(go.Scatter(x=user_hist['Date'], y=user_hist['Score_Def'], name='المناعة'))
            fig_h.update_layout(hovermode="x unified")
            st.plotly_chart(fig_h, use_container_width=True)
        else:
            st.info("لا يوجد سجل بيانات لهذا الاسم بعد.")

st.header("🏆 قائمة المتصدرين")
if st.button("تحديث القائمة"):
    df_top = load_history_data()
    if not df_top.empty:
        top = df_top.groupby('Name')['Score_Eff'].max().sort_values(ascending=False).head(5)
        st.table(top)
