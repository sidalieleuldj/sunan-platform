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

# --- 2. الاتصال بقاعدة البيانات (Google Sheets) ---
def get_google_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_dict = st.secrets["service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet_id = "1uXX-R40l8JQrPX8lcAxWbzxeeSs8Q5zaMF_DZ-R8TmE" 
    return client.open_by_key(sheet_id).sheet1

def save_to_google_sheet(eff, def_score, coh, diagnosis):
    try:
        sheet = get_google_sheet()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [current_time, eff, def_score, coh, diagnosis]
        sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"⚠️ خطأ في الحفظ: {e}")
        return False

def load_history_data():
    try:
        sheet = get_google_sheet()
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.warning("⚠️ لا توجد بيانات كافية لعرض التاريخ.")
        return pd.DataFrame()

# --- 3. التصميم (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Cairo', sans-serif; }
    .stSidebar [data-testid="stMarkdownContainer"] { direction: rtl; text-align: right; }
    .stMarkdown { direction: rtl; text-align: right; }
    h1, h2, h3, h4, h5 { text-align: right; color: #1F618D; }
    .stButton>button { width: 100%; background-color: #1F618D; color: white; border-radius: 8px; font-weight: bold; }
    [data-testid="stDataFrame"] { direction: rtl; }
</style>
""", unsafe_allow_html=True)

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
    else:
        diag = "🌟 حالة متوازنة (الاستواء الحضاري): استمر على هذا المنوال."
        actions = []
        
    return eff, def_, coh, diag, actions
# --- 5. واجهة المستخدم ولوحة التحكم ---
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

# --- 6. عرض النتائج والتشخيص ---
st.title("منصة السُّنَن الرقمية")

if calc_btn:
    input_data = {
        'daily_hours': d_hours, 'production_ratio': p_ratio, 'completed_projects': projects, 
        'quality_score': quality, 'original_posts': orig, 'replies': replies, 
        'emotional_stability': emotion, 'task_alignment': align, 'is_team': team
    }
    st.session_state['results'] = calculate_sunan_scores(input_data)
    st.session_state['show_results'] = True

if st.session_state.get('show_results'):
    eff, def_, coh, diagnosis, rec_actions = st.session_state['results']
    col_chart, col_text = st.columns([1.5, 1])
    with col_chart:
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=[eff, def_, coh], theta=['الفعالية', 'المناعة', 'التماسك'], fill='toself', name='مؤشرك', line_color='#1F618D'))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
    with col_text:
        st.markdown("### 🩺 التشخيص الحالي")
        st.success(diagnosis)
        if rec_actions:
            for act in rec_actions: st.warning(act)
    
    st.markdown("---")
    if st.button("💾 حفظ هذه النتيجة في السجل الحضاري"):
        with st.spinner('جاري التدوين...'):
            if save_to_google_sheet(eff, def_, coh, diagnosis):
                st.balloons(); st.success("✅ تم التدوين بنجاح!")
else:
    st.info("👈 قم بضبط المؤشرات في القائمة الجانبية ثم اضغط 'تحليل الموقف'.")

st.markdown("---")

# --- 7. سجل النمو التاريخي ---
st.header("📈 سجل النمو التاريخي")
if st.button("🔄 تحديث البيانات من السجل"):
    st.session_state['history_df'] = load_history_data()

df_hist = st.session_state.get('history_df', pd.DataFrame())
if not df_hist.empty:
    try:
        df_hist['date'] = pd.to_datetime(df_hist['date'])
        fig_history = px.line(df_hist, x='date', y=['eff_score', 'def_score', 'coh_score'], markers=True)
        st.plotly_chart(fig_history, use_container_width=True)
        st.dataframe(df_hist.sort_values(by='date', ascending=False), use_container_width=True)
    except:
        st.error("تأكد من مطابقة أسماء الأعمدة في ملف Excel")

