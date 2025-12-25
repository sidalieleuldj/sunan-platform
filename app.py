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
    
    body, .main, .stMarkdown, p, h1, h2, h3, h4, h5, span, div {
        font-family: 'Cairo', sans-serif !important;
        text-align: right !important;
        direction: rtl !important;
    }
    section[data-testid="stSidebar"] {
        left: 0 !important;
        right: auto !important;
        text-align: right !important;
    }
    .stSlider, .stCheckbox, .stNumberInput, .stTextInput {
        direction: rtl !important;
        text-align: right !important;
    }
    .stButton>button {
        width: 100%;
        background-color: #1F618D;
        color: white;
        border-radius: 8px;
        border: none;
    }
    /* تنسيق خاص للوحة المتصدرين */
    div[data-testid="stMetricValue"] {
        font-size: 20px;
        color: #1F618D;
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

# تحديث دالة الحفظ لتشمل الاسم
def save_to_google_sheet(name, eff, def_score, coh, diagnosis):
    sheet = get_google_sheet()
    if sheet:
        try:
            # الترتيب الجديد: الاسم، التاريخ، الفعالية، المناعة، التماسك، التشخيص
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

# --- 4. محرك السنن (المحدث) ---
def calculate_sunan_scores(data):
    # معادلة الفعالية (نظام الخصم)
    raw_points = (data['production_ratio'] * 80) + (data['completed_projects'] * 20)
    quality_factor = data['quality_score'] / 5
    eff = (raw_points * quality_factor) - (data['daily_hours'] * 3) + 15
    eff = max(min(round(eff, 2), 100), 5)
    
    # المناعة
    total = data['original_posts'] + data['replies'] + 0.1
    def_s = round(((data['original_posts'] / total) * 60) + ((data['emotional_stability'] / 10) * 40), 2)
    
    # التماسك
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
        diag = "🌟 حالة متوازنة: استمر على هذا المنوال."
        acts = []
        
    return eff, def_s, coh, diag, acts

# --- 5. واجهة المستخدم ---
if 'res' not in st.session_state: st.session_state['res'] = None

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2331/2331718.png", width=60)
    st.header("🎛️ لوحة التحكم")
    
    # --- إضافة خانة الاسم ---
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
    # تمرير البيانات للحساب
    vals = {
        'daily_hours': d_hours, 'production_ratio': p_ratio, 'completed_projects': projects,
        'quality_score': quality, 'original_posts': orig, 'replies': replies,
        'emotional_stability': emotion, 'task_alignment': align, 'is_team': team
    }
    st.session_state['res'] = calculate_sunan_scores(vals)

# عرض النتائج
if st.session_state['res']:
    eff, def_s, coh, diag, acts = st.session_state['res']
    
    col_chart, col_info = st.columns([1.5, 1])
    with col_chart:
        fig = go.Figure(go.Scatterpolar(r=[eff, def_s, coh], theta=['الفعالية', 'المناعة', 'التماسك'], fill='toself', line_color='#1F618D'))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), margin=dict(t=40, b=40))
        st.plotly_chart(fig, use_container_width=True)
        
    with col_info:
        st.subheader(f"نتيجة الأخ/ت: {user_name}")
        st.info(diag)
        if acts:
            for a in acts: st.warning(f"💡 {a}")
            
    # زر الحفظ مع الاسم
    if st.button("💾 تدوين النتيجة في السجل العام"):
        if user_name and user_name != "مبادر":
            if save_to_google_sheet(user_name, eff, def_s, coh, diag):
                st.balloons(); st.success(f"✅ تم تسجيل نتيجتك يا {user_name}!")
        else:
            st.error("⚠️ يرجى كتابة اسمك الحقيقي قبل الحفظ.")

st.markdown("---")

# --- 6. لوحة المتصدرين (الجديد) ---
st.header("🏆 لوحة الشرف (فرسان الحضارة)")

if st.button("🔄 تحديث القائمة"):
    df = load_history_data()
    if not df.empty:
        # نفترض أن العمود الأول هو الاسم، والثالث هو الفعالية
        # ملاحظة: يعتمد هذا على أسماء الأعمدة في Google Sheet
        # يفضل أن تكون الأعمدة في الشيت: Name, Date, Efficiency, Immunity, Cohesion, Diagnosis
        try:
            # ترتيب حسب الفعالية (الأعلى فالأعلى)
            # نستخدم أسماء الأعمدة المتوقعة، إذا لم تكن موجودة نستخدم المؤشرات
            # هنا سنفترض أنك ستسمي الأعمدة في شيت جوجل كالتالي:
            # Name, Date, Score_Eff, Score_Def, Score_Coh, Diagnosis
            
            # للعرض المبسط سنأخذ آخر 5 مساهمات
            st.subheader("آخر المساهمات الموثقة")
            st.dataframe(df.tail(5), use_container_width=True)
            
            # محاولة صنع لوحة متصدرين
            if 'Score_Eff' in df.columns and 'Name' in df.columns:
                leaderboard = df.groupby('Name')['Score_Eff'].max().sort_values(ascending=False).head(3)
                st.subheader("🥇 أعلى 3 رواد في الفعالية")
                
                c1, c2, c3 = st.columns(3)
                if len(leaderboard) >= 1: c1.metric("المركز الأول", leaderboard.index[0], f"{leaderboard.iloc[0]}%")
                if len(leaderboard) >= 2: c2.metric("المركز الثاني", leaderboard.index[1], f"{leaderboard.iloc[1]}%")
                if len(leaderboard) >= 3: c3.metric("المركز الثالث", leaderboard.index[2], f"{leaderboard.iloc[2]}%")
                
        except Exception as e:
            st.warning("يرجى ضبط عناوين الأعمدة في Google Sheet لتكون (Name, Date, Score_Eff, Score_Def, Score_Coh, Diagnosis) لظهور الترتيب بدقة.")
            st.dataframe(df) # عرض الجدول كما هو احتياطياً
    else:
        st.info("لا توجد سجلات بعد.")
