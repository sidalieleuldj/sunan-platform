import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="منصة السُّنَن الرقمية", page_icon="🕌", layout="wide")

# --- 2. CSS المطور للعربية ---
/* تحسين شكل السلايدر */
.stSlider [data-baseweb="slider"] {
    background-color: transparent;
    padding-top: 20px;
}

/* تغيير لون المسار (الخلفية) */
.stSlider [data-testid="stTickBar"] {
    display: none; /* إخفاء النقاط الصغيرة تحت الشريط */
}

/* لون الجزء النشط من الشريط (الأخضر) */
div[data-roles="track"] > div > div {
    background: linear-gradient(90deg, #c9a44c 0%, #1e5631 100%) !important;
}

/* شكل المقبض (الدائرة) */
div[role="slider"] {
    background-color: #1e5631 !important;
    border: 2px solid #c9a44c !important;
    height: 20px !important;
    width: 20px !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
}

/* تحسين تسمية السلايدر (Label) */
.stSlider label {
    font-weight: bold !important;
    color: #1e5631 !important;
    font-size: 1.1em !important;
    margin-bottom: 10px !important;
}
</style>
""", unsafe_allow_html=True)

# --- 3. وظائف قاعدة البيانات ---
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

# --- 4. محرك السنن (المنطق الحسابي) ---
def calculate_sunan_scores(data):
    raw_points = (data['production_ratio'] * 80) + (data['completed_projects'] * 20)
    quality_factor = data['quality_score'] / 5
    eff = (raw_points * quality_factor) - (data['daily_hours'] * 3) + 15
    eff = max(min(round(eff, 2), 100), 5)
    
    total = data['original_posts'] + data['replies'] + 0.1
    def_s = round(((data['original_posts'] / total) * 60) + ((data['emotional_stability'] / 10) * 40), 2)
    coh = min(round((data['task_alignment'] * 10) * (1.2 if data['is_team'] else 1.0), 2), 100)
    
    if eff < 45: diag, acts = "🛑 ركود حضاري", ["خصص ساعة عمل مركزة.", "قلل التصفح."]
    elif def_s < 45: diag, acts = "⚠️ جهد مكشوف", ["توقف عن الجدال.", "ابنِ محتواك الخاص."]
    elif coh < 45: diag, acts = "🧩 تشتت الجهد", ["ابحث عن شريك.", "اربط عملك بهدف."]
    else: diag, acts = "🌟 استواء حضاري", ["زكاة العلم تعليمه.", "وثّق تجربتك."]
    return eff, def_s, coh, diag, acts

# --- 5. واجهة المستخدم (Sidebar) ---
if 'res' not in st.session_state: st.session_state['res'] = None

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2331/2331718.png", width=60)
    st.header("🎛️ لوحة التحكم")
    user_name = st.text_input("الاسم", "مبادر")
    st.markdown("---")
    with st.expander("⏱️ الفعالية", expanded=True):
        d_hours = st.slider("ساعات التصفح", 0.0, 16.0, 4.0)
        p_ratio = st.slider("نسبة الإنتاج", 0.0, 1.0, 0.2)
        projects = st.number_input("مشاريع منجزة", 0, 50, 0)
        quality = st.select_slider("جودة المخرج", [1, 2, 3, 4, 5], value=3)
    with st.expander("🛡️ المناعة"):
        orig = st.number_input("منشورات أصلية", 0, 50, 1)
        replies = st.number_input("ردود وتفاعل", 0, 100, 5)
        emotion = st.slider("الاتزان الانفعالي", 0, 10, 5)
    with st.expander("🤝 التماسك"):
        align = st.slider("وضوح الأهداف", 0, 10, 5)
        team = st.checkbox("ضمن فريق عمل")
    
    calc_btn = st.button("🔍 تحليل النتائج")

st.title("🕌 منصة السُّنَن الرقمية")

# تنفيذ التحليل
if calc_btn:
    vals = {'daily_hours': d_hours, 'production_ratio': p_ratio, 'completed_projects': projects,
            'quality_score': quality, 'original_posts': orig, 'replies': replies,
            'emotional_stability': emotion, 'task_alignment': align, 'is_team': team}
    st.session_state['res'] = calculate_sunan_scores(vals)

# عرض النتائج
if st.session_state['res']:
    eff, def_s, coh, diag, acts = st.session_state['res']
    
    # تقسيم العرض إلى عمودين
    c1, c2 = st.columns([1.5, 1])
    
    with c1:
        # هنا تم إصلاح الإزاحة (Indentation)
        fig = go.Figure(go.Scatterpolar(
            r=[eff, def_s, coh, eff], 
            theta=['الفعالية', 'المناعة', 'التماسك', 'الفعالية'], 
            fill='toself',
            fillcolor='rgba(45, 138, 78, 0.3)', # لون أخضر شفاف
            line=dict(color='#c9a44c', width=3)   # خط ذهبي
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], gridcolor="#eeeeee"),
                bgcolor="white"
            ),
            margin=dict(t=40, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with c2:
        st.markdown(f"""
            <div style="background-color: white; padding: 20px; border-radius: 15px; border-right: 5px solid #c9a44c; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h3 style="color: #1e5631; margin-top: 0;">النتيجة: {user_name}</h3>
                <p style="font-size: 1.2em; font-weight: bold; color: #2d8a4e;">{diag}</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("") # مسافة
        for a in acts: 
            st.success(f"💡 {a}")
    
    if st.button("💾 حفظ النتيجة في السجل"):
        sheet = get_google_sheet()
        if sheet and user_name != "مبادر":
            row = [user_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), str(eff), str(def_s), str(coh), diag]
            sheet.append_row(row)
            st.success("تم الحفظ بنجاح!")
            st.balloons()
        else: st.error("اكتب اسمك أولاً")

# --- 6. الرسوم التاريخية والمتصدرين ---
st.markdown("---")
df_history = load_history_data()

if not df_history.empty:
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.header(f"📈 تاريخ: {user_name}")
        u_df = df_history[df_history['Name'] == user_name].sort_values('Date')
        if not u_df.empty:
            fig_h = go.Figure()
            fig_h.add_trace(go.Scatter(x=u_df['Date'], y=u_df['Score_Eff'], name="الفعالية"))
            st.plotly_chart(fig_h, use_container_width=True)
        else: st.info("لا بيانات سابقة.")
        
    with col_b:
        st.header("🏆 المتصدرون")
        if st.button("🔄 تحديث"): st.rerun()
        top = df_history.groupby('Name')['Score_Eff'].max().sort_values(ascending=False).head(5)
        st.table(top)




