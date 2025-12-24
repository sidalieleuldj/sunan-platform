import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. محرك السنن (مدمج هنا للتسهيل) ---
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
    diag = "حالة متوازنة: استمر على هذا النهج."
    actions = []
    if eff < 40: 
        diag = "⚠️ تحذير: حالة ركود (تراكم سلبي). استهلاكك للمحتوى يطغى على إنتاجك."
        actions.append("مهمة فورية: صم عن التصفح لمدة 24 ساعة وأنجز مهمة واحدة مؤجلة.")
    elif def_ < 40:
        diag = "⚠️ تحذير: جهد مكشوف. أنت مستنزف في ردود الأفعال."
        actions.append("مهمة فورية: توقف عن التعليقات الجدلية، واكتب منشوراً واحداً يمثل فكرتك.")
    elif coh < 40:
        diag = "⚠️ تحذير: تشتت. جهدك فردي ولا يخدم هدفك الأكبر."
        actions.append("مهمة فورية: ابحث عن شريك أو راجع أهدافك.")
        
    return eff, def_, coh, diag, actions

# --- 2. واجهة المستخدم (Streamlit) ---
st.set_page_config(page_title="منصة السنن الرقمية", layout="wide")

st.title("🏛️ منصة السُّنَن الرقمية (النموذج الأولي)")
st.markdown("---")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("📝 أدخل بياناتك")
    
    with st.expander("1. محور الفعالية (التغيير)", expanded=True):
        d_hours = st.slider("ساعات التصفح اليومي", 0.0, 12.0, 4.0)
        p_ratio = st.slider("نسبة الإنتاج", 0.0, 1.0, 0.1)
        projects = st.number_input("المشاريع المنجزة", 0, 50, 0)
        quality = st.slider("جودة الإنتاج", 1, 5, 3)

    with st.expander("2. محور المناعة (التدافع)"):
        orig = st.number_input("منشورات أصلية", 0, 50, 1)
        replies = st.number_input("ردود وتعليقات", 0, 50, 10)
        emotion = st.slider("الاتزان الانفعالي", 0, 10, 5)

    with st.expander("3. محور التماسك (الوحدة)"):
        align = st.slider("توافق المهام مع الهدف", 0, 10, 5)
        team = st.checkbox("أعمل ضمن فريق")
    
    calc_btn = st.button("🔍 تحليل الموقف الحضاري", type="primary")

with col2:
    if calc_btn:
        # تجهيز البيانات
        input_data = {
            'daily_hours': d_hours, 'production_ratio': p_ratio,
            'completed_projects': projects, 'quality_score': quality,
            'original_posts': orig, 'replies': replies,
            'emotional_stability': emotion, 'task_alignment': align,
            'is_team': team
        }
        
        # الحساب
        eff, def_, coh, diagnosis, rec_actions = calculate_sunan_scores(input_data)
        
        # عرض النتائج
        st.subheader("📊 رادار التوازن السنني")
        
        # الرسم البياني
        df = pd.DataFrame(dict(
            r=[eff, def_, coh, eff], # تكرار الأول لإغلاق الدائرة
            theta=['الفعالية', 'المناعة', 'التماسك', 'الفعالية']
        ))
        fig = px.line_polar(df, r='r', theta='theta', line_close=True, range_r=[0,100])
        fig.update_traces(fill='toself', line_color='#00CC96')
        fig.update_layout(polar=dict(radialaxis=dict(visible=True)))
        st.plotly_chart(fig, use_container_width=True)
        
        # التشخيص
        st.info(f"**التشخيص المنهجي:** {diagnosis}")
        
        if rec_actions:
            st.write("🛠️ **خطة العمل:**")
            for act in rec_actions:
                st.warning(act)
    else:
        st.markdown("### 👈 ابدأ بإدخال البيانات في القائمة اليمنى واضغط زر التحليل.")
        st.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=150)