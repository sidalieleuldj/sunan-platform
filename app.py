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

# --- 2. التصميم (CSS) - الحل النهائي الشامل ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* 1. جعل الهيكل العام LTR لتثبيت اللوحة يساراً ومنع الأخطاء */
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
    }
    
    /* 2. تحويل النصوص والعناصر الداخلية للعربية (يمين) */
    .stMarkdown, .stTextInput > label, .stNumberInput > label, .stSelectbox > label, p, h1, h2, h3, h4, h5 {
        text-align: right !important;
        direction: rtl !important;
    }

    /* 3. إصلاح مشكلة الأرقام الطائرة في السلايدر */
    div[data-testid="stSlider"] {
        direction: ltr !important; /* الشريط يبقى يسار */
    }
    div[data-testid="stSlider"] > label {
        text-align: right !important; /* العنوان يذهب يمين */
        direction: rtl !important;
        width: 100%;
        display: block;
    }
    
    /* 4. تثبيت القائمة الجانبية في اليسار مع محتوى عربي */
    section[data-testid="stSidebar"] {
        left: 0 !important;
        right: auto !important;
    }
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] h1 {
        text-align: right !important;
    }

    /* 5. تنسيق الأزرار وحقول الإدخال */
    .stButton>button {
        width: 100%;
        background-color: #1F618D;
        color: white;
        border-radius: 8px;
    }
    input {
        text-align: right !important;
        direction: rtl !important;
    }
    
    /* 6. تحسين التنبيهات */
    .stAlert {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* 7. تنسيق الجدول */
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
        # 🚨 تأكد من الـ ID الصحيح
        sheet_id = "1uXX-R40l8JQrPX8lcAxWbzxeeSs8Q5zaMF_DZ-R8TmE" 
        return client.open_by_key(sheet_id).sheet1
    except:
        return None

def save_to_google_sheet(name, eff, def_score, coh, diagnosis):
    sheet = get_google_sheet()
    if sheet:
        try:
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

# --- 4. محرك السنن ---
def calculate_sunan_scores(data):
    # 1. حساب الفعالية (نظام المكافأة والخصم)
    # نجمع نقاط الإنتاج والمشاريع أولاً
    raw_points = (data['production_ratio'] * 80) + (data['completed_projects'] * 20)
    
    # نضربها في الجودة (الجودة السيئة تقلل النقاط، الجيدة ترفعها)
    quality_factor = data['quality_score'] / 5
    gained_score = raw_points * quality_factor
    
    # نخصم "ضريبة الوقت": كل ساعة تكلفك 3 نقاط فقط بدلاً من القسمة عليها
    time_tax = data['daily_hours'] * 3
    
    eff = gained_score - time_tax + 15 # +15 رصيد افتتاحي للتشجيع
    eff = max(min(round(eff, 2), 100), 5) # ضمان أن الرقم بين 5 و 100

    # 2. حساب المناعة (كما هي)
    total_actions = data['original_posts'] + data['replies'] + 0.1
    indep_ratio = data['original_posts'] / total_actions
    stability = data['emotional_stability'] / 10.0
    def_ = round((indep_ratio * 60) + (stability * 40), 2)
    
    # 3. حساب التماسك (كما هي)
    base = data['task_alignment'] * 10
    mult = 1.2 if data['is_team'] else 1.0
    coh = min(round(base * mult, 2), 100)
    
    # التشخيص (التسلسل الهرمي)
    if eff < 45:
        diag = "🛑 ركود حضاري: تستهلك أكثر مما تنتج."
        actions = ["خصص ساعة للعمل العميق.", "قلل ساعات التصفح."]
    elif def_ < 45:
        diag = "⚠️ جهد مكشوف: إنتاجك عالٍ لكنك مستنزف في معارك جانبية."
        actions = ["توقف عن الردود تماماً اليوم.", "ركز على البناء لا الجدال."]
    elif coh < 45:
        diag = "🧩 تشتت الجهد: أنت ذرة قوية لكنك تعمل وحيداً."
        actions = ["ابحث عن شريك.", "اربط عملك بهدف أكبر."]
   else : 
        # --- التحديث الجديد (الحالة المتوازنة) ---
        diag = "🌟 حالة متوازنة (الاستواء الحضاري): أنت الآن في مرحلة العطاء."
        acts = [
            "زكاة العلم تعليمه: تبنَّ شخصاً مبتدئاً ووجهه.",
            "وثّق تجربتك: اكتب كيف تغلبت على المشتتات لتلهم غيرك."
        ]
        
    return eff, def_s, coh, diag, acts
# --- 5. واجهة المستخدم ---
if 'res' not in st.session_state: st.session_state['res'] = None

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2331/2331718.png", width=60)
    st.header("🎛️ لوحة التحكم")
    
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
        st.subheader(f"نتيجة: {user_name}")
        st.info(diag)
        # --- ✅ هنا كان الخطأ وتم إصلاحه ---
        if acts:
            for a in acts: st.warning(f"💡 {a}")
            
    if st.button("💾 تدوين النتيجة"):
        if user_name and user_name != "مبادر":
            if save_to_google_sheet(user_name, eff, def_s, coh, diag):
                st.balloons(); st.success(f"تم التسجيل لـ {user_name}")
        else:
            st.error("يرجى كتابة الاسم.")

st.markdown("---")

# --- 6. لوحة المتصدرين ---
st.header("🏆 لوحة الشرف")
if st.button("🔄 تحديث القائمة"):
    df = load_history_data()
    if not df.empty:
        try:
            st.dataframe(df.tail(5), use_container_width=True)
            if 'Name' in df.columns and 'Score_Eff' in df.columns:
                leaderboard = df.groupby('Name')['Score_Eff'].max().sort_values(ascending=False).head(3)
                c1, c2, c3 = st.columns(3)
                if len(leaderboard) > 0: c1.metric("الأول", leaderboard.index[0], f"{leaderboard.iloc[0]}%")
                if len(leaderboard) > 1: c2.metric("الثاني", leaderboard.index[1], f"{leaderboard.iloc[1]}%")
                if len(leaderboard) > 2: c3.metric("الثالث", leaderboard.index[2], f"{leaderboard.iloc[2]}%")
        except:
            st.warning("تأكد من وجود الأعمدة (Name, Score_Eff) في ملف البيانات.")
            st.dataframe(df)





