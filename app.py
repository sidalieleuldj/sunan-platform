import streamlit as st
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

# --- 2. دالة الاتصال بقاعدة البيانات (Google Sheets) ---
def save_to_google_sheet(eff, def_score, coh, diagnosis):
    try:
        # تعريف النطاق والصلاحيات
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        # استدعاء المفاتيح من خزنة Secrets
        creds_dict = st.secrets["service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # فتح الملف (تأكد أن الاسم يطابق اسم ملفك في جوجل شيت)
        sheet = client.open("sunan_db").sheet1
        
        # تجهيز الصف الجديد (التاريخ + النتائج)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [current_time, eff, def_score, coh, diagnosis]
        
        # إضافة الصف
        sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
        return False

# --- 3. التصميم (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Cairo', sans-serif; }
    .stSidebar [data-testid="stMarkdownContainer"] { direction: rtl; text-align: right; }
    .stMarkdown { direction: rtl; text-align: right; }
    h1, h2, h3 { text-align: right; font-family: 'Cairo', sans-serif; color: #1F618D; }
    .stButton>button { width: 100%; background-color: #1F618D; color: white; border-radius: 8px; font-weight: bold; }
    .stSlider [data-testid="stMarkdownContainer"] p { font-size: 16px; direction: rtl; }
</style>
""", unsafe_allow_html=True)

# --- 4. محرك السنن ---
def calculate_sunan_scores(data):
    ratio_cons = 1.0 - data['production_ratio']
    numerator = (data['completed_projects'] * 10) + (data['production_ratio'] * 100 * (data['quality_score']/5))
    denominator = (data['daily_hours'] * ratio_cons * 5) + 0.001
    eff = min(round(numerator / denominator * 10, 2), 100)
    
    total_actions = data['original_posts'] + data['replies'] + 0.001
    indep_ratio = data['original_posts'] / total_actions
    stability = data['emotional_stability'] / 10.0
    def_ = round((indep_ratio * 60) + (stability * 40), 2)
    
    base = data['task_alignment'] * 10
    mult = 1.2 if data['is_team'] else 1.0
    coh = min(round(base * mult, 2), 100)
    
    diag = "🌟 حالة متوازنة: تسير وفق السنن."
    actions = []
    if eff < 40: 
        diag = "🛑 ركود حضاري: تستهلك أكثر مما تنتج."
        actions.append("خصص ساعة يومياً للعمل العميق.")
    elif def_ < 40:
        diag = "⚠️ جهد مكشوف: طاقتك مهدورة."
        actions.append("صيام عن الجدل لمدة 3 أيام.")
    elif coh < 40:
        diag = "🧩 تشتت الجهد: عمل فردي."
        actions.append("ابحث عن شريك.")
        
    return eff, def_, coh, diag, actions

# --- 5. واجهة المستخدم ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2331/2331718.png", width=60)
    st.header("🎛️ لوحة التحكم")
    with st.expander("⏱️ 1. محور الفعالية", expanded=True):
        d_hours = st.slider("ساعات التصفح", 0.0, 16.0, 4.0)
        p_ratio = st.slider("نسبة الإنتاج", 0.0, 1.0, 0.1)
        projects = st.number_input("مشاريع منجزة", 0, 50, 0)
        quality = st.select_slider("جودة الأثر", options=[1, 2, 3, 4, 5], value=3)
    with st.expander("🛡️ 2. محور المناعة"):
        orig = st.number_input("منشورات أصلية", 0, 50, 1)
        replies = st.number_input("ردود وتعليقات", 0, 100, 10)
        emotion = st.slider("الهدوء النفسي", 0, 10, 5)
    with st.expander("🤝 3. محور التماسك"):
        align = st.slider("توافق مع الهدف", 0, 10, 5)
        team = st.checkbox("أعمل ضمن فريق", value=False)
    st.markdown("---")
    calc_btn = st.button("🔍 تحليل الموقف")

st.title("منصة السُّنَن الرقمية")

if 'result_saved' not in st.session_state:
    st.session_state.result_saved = False

if calc_btn:
    st.session_state.result_saved = False # تصفير الحالة عند التحليل الجديد
    input_data = {'daily_hours': d_hours, 'production_ratio': p_ratio, 'completed_projects': projects, 'quality_score': quality, 'original_posts': orig, 'replies': replies, 'emotional_stability': emotion, 'task_alignment': align, 'is_team': team}
    eff, def_, coh, diagnosis, rec_actions = calculate_sunan_scores(input_data)
    
    # حفظ النتائج مؤقتاً في الجلسة
    st.session_state.last_results = (eff, def_, coh, diagnosis)
    
    col_chart, col_text = st.columns([1.5, 1])
    with col_chart:
        categories = ['الفعالية', 'المناعة', 'التماسك']
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=[eff, def_, coh], theta=categories, fill='toself', name='مؤشرك', line_color='#1F618D'))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
    with col_text:
        st.success(diagnosis)
        if rec_actions:
            for act in rec_actions: st.warning(act)
            
    # زر الحفظ في قاعدة البيانات
    st.markdown("---")
    if st.button("💾 حفظ النتيجة في السجل الحضاري"):
        if save_to_google_sheet(eff, def_, coh, diagnosis):
            st.success("✅ تم حفظ نتيجتك بنجاح في قاعدة البيانات!")
            st.session_state.result_saved = True
            st.balloons()

else:
    st.info("👈 اضبط المؤشرات واضغط تحليل.")
