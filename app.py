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

# --- 2. التصميم (CSS) المطور لدعم العربية مع بقاء اللوحة يساراً ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    /* ضبط الخط والاتجاه العام للمحتوى */
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
        direction: rtl; /* النصوص من اليمين لليسار */
    }

    /* الحفاظ على لوحة التحكم في الجهة اليسرى (الوضع الافتراضي لستريمليت) */
    section[data-testid="stSidebar"] {
        direction: rtl; /* المحتوى داخل اللوحة يبقى يمين */
    }
    
    /* ضبط محاذاة العناوين والنصوص */
    h1, h2, h3, h4, h5, p {
        text-align: right;
    }

    /* تحسين شكل الأزرار */
    .stButton>button {
        width: 100%;
        background-color: #1F618D;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        padding: 0.5rem;
    }
    
    /* تعديل تنسيق التنبيهات */
    .stAlert {
        direction: rtl;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. الاتصال بقاعدة البيانات (Google Sheets) ---
def get_google_sheet():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_dict = st.secrets["service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        # ID الملف الخاص بك
        sheet_id = "1uXX-R40l8JQrPX8lcAxWbzxeeSs8Q5zaMF_DZ-R8TmE" 
        return client.open_by_key(sheet_id).sheet1
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال بـ Google Sheets: {e}")
        return None

def save_to_google_sheet(eff, def_score, coh, diagnosis):
    sheet = get_google_sheet()
    if sheet:
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row = [current_time, eff, def_score, coh, diagnosis]
            sheet.append_row(row)
            return True
        except Exception as e:
            st.error(f"⚠️ خطأ في الحفظ: {e}")
    return False

def load_history_data():
    sheet = get_google_sheet()
    if sheet:
        try:
            data = sheet.get_all_records()
            return pd.DataFrame(data)
        except Exception as e:
            st.warning("⚠️ لا توجد بيانات في السجل حالياً.")
    return pd.DataFrame()

# --- 4. محرك السنن (المعادلات المحدثة للتفاعل الفوري) ---
def calculate_sunan_scores(data):
    # الفعالية: توازن بين الإنتاج والوقت (تم تحديثها لتكون أكثر حساسية للتغيير)
    prod_val = data['production_ratio'] * 70
    proj_val = data['completed_projects'] * 10
    quality_mult = (data['quality_score'] / 5)
    time_impact = (data['daily_hours'] * 3)
    
    eff = ((prod_val + proj_val) * quality_mult) - time_impact + 20
    eff = max(min(round(eff, 2), 100), 5)
    
    # المناعة: الاستقلالية مقابل ردود الفعل
    total_actions = data['original_posts'] + data['replies'] + 0.1
    indep_ratio = data['original_posts'] / total_actions
    stability = data['emotional_stability'] / 10.0
    def_score = round((indep_ratio * 60) + (stability * 40), 2)
    
    # التماسك: العمل الجماعي والوضوح
    coh = min(round((data['task_alignment'] * 10) * (1.2 if data['is_team'] else 1.0), 2), 100)
    
    # التشخيص الآلي
    if eff < 40:
        diag = "🛑 ركود حضاري: استهلاكك الرقمي يطغى على إنتاجك. أنت في حالة تبديد للزمن."
        acts = ["صيام رقمي: اقطع الاتصال ساعتين متواصلتين.", "أنهِ مهمة واحدة معلقة منذ زمن."]
    elif def_score < 40:
        diag = "⚠️ جهد مكشوف: أنت مستنزف في ردود الأفعال. ابدأ بصناعة المحتوى لا التعليق عليه."
        acts = ["لا ترد على أي استفزاز اليوم.", "اكتب مقالاً أو فكرة أصلية من إنتاجك."]
    elif coh < 40:
        diag = "🧩 تشتت الجهد: طاقاتك مبعثرة ولا تخدم أهدافك الكبرى."
        acts = ["حدد هدفاً واحداً لهذا الأسبوع فقط.", "ابحث عن فريق عمل يشاركك الرؤية."]
    else:
        diag = "🌟 حالة الاستواء الحضاري: أنت تسيطر على أدواتك الرقمية وتوجهها نحو أثر حقيقي."
        acts = ["استمر في هذا الإيقاع.", "حاول نقل هذه التجربة لغيرك."]
        
    return eff, def_score, coh, diag, acts

# --- 5. واجهة المستخدم الرئيسية ---

# تهيئة المتغيرات في الذاكرة
if 'results' not in st.session_state:
    st.session_state['results'] = None

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2331/2331718.png", width=60)
    st.header("🎛️ لوحة التحكم")
    
    with st.expander("⏱️ 1. محور الفعالية", expanded=True):
        d_hours = st.slider("ساعات التصفح اليومي", 0.0, 16.0, 4.0)
        p_ratio = st.slider("نسبة الإنتاج إلى الاستهلاك", 0.0, 1.0, 0.2)
        projects = st.number_input("مشاريع أو مهام مكتملة", 0, 50, 0)
        quality = st.select_slider("جودة الأثر الناتج", options=[1, 2, 3, 4, 5], value=3)
        
    with st.expander("🛡️ 2. محور المناعة"):
        orig = st.number_input("منشورات أصلية (بصمتك)", 0, 50, 1)
        replies = st.number_input("ردود وتعليقات (رد فعل)", 0, 100, 5)
        emotion = st.slider("الهدوء والاتزان النفسي", 0, 10, 5)
        
    with st.expander("🤝 3. محور التماسك"):
        align = st.slider("وضوح الهدف الشخصي", 0, 10, 5)
        team = st.checkbox("العمل ضمن بيئة جماعية")
        
    st.markdown("---")
    calc_btn = st.button("🔍 تحليل الموقف الحالي")

st.title("🕌 منصة السُّنَن الرقمية")
st.markdown("قياس الأثر الحضاري في الفضاء الرقمي")

if calc_btn:
    input_data = {
        'daily_hours': d_hours, 'production_ratio': p_ratio, 
        'completed_projects': projects, 'quality_score': quality, 
        'original_posts': orig, 'replies': replies, 
        'emotional_stability': emotion, 'task_alignment': align, 'is_team': team
    }
    # تحديث النتائج فورياً
    st.session_state['results'] = calculate_sunan_scores(input_data)

# عرض النتائج في حال وجودها
if st.session_state['results']:
    eff, def_s, coh, diag, acts = st.session_state['results']
    
    col_chart, col_info = st.columns([1.5, 1])
    
    with col_chart:
        # رسم الرادار الحضاري
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=[eff, def_s, coh],
            theta=['الفعالية', 'المناعة', 'التماسك'],
            fill='toself',
            name='مؤشراتك',
            line_color='#1F618D'
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=False,
            margin=dict(t=40, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with col_info:
        st.subheader("📋 التشخيص والمقترحات")
        st.info(diag)
        if acts:
            for a in acts:
                st.warning(f"💡 {a}")
            
    if st.button("💾 تدوين في السجل الحضاري (حفظ)"):
        with st.spinner("جاري الحفظ..."):
            if save_to_google_sheet(eff, def_s, coh, diag):
                st.balloons()
                st.success("✅ تم تدوين النتيجة في سجلك التاريخي.")

st.markdown("---")

# --- 6. السجل التاريخي وتحليل النمو ---
st.header("📈 سجل النمو والارتقاء")

if st.button("🔄 استعادة السجل من القاعدة"):
    history_df = load_history_data()
    if not history_df.empty:
        st.session_state['history_df'] = history_df
    else:
        st.info("السجل فارغ حالياً، ابدأ بحفظ نتائجك أولاً.")

if 'history_df' in st.session_state:
    df = st.session_state['history_df']
    
    # عرض الرسم البياني للتطور الزمني
    try:
        # نفترض أن الأعمدة هي: التاريخ، الفعالية، المناعة، التماسك، التشخيص
        fig_line = px.line(df, x=df.columns[0], y=df.columns[1:4], 
                           title="مسار ارتقائك الحضاري عبر الزمن",
                           labels={'value': 'الدرجة', 'variable': 'المؤشر'},
                           markers=True)
        st.plotly_chart(fig_line, use_container_width=True)
        
        # عرض البيانات في جدول
        st.subheader("📑 التفاصيل التاريخية")
        st.dataframe(df.iloc[::-1], use_container_width=True)
    except:
        st.error("تأكد من أن ترتيب الأعمدة في Google Sheet صحيح (التاريخ ثم المؤشرات الثلاثة).")
