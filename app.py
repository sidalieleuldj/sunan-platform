import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="منصة السُّنَن الرقمية", page_icon="🕌", layout="wide")

# --- 2. التصميم الشامل (CSS) - يحفظ كل التعديلات السابقة ---
st.markdown("""
<style>
    /* تصميم خلفية السلايدر (المسار) */
    div[data-baseweb="slider"] > div:first-child > div:first-child {
        background: linear-gradient(90deg, #c9a44c 0%, #1e5631 100%) !important;
        height: 12px !important;
        border-radius: 10px !important;
    }
    
    /* تصميم المقبض (الكرة التي تتحرك) */
    div[role="slider"] {
        background-color: #ffffff !important;
        border: 4px solid #1e5631 !important;
        height: 28px !important;
        width: 28px !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2) !important;
        transition: transform 0.2s ease-in-out !important;
    }
    
    /* تأثير عند تمرير الماوس فوق المقبض */
    div[role="slider"]:hover {
        transform: scale(1.15) !important;
        cursor: pointer !important;
    }

    /* تحسين شكل النص فوق السلايدر */
    .stSlider label {
        color: #1e5631 !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px !important;
        margin-bottom: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. الدوال البرمجية (Logic & Data) ---
def get_google_sheet():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_info = dict(st.secrets["service_account"])
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)
        return client.open_by_key("1uXX-R40l8JQrPX8lcAxWbzxeeSs8Q5zaMF_DZ-R8TmE").sheet1
    except: return None

def load_history_data():
    sheet = get_google_sheet()
    if sheet:
        try:
            data = sheet.get_all_values()
            if len(data) > 1:
                df = pd.DataFrame(data[1:], columns=['Name', 'Date', 'Score_Eff', 'Score_Def', 'Score_Coh', 'Diagnosis'])
                for c in ['Score_Eff', 'Score_Def', 'Score_Coh']:
                    df[c] = pd.to_numeric(df[c].str.replace(',', '.'), errors='coerce').fillna(0)
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                return df
        except: pass
    return pd.DataFrame()

def ai_logic_analysis(eff, def_s, coh):
    # مصفوفة التحليلات الذكية
    if eff < 40:
        return f"🤖 تحليل الذكاء الاصطناعي: نلاحظ انخفاضاً حاداً في 'الفعالية' ({eff}%). محرك الإنتاج لديك يحتاج لإعادة ضبط. النصيحة: قلل ساعات التصفح فوراً وابدأ بإنتاج محتوى أصلي."
    
    if def_s < 45:
        return f"🤖 تحليل الذكاء الاصطناعي: تشخيصنا يشير إلى 'انكشاف دفاعي' ({def_s}%). أنت تستهلك وتتفاعل مع الآخرين أكثر مما تبني بصمتك الخاصة. النصيحة: طبق قاعدة 1:3 (مقابل كل 3 ردود، انشر فكرة أصلية واحدة)."
    
    if coh < 50:
        return f"🤖 تحليل الذكاء الاصطناعي: تعاني من 'تشتت الغاية' ({coh}%). تعمل بجد ولكن في اتجاهات متضاربة. النصيحة: اربط مهامك اليومية بهدف استراتيجي واحد واضح."
    
    if eff >= 75 and def_s >= 70:
        return f"🤖 تحليل الذكاء الاصطناعي: أنت في مرحلة **النضج الحضاري** ({eff}%). توازنك ممتاز بين الحماية والإنتاج. النصيحة: ابدأ في قيادة مشاريع جماعية وتوثيق منهجيتك."
    
    return f"🤖 تحليل الذكاء الاصطناعي: أداؤك متوازن بنسبة ({eff}%) ولكن يحتاج إلى 'دفعة نوعية'. النصيحة: ارفع معيار جودة المخرج بدلاً من زيادة ساعات العمل."

def get_30_day_challenge(diag):
    challenges = {
        "🛑 ركود حضاري": ["الأسبوع 1: حذف تطبيقات التشتت.", "الأسبوع 2: إنتاج مخرج رقمي واحد يومياً.", "الأسبوع 3: إنهاء مهمة معلقة منذ شهر.", "الأسبوع 4: مراجعة الفرق في الإنجاز."],
        "⚠️ جهد مكشوف": ["الأسبوع 1: الصيام عن الردود الجدلية.", "الأسبوع 2: كتابة تدوينة أسبوعية أصلية.", "الأسبوع 3: تحويل الردود لنصائح بناءة.", "الأسبوع 4: إطلاق مبادرة رقمية خاصة."],
        "🧩 تشتت الجهد": ["الأسبوع 1: تحديد هدف واحد كبير للشهر.", "الأسبوع 2: تقنية العمل العميق (ساعتين يومياً).", "الأسبوع 3: التخلص من المهام غير الضرورية.", "الأسبوع 4: تقييم التقدم نحو الغاية."]
    }
    return challenges.get(diag, ["الأسبوع 1: زكاة العلم تعليمه.", "الأسبوع 2: توثيق سُنن عملك.", "الأسبوع 3: بناء فريق عمل.", "الأسبوع 4: التخطيط للمرحلة القادمة."])

def calculate_scores(data):
    raw_points = (data['p_ratio'] * 80) + (data['projects'] * 20)
    eff = (raw_points * (data['quality'] / 5)) - (data['hours'] * 3) + 15
    eff = max(min(round(eff, 2), 100), 5)
    total = data['orig'] + data['replies'] + 0.1
    def_s = round(((data['orig'] / total) * 60) + ((data['emotion'] / 10) * 40), 2)
    coh = min(round((data['align'] * 10) * (1.2 if data['team'] else 1.0), 2), 100)
    if eff < 45: diag = "🛑 ركود حضاري"
    elif def_s < 45: diag = "⚠️ جهد مكشوف"
    elif coh < 45: diag = "🧩 تشتت الجهد"
    else: diag = "🌟 استواء حضاري"
    return eff, def_s, coh, diag

# --- 4. واجهة التحكم (Sidebar) ---
if 'res' not in st.session_state: st.session_state['res'] = None

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2331/2331718.png", width=80)
    st.header("🎛️ لوحة التحكم")
    user_name = st.text_input("اسم المستخدم", "مبادر")
    st.markdown("---")
    with st.expander("⏱️ الفعالية", expanded=True):
        d_hours = st.slider("ساعات التصفح", 0.0, 16.0, 4.0)
        p_ratio = st.slider("نسبة الإنتاج", 0.0, 1.0, 0.2)
        projects = st.number_input("مشاريع منجزة", 0, 50, 0)
        quality = st.select_slider("جودة المخرج", [1, 2, 3, 4, 5], value=3)
    with st.expander("🛡️ المناعة"):
        orig = st.number_input("بصمة أصلية", 0, 50, 1)
        replies = st.number_input("ردود", 0, 100, 5)
        emotion = st.slider("الاتزان", 0, 10, 5)
    with st.expander("🤝 التماسك"):
        align = st.slider("وضوح الغاية", 0, 10, 5)
        team = st.checkbox("عمل جماعي")
    calc_btn = st.button("🔍 تحليل وبناء الخطة")

st.title("🕌 منصة السُّنَن الرقمية")

# --- 5. العرض الرئيسي (النتائج + التحدي + الذكاء الاصطناعي) ---
if calc_btn:
    vals = {'hours': d_hours, 'p_ratio': p_ratio, 'projects': projects, 'quality': quality, 'orig': orig, 'replies': replies, 'emotion': emotion, 'align': align, 'team': team}
    st.session_state['res'] = calculate_scores(vals)

if st.session_state['res']:
    eff, def_s, coh, diag = st.session_state['res']
    ai_report = ai_logic_analysis(eff, def_s, coh)
    challenge_tasks = get_30_day_challenge(diag)
    
    # عرض التحدي أولاً (أهم ميزة)
    st.markdown(f"""
    <div class="challenge-box">
        <h3 style="margin-top:0; color:#d35400;">🚀 مسار الـ 30 يوماً للتغيير (حالة: {diag})</h3>
        {"".join([f'<div class="task-item">📅 {t}</div>' for t in challenge_tasks])}
    </div>
    """, unsafe_allow_html=True)
    
    col_g, col_t = st.columns([1.5, 1])
    with col_g:
        fig = go.Figure(go.Scatterpolar(r=[eff, def_s, coh, eff], theta=['الفعالية', 'المناعة', 'التماسك', 'الفعالية'], 
                                       fill='toself', fillcolor='rgba(30, 86, 49, 0.2)', line=dict(color='#c9a44c', width=4)))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), margin=dict(t=30, b=30))
        st.plotly_chart(fig, use_container_width=True)
        
    with col_t:
        st.markdown(f"""
            <div class="ai-analysis-card">
                <h2 style="color: #1e5631; margin-top: 0;">{user_name}</h2>
                <h4 style="color: #c9a44c;">التشخيص: {diag}</h4>
                <hr>
                <p style="font-size: 1.1em; line-height: 1.6;">🤖 <b>تحليل الذكاء الاصطناعي:</b> {ai_report}</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("💾 توثيق النتيجة في السجل"):
            sheet = get_google_sheet()
            if sheet and user_name != "مبادر":
                sheet.append_row([user_name, datetime.now().strftime("%Y-%m-%d %H:%M"), str(eff), str(def_s), str(coh), diag])
                st.balloons(); st.success("تم الحفظ بنجاح!")

# --- 6. الإحصائيات (دائماً ظاهرة) ---
st.markdown("---")
df_all = load_history_data()
if not df_all.empty:
    ca, cb = st.columns([1.5, 1])
    with ca:
        st.subheader(f"📈 مسار تطور: {user_name}")
        u_df = df_all[df_all['Name'] == user_name].sort_values('Date')
        if not u_df.empty:
            fig_h = go.Figure(go.Scatter(x=u_df['Date'], y=u_df['Score_Eff'], line=dict(color='#1e5631', width=3), fill='tozeroy'))
            st.plotly_chart(fig_h, use_container_width=True)
    with cb:
        st.subheader("🏆 المتصدرون")
        top = df_all.groupby('Name')['Score_Eff'].max().sort_values(ascending=False).head(5).reset_index()
        top.columns = ['المبادر', 'الفعالية %']
        st.table(top)
        if st.button("🔄 تحديث السجل"): st.rerun()


