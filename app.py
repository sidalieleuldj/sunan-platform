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

# --- 2. التصميم (CSS) - الحل النهائي لمشكلة اللوحة ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* 1. إبقاء هيكل الصفحة LTR (لتثبيت اللوحة يساراً) */
    body {
        direction: ltr;
    }

    /* 2. تحويل النصوص والعناصر الداخلية فقط إلى RTL (للعربية) */
    .stMarkdown, .stTextInput, .stNumberInput, .stSelectbox, .stSlider, p, h1, h2, h3, h4, h5, .stAlert {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }

    /* 3. تنسيق خاص للقائمة الجانبية (محتواها عربي لكن مكانها يسار) */
    section[data-testid="stSidebar"] {
        text-align: right !important;
    }
    
    /* ضبط محاذاة العناوين داخل اللوحة */
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2 {
        direction: rtl !important;
        text-align: right !important;
    }

    /* 4. تنسيق مربعات الإدخال لتكتب من اليمين */
    input {
        direction: rtl !important;
        text-align: right !important;
    }

    /* 5. تنسيق الأزرار */
    .stButton>button {
        width: 100%;
        background-color: #1F618D;
        color: white;
        border-radius: 8px;
        font-family: 'Cairo', sans-serif;
    }
    
    /* تنسيق جدول البيانات */
    [data-testid="stDataFrame"] { direction: rtl; }
</style>
""", unsafe_allow_html=True)

# --- 3. الاتصال بقاعدة البيانات ---
def get_google_sheet():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_dict = st.secrets["service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        # 🚨 تأكد أن الـ ID هنا هو الصحيح لملفك
        sheet_id = "1uXX-R40l8JQrPX8lcAxWbzxeeSs8Q5zaMF_DZ-R8TmE" 
        return client.open_by_key(sheet_id).sheet1
    except:
        return None

# دالة الحفظ (مع الاسم)
def save_to_google_sheet(name, eff, def_score, coh, diagnosis):
    sheet = get_google_sheet()
    if sheet:
        try:
            # الترتيب: الاسم، التاريخ، الفعالية، المناعة، التماسك، التشخيص
            row = [name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), eff, def_score, coh, diagnosis]
            sheet.append_row(row)
            return True
        except: return False
    return False

# دالة جلب البيانات
def load_history_data():
    sheet = get_google_sheet()
    if sheet:
        try:
            data = sheet.get_all_records()
            return pd.DataFrame(data)
        except: pass
    return pd.DataFrame()

# --- 4. محرك السنن (المعادلة الموزونة) ---
def calculate_sunan_scores(data):
    # معادلة الفعالية (نظام الخصم)
    # النقاط = (الإنتاج * 80 + المشاريع * 20) * (الجودة / 5) - (ساعات التصفح * 3)
    raw_points = (data['production_ratio'] * 80) + (data['completed_projects'] * 20)
    quality_factor = data['quality_score'] / 5
    eff = (raw_points * quality_factor) - (data['daily_hours'] * 3) + 15
    eff = max(min(round(eff, 2), 100), 5)
    
    # المناعة
    total_actions = data['original_posts'] + data['replies'] + 0.1
    indep_ratio = data['original_posts'] / total_actions
    stability = data['emotional_stability'] / 10.0
    def_s = round(((data['original_posts'] / total_actions) * 60) + (stability * 40), 2)
    
    # التماسك
    coh = min(round((data['task_alignment'] * 10) * (1.2 if data['is_team'] else 1.0), 2), 100)
    
    # التشخيص
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
        diag = "🌟 حالة متوازنة (الاستواء الحضاري): استمر على هذا المنوال."
        acts = []
        
    return eff, def_s, coh, diag, acts

# --- 5. واجهة المستخدم ---
if 'res' not in st.session_state: st.session_state['res'] = None

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2331/2331718.png", width=60)
    st.header("🎛️ لوحة التحكم")
    
    # خانة الاسم
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
            
    # زر الحفظ
    if st.button("💾 تدوين النتيجة في السجل العام"):
        if user_name and user_name != "مبادر":
            if save_to_google_sheet(user_name, eff, def_s, coh, diag):
                st.balloons(); st.success(f"✅ تم تسجيل نتيجتك يا {user_name}!")
        else:
            st.error("⚠️ يرجى كتابة اسمك الحقيقي قبل الحفظ.")

st.markdown("---")

# --- 6. لوحة المتصدرين ---
st.header("🏆 لوحة الشرف (فرسان الحضارة)")
if st.button("🔄 تحديث القائمة"):
    df = load_history_data()
    if not df.empty:
        try:
            # نتوقع أسماء الأعمدة في جوجل شيت كالتالي: Name, Date, Score_Eff, Score_Def, Score_Coh, Diagnosis
            # إذا كانت الأسماء مختلفة قد لا يظهر الترتيب بدقة، لذا نعرض الجدول الخام احتياطياً
            
            # محاولة عرض الجدول
            st.dataframe(df.tail(10), use_container_width=True)
            
            # محاولة استخراج المتصدرين (إذا كانت الأعمدة موجودة)
            if 'Name' in df.columns and 'Score_Eff' in df.columns:
                leaderboard = df.groupby('Name')['Score_Eff'].max().sort_values(ascending=False).head(3)
                st.subheader("🥇 أعلى 3 رواد في الفعالية")
                c1, c2, c3 = st.columns(3)
                if len(leaderboard) > 0: c1.metric("المركز 1", leaderboard.index[0], f"{leaderboard.iloc[0]}%")
                if len(leaderboard) > 1: c2.metric("المركز 2", leaderboard.index[1], f"{leaderboard.iloc[1]}%")
                if len(leaderboard) > 2: c3.metric("المركز 3", leaderboard.index[2], f"{leaderboard.iloc[2]}%")
        except:
            st.warning("تم جلب البيانات، لكن يرجى التأكد من أسماء الأعمدة لظهور لوحة المتصدرين.")
            st.dataframe(df)
    else:
        st.info("السجل فارغ حالياً.")
