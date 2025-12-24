import streamlit as st
import plotly.graph_objects as go

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="منصة السُّنَن الرقمية",
    page_icon="🕌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. التصميم والخطوط (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');

    /* تعميم الخط والاتجاه */
    html, body, [class*="css"]  {
        font-family: 'Cairo', sans-serif;
    }
    
    /* ضبط اتجاه النصوص في القائمة الجانبية والرئيسية */
    .stSidebar [data-testid="stMarkdownContainer"] {
        direction: rtl;
        text-align: right;
    }
    .stMarkdown {
        direction: rtl;
        text-align: right;
    }
    
    /* تنسيق العناوين */
    h1, h2, h3 {
        text-align: right;
        font-family: 'Cairo', sans-serif;
        color: #1F618D;
    }

    /* تنسيق الأزرار */
    .stButton>button {
        width: 100%;
        background-color: #1F618D;
        color: white;
        border-radius: 8px;
        font-weight: bold;
    }
    
    /* إصلاح محاذاة النصوص داخل المدخلات */
    .stSlider [data-testid="stMarkdownContainer"] p {
        font-size: 16px;
        direction: rtl;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. محرك السنن ---
def calculate_sunan_scores(data):
    # معادلة الفعالية
    ratio_cons = 1.0 - data['production_ratio']
    numerator = (data['completed_projects'] * 10) + (data['production_ratio'] * 100 * (data['quality_score']/5))
    denominator = (data['daily_hours'] * ratio_cons * 5) + 0.001
    eff = min(round(numerator / denominator * 10, 2), 100)
    
    # معادلة المناعة
    total_actions = data['original_posts'] + data['replies'] + 0.001
    indep_ratio = data['original_posts'] / total_actions
    stability = data['emotional_stability'] / 10.0
    def_ = round((indep_ratio * 60) + (stability * 40), 2)
    
    # معادلة التماسك
    base = data['task_alignment'] * 10
    mult = 1.2 if data['is_team'] else 1.0
    coh = min(round(base * mult, 2), 100)
    
    # التشخيص
    diag = "🌟 **حالة متوازنة:** تسير وفق السنن، حافظ على هذا الإيقاع."
    actions = []
    
    if eff < 40: 
        diag = "🛑 **ركود حضاري:** تستهلك أكثر مما تنتج."
        actions.append("خصص ساعة يومياً للعمل العميق بعيداً عن الهاتف.")
    elif def_ < 40:
        diag = "⚠️ **جهد مكشوف:** طاقتك مهدورة في ردود الأفعال."
        actions.append("توقف عن النقاشات الجدلية لمدة 3 أيام.")
    elif coh < 40:
        diag = "🧩 **تشتت الجهد:** عمل فردي يفتقد للبوصلة."
        actions.append("ابحث عن شريك يشاركك نفس الهدف.")
        
    return eff, def_, coh, diag, actions

# --- 4. واجهة المستخدم ---

# القائمة الجانبية (للمدخلات فقط)
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2331/2331718.png", width=60)
    st.header("🎛️ لوحة التحكم السننية")
    
    st.info("قم بضبط المؤشرات هنا 👇")
    
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

# منطقة العرض الرئيسية (للنتائج فقط)
st.title("منصة السُّنَن الرقمية")
st.markdown("##### نحو هندسة حضارية لعصر ما بعد الطوفان الرقمي")

if calc_btn:
    # الحساب
    input_data = {
        'daily_hours': d_hours, 'production_ratio': p_ratio,
        'completed_projects': projects, 'quality_score': quality,
        'original_posts': orig, 'replies': replies,
        'emotional_stability': emotion, 'task_alignment': align,
        'is_team': team
    }
    eff, def_, coh, diagnosis, rec_actions = calculate_sunan_scores(input_data)
    
    # تقسيم النتائج
    col_chart, col_text = st.columns([1.5, 1])
    
    with col_chart:
        # الرسم البياني
        categories = ['الفعالية (التغيير)', 'المناعة (التدافع)', 'التماسك (الوحدة)']
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=[eff, def_, coh],
            theta=categories,
            fill='toself',
            name='مؤشرك',
            line_color='#1F618D'
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            margin=dict(t=20, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_text:
        st.markdown("### 🩺 التشخيص")
        st.success(diagnosis)
        
        if rec_actions:
            st.markdown("### 🚀 خطة العمل")
            for act in rec_actions:
                st.warning(act)
else:
    # شاشة ترحيبية عند الفتح
    st.image("https://img.freepik.com/free-vector/data-extraction-concept-illustration_114360-4876.jpg", width=400)
    st.markdown("""
    ### أهلاً بك في مختبر السنن..
    ابدأ بتعديل الأرقام في **القائمة الجانبية** (يمين الشاشة) ثم اضغط **"تحليل الموقف"** لترى نتيجتك.
    """)
