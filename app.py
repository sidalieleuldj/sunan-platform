import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. إعدادات الصفحة والهوية البصرية ---
st.set_page_config(
    page_title="منصة السُّنَن الرقمية",
    page_icon="🕌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. حقن CSS (تجميل الواجهة والخطوط) ---
st.markdown("""
<style>
    /* استيراد خط 'Cairo' من جوجل */
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');

    /* تطبيق الخط على كامل التطبيق */
    html, body, [class*="css"]  {
        font-family: 'Cairo', sans-serif;
        direction: rtl; /* فرض الاتجاه من اليمين لليسار */
    }
    
    /* تنسيق العناوين */
    h1, h2, h3 {
        color: #2E86C1; /* لون أزرق وقور */
        font-weight: 700;
        text-align: right;
    }

    /* تنسيق النصوص العادية */
    p, label {
        text-align: right;
        font-size: 18px;
    }

    /* تنسيق الأزرار */
    .stButton>button {
        background-color: #2E86C1;
        color: white;
        border-radius: 10px;
        width: 100%;
        font-weight: bold;
        font-size: 20px;
        padding: 10px;
    }
    .stButton>button:hover {
        background-color: #1B4F72;
        color: white;
    }
    
    /* تنسيق الرسائل التحذيرية والمعلوماتية */
    .stAlert {
        direction: rtl;
        text-align: right;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. محرك السنن (الخوارزميات) ---
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
    
    # التشخيص المنهجي
    diag = "🌟 **حالة متوازنة (الاستواء الحضاري):** أنت تسير وفق السنن، حافظ على هذا الإيقاع."
    actions = []
    
    if eff < 40: 
        diag = "🛑 **حالة (القابلية للتراكم):** تستهلك أكثر مما تنتج. الزمن الرقمي يلتهمك."
        actions.append("صيام رقمي: اقطع الاتصال لمدة 4 ساعات يومياً.")
        actions.append("مشروع صغير: أنجز عملاً واحداً (مقال، كود، تصميم) اليوم.")
    elif def_ < 40:
        diag = "⚠️ **حالة (الجهد المكشوف):** طاقتك مستنزفة في ردود الأفعال ومعارك الآخرين."
        actions.append("الانسحاب التكتيكي: لا ترد على أي تعليق لمدة 3 أيام.")
        actions.append("المبادرة: اكتب منشوراً واحداً يمثل فكرتك الخاصة.")
    elif coh < 40:
        diag = "🧩 **حالة (التشتت):** جهدك فردي ولا يصب في تيار الأمة أو هدفك الأكبر."
        actions.append("البحث عن شريك: اعرض فكرتك على صديق يشاركك الاهتمام.")
        actions.append("بوصلة الأهداف: اكتب هدفك الأكبر وراجع مهامك اليومية بناءً عليه.")
        
    return eff, def_, coh, diag, actions

# --- 4. واجهة المستخدم (Layout) ---

# رأس الصفحة
col_logo, col_title = st.columns([1, 4])
with col_title:
    st.title("منصة السُّنَن الرقمية")
    st.markdown("**نحو هندسة حضارية لعصر ما بعد الطوفان الرقمي**")
with col_logo:
    st.image("https://cdn-icons-png.flaticon.com/512/2331/2331718.png", width=80)

st.markdown("---")

# التقسيم الرئيسي
col_inputs, col_results = st.columns([1, 1.5], gap="large")

with col_inputs:
    st.markdown("### 🎛️ لوحة المؤشرات")
    
    with st.expander("⏱️ 1. محور الفعالية (الزمن والإنتاج)", expanded=True):
        d_hours = st.slider("ساعات الاستخدام اليومي", 0.0, 16.0, 4.0, help="الوقت الكلي المقضي على الشاشات")
        p_ratio = st.slider("نسبة الإنتاج %", 0.0, 1.0, 0.1, help="كم % من وقتك تقضيه في صناعة محتوى أو تعلم؟")
        projects = st.number_input("المشاريع المنجزة (شهرياً)", 0, 50, 0)
        quality = st.select_slider("جودة الأثر", options=[1, 2, 3, 4, 5], value=3)

    with st.expander("🛡️ 2. محور المناعة (الاستقلال النفسي)"):
        orig = st.number_input("منشورات/أفكار أصلية", 0, 50, 1)
        replies = st.number_input("ردود وتعليقات جانبية", 0, 100, 10)
        emotion = st.slider("مقياس الهدوء النفسي", 0, 10, 5, help="10 تعني هدوء تام، 0 تعني غضب وتوتر دائم")

    with st.expander("🤝 3. محور التماسك (العمل الجماعي)"):
        align = st.slider("توافق المهام مع الرسالة", 0, 10, 5)
        team = st.toggle("أعمل ضمن فريق/مشروع مشترك؟", value=False)
    
    st.markdown("<br>", unsafe_allow_html=True)
    calc_btn = st.button("🔍 تحليل الموقف الحضاري")

with col_results:
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
        
        # عرض الرادار بتصميم محسن
        st.markdown("### 📊 رادار التوازن")
        
        categories = ['الفعالية (التغيير)', 'المناعة (التدافع)', 'التماسك (الوحدة)']
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=[eff, def_, coh],
            theta=categories,
            fill='toself',
            name='مؤشرك الحالي',
            line_color='#2E86C1',
            fillcolor='rgba(46, 134, 193, 0.4)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100]),
            ),
            showlegend=False,
            margin=dict(l=40, r=40, t=20, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # بطاقة التشخيص
        st.success(diagnosis, icon="🩺")
        
        # خطة العمل
        if rec_actions:
            st.markdown("### 🛠️ ما العمل؟ (الخطوة القادمة)")
            for act in rec_actions:
                st.warning(f"**مهمة:** {act}", icon="🚀")
                
    else:
        # شاشة الانتظار
        st.info("👈 ابدأ بضبط المؤشرات على اليمين لترى موقعك في خريطة السنن.")
        st.markdown("""
        > **"إن قضية الحضارة لا تحل بتكديس المنتجات، بل بحل مشكلة الإنسان."**
        > — *مالك بن نبي*
        """)
