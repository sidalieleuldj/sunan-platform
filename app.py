import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="منصة السُّنَن الرقمية", page_icon="🕌", layout="wide")

# --- 2. التصميم (CSS المطور ليشمل التحدي) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; background-color: #f4f7f6; }
    .stApp { direction: ltr; }
    .stMarkdown, p, h1, h2, h3, h4, .stAlert { text-align: right !important; direction: rtl !important; }
    
    /* تصميم البطاقات */
    .challenge-card {
        background: white; border-radius: 20px; padding: 20px;
        border-top: 5px solid #c9a44c; box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        margin-top: 20px;
    }
    .task-item {
        background: #f9f9f9; padding: 10px 15px; border-radius: 10px;
        margin-bottom: 8px; border-right: 4px solid #1e5631;
    }
    .stButton>button {
        background: linear-gradient(135deg, #1e5631 0%, #2d8a4e 100%) !important;
        color: white !important; border-radius: 12px !important; font-weight: bold !important;
        padding: 12px 25px !important; border: none !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. الدوال البرمجية ---
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

# دالة تحدي الـ 30 يوماً بناءً على النتيجة
def get_30_day_challenge(diag):
    challenges = {
        "🛑 ركود حضاري": ["الأسبوع 1: تقليل ساعات التصفح بنسبة 50%.", "الأسبوع 2: تحديد ساعة واحدة يومياً للإنتاج فقط.", "الأسبوع 3: إنهاء مشروع واحد صغير مؤجل.", "الأسبوع 4: مشاركة المخرج مع الآخرين."],
        "⚠️ جهد مكشوف": ["الأسبوع 1: التوقف عن الردود الجدلية تماماً.", "الأسبوع 2: كتابة مقال أو فكرة أصلية يومياً.", "الأسبوع 3: تحويل الردود إلى 'بصمات إيجابية' فقط.", "الأسبوع 4: بناء منصة خاصة لنشر الأفكار."],
        "🧩 تشتت الجهد": ["الأسبوع 1: تحديد هدف واحد كبير للشهر.", "الأسبوع 2: ربط كل مهمة يومية بهذا الهدف.", "الأسبوع 3: البحث عن شريك لتبادل المتابعة.", "الأسبوع 4: تقييم ما تم إنجازه وحذف المشتتات."],
        "🌟 استواء حضاري": ["الأسبوع 1: تعليم مهارة تتقنها لشخص آخر.", "الأسبوع 2: البحث عن ثغرة في مجالك وسدها.", "الأسبوع 3: كتابة 'دليل عملي' لتجربتك.", "الأسبوع 4: البدء بمبادرة جماعية كبرى."]
    }
    return challenges.get(diag, ["ابدأ بالتحليل لتلقي تحديك الخاص."])

def calculate_sunan_scores(data):
    raw_points = (data['production_ratio'] * 80) + (data['completed_projects'] * 20)
    eff = (raw_points * (data['quality_score'] / 5)) - (data['daily_hours'] * 3) + 15
    eff = max(min(round(eff, 2), 100), 5)
    total = data['original_posts'] + data['replies'] + 0.1
    def_s = round(((data['original_posts'] / total) * 60) + ((data['emotional_stability'] / 10) * 40), 2)
    coh = min(round((data['task_alignment'] * 10) * (1.2 if data['is_team'] else 1.0), 2), 100)
    
    if eff < 45: diag = "🛑 ركود حضاري"
    elif def_s < 45: diag = "⚠️ جهد مكشوف"
    elif coh < 45: diag = "🧩 تشتت الجهد"
    else: diag = "🌟 استواء حضاري"
    return eff, def_s, coh, diag

# --- 4. واجهة المستخدم ---
if 'res' not in st.session_state: st.session_state['res'] = None

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2331/2331718.png", width=80)
    st.title("لوحة التحكم")
    user_name = st.text_input("اسم المبادر", "زائر")
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

# --- 5. عرض النتائج والتحدي ---
if calc_btn:
    vals = {'daily_hours': d_hours, 'production_ratio': p_ratio, 'completed_projects': projects,
            'quality_score': quality, 'original_posts': orig, 'replies': replies,
            'emotional_stability': emotion, 'task_alignment': align, 'is_team': team}
    st.session_state['res'] = calculate_sunan_scores(vals)

if st.session_state['res']:
    eff, def_s, coh, diag = st.session_state['res']
    
    c1, c2 = st.columns([1.5, 1])
    with c1:
        fig = go.Figure(go.Scatterpolar(r=[eff, def_s, coh, eff], theta=['الفعالية', 'المناعة', 'التماسك', 'الفعالية'], fill='toself', fillcolor='rgba(45, 138, 78, 0.2)', line=dict(color='#c9a44c', width=4)))
        st.plotly_chart(fig, use_container_width=True)
        
        # قسم تحدي الـ 30 يوماً
        st.markdown(f'<div class="challenge-card"><h3>🚀 تحدي الـ 30 يوماً القادم</h3>', unsafe_allow_html=True)
        tasks = get_30_day_challenge(diag)
        for task in tasks:
            st.markdown(f'<div class="task-item">{task}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with c2:
        st.info(f"المبادر: {user_name} | التشخيص: {diag}")
        st.markdown(f"**🤖 تحليل الذكاء الاصطناعي:** توازنك الحالي يعطيك مؤشر {eff}% في الفعالية. تحديك القادم مصمم لرفع هذا الرقم بمقدار 20 درجة خلال شهر.")
        
        if st.button("💾 حفظ في السجل الحضاري"):
            sheet = get_google_sheet()
            if sheet and user_name != "زائر":
                sheet.append_row([user_name, datetime.now().strftime("%Y-%m-%d %H:%M"), str(eff), str(def_s), str(coh), diag])
                st.success("تم الحفظ!")

# --- 6. الإحصائيات ---
st.markdown("---")
df_all = load_history_data()
if not df_all.empty:
    col_a, col_b = st.columns([1.6, 1])
    with col_a:
        st.header(f"📈 مسار تطورك")
        u_df = df_all[df_all['Name'] == user_name].sort_values('Date')
        if not u_df.empty:
            st.line_chart(u_df.set_index('Date')['Score_Eff'])
    with col_b:
        st.header("🏆 المتصدرون")
        top = df_all.groupby('Name')['Score_Eff'].max().sort_values(ascending=False).head(5).reset_index()
        st.table(top)
