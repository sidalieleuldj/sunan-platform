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
    # تأكد أن هذا الـ ID هو الخاص بملفك
    sheet_id = "1uXX-R40l8JQrPX8lcAxWbzxeeSs8Q5zaMF_DZ-R8TmE" 
    return client.open_by_key(sheet_id).sheet1

def save_to_google_sheet(eff, def_score, coh, diagnosis):
    try:
        sheet = get_google_sheet()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # يجب أن تتطابق هذه الأسماء مع رؤوس الأعمدة في ملفك
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
        return pd.DataFrame(data)
    except Exception as e:
        st.warning("⚠️ لم نتمكن من جلب السجل التاريخي.")
        return pd.DataFrame()

# --- 3. التصميم (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Cairo', sans-serif; direction: rtl; }
    .stSidebar [data-testid="stMarkdownContainer"] { direction: rtl; text-align: right; }
    h1, h2, h3, h4, h5 { text-align: right; color: #1F618D; }
    .stButton>button { width: 100%; background-color: #1F618D; color: white; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# --- 4. محرك السنن (المعادلات المحدثة) ---
def calculate_sunan_scores(data):
    # الفعالية: توازن بين الإنتاج والوقت المستهلك
    prod_weight = data['production_ratio'] * 60 
    proj_weight = data['completed_projects'] * 15
    quality_mod = (data['quality_score'] / 5)
    time_penalty = (data['daily_hours'] * 2.5) # خصم بسيط عن كل ساعة تصفح
    
    eff = (prod_weight + proj_weight) * quality_mod - time_penalty
    eff = max(min(round(eff + 20, 2), 100), 10) # +20 لضبط نقطة البداية
    
    # المناعة
    total_actions = data['original_posts'] + data['replies'] + 0.1
    indep_ratio = data['original_posts'] / total_actions
    stability = data['emotional_stability'] / 10.0
    def_score = round((indep_ratio * 60) + (stability * 40), 2)
    
    # التماسك
    coh = min(round((data['task_alignment'] * 10) * (1.2 if data['is_team'] else 1.0), 2), 100)
    
    # التشخيص
    if eff < 45:
        diag = "🛑 ركود حضاري: تستهلك أكثر مما تنتج. الزمن الرقمي يلتهم أثرك."
        acts = ["صيام رقمي لمدة ساعتين.", "أنجز مهمة واحدة صغيرة للنهاية."]
    elif def_score < 45:
        diag = "⚠️ جهد مكشوف: طاقتك مستنزفة في ردود الأفعال ومعارك الآخرين."
        acts = ["توقف عن الرد على التعليقات اليوم.", "اكتب فكرة أصلية بدلاً من النقد."]
    elif coh < 45:
        diag = "🧩 تشتت الجهد: جهدك فردي ولا يصب في هدفك الأكبر."
        acts = ["راجع أهدافك الأسبوعية.", "ابحث عن شريك لعمل مشترك."]
    else:
        diag = "🌟 حالة متوازنة: أنت تسير وفق السنن الحضارية."
        acts = []
        
    return eff, def_score, coh, diag, acts

# --- 5. واجهة المستخدم ---

# تهيئة ذاكرة الجلسة
if 'results' not in st.session_state:
    st.session_state['results'] = None
if 'show_history' not in st.session_state:
    st.session_state['show_history'] = False

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
        team = st.checkbox("أعمل ضمن فريق")
        
    st.markdown("---")
    # زر التحليل يقوم بتحديث النتائج في ذاكرة الجلسة فوراً
    calc_btn = st.button("🔍 تحليل الموقف")

st.title("منصة السُّنَن الرقمية")

if calc_btn:
    input_data = {
        'daily_hours': d_hours, 'production_ratio': p_ratio, 
        'completed_projects': projects, 'quality_score': quality, 
        'original_posts': orig, 'replies': replies, 
        'emotional_stability': emotion, 'task_alignment': align, 'is_team': team
    }
    # إعادة الحساب ببيانات جديدة
    st.session_state['results'] = calculate_sunan_scores(input_data)

# عرض النتائج
if st.session_state['results']:
    eff, def_s, coh, diag, acts = st.session_state['results']
    
    col_chart, col_text = st.columns([1.5, 1])
    
    with col_chart:
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=[eff, def_s, coh],
            theta=['الفعالية', 'المناعة', 'التماسك'],
            fill='toself',
            line_color='#1F618D'
        ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), margin=dict(t=30, b=30))
        st.plotly_chart(fig, use_container_width=True)
        
    with col_text:
        st.subheader("📋 التشخيص الحضاري")
        st.success(diag)
        for a in acts:
            st.warning(f"🔹 {a}")
            
    if st.button("💾 حفظ النتيجة في السجل"):
        if save_to_google_sheet(eff, def_s, coh, diag):
            st.balloons()
            st.success("تم الحفظ بنجاح!")

st.markdown("---")

# --- 6. السجل التاريخي ---
st.header("📈 سجل النمو التاريخي")
if st.button("🔄 تحديث السجل التاريخي"):
    st.session_state['history_df'] = load_history_data()
    st.session_state['show_history'] = True

if st.session_state.get('show_history'):
    df = st.session_state.get('history_df', pd.DataFrame())
    if not df.empty:
        # رسم بياني للتطور
        fig_hist = px.line(df, x=df.columns[0], y=df.columns[1:4], markers=True, title="مسار التطور")
        st.plotly_chart(fig_hist, use_container_width=True)
        st.dataframe(df.iloc[::-1], use_container_width=True)
