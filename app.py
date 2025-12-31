import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from fpdf import FPDF
import io

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="منصة السُّنَن الرقمية", page_icon="🕌", layout="wide")

# --- 2. التصميم (CSS المطور) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; background-color: #f8f9fa; }
    .stApp { direction: ltr; }
    .stMarkdown, p, h1, h2, h3, h4, .stAlert { text-align: right !important; direction: rtl !important; }
    
    /* تصميم السلايدر والأزرار */
    div[role="slider"] { background-color: #1e5631 !important; border: 3px solid #c9a44c !important; }
    div[data-baseweb="slider"] > div:first-child > div:first-child {
        background: linear-gradient(90deg, #c9a44c 0%, #1e5631 100%) !important;
    }
    .stButton>button {
        background: linear-gradient(135deg, #1e5631 0%, #2d8a4e 100%) !important;
        color: white !important; border-radius: 12px !important; font-weight: bold !important;
        padding: 10px 20px !important; border: none !important;
    }
    div[data-testid="stExpander"] { background-color: white !important; border-radius: 15px !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. الدوال (قاعدة البيانات والتحليل والـ PDF) ---
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

def create_pdf(name, eff, def_s, coh, diag):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Digital Sunan Platform Report", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"User: {name}", ln=True)
    pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True)
    pdf.ln(5)
    pdf.cell(200, 10, txt=f"Efficiency: {eff}% | Immunity: {def_s}% | Cohesion: {coh}%", ln=True)
    pdf.cell(200, 10, txt=f"Final Diagnosis: {diag}", ln=True)
    pdf.ln(10)
    pdf.cell(200, 10, txt="Note: This report is a digital assessment of your performance.", ln=True)
    return pdf.output(dest='S').encode('latin-1')

def calculate_sunan_scores(data):
    raw_points = (data['production_ratio'] * 80) + (data['completed_projects'] * 20)
    eff = (raw_points * (data['quality_score'] / 5)) - (data['daily_hours'] * 3) + 15
    eff = max(min(round(eff, 2), 100), 5)
    total = data['original_posts'] + data['replies'] + 0.1
    def_s = round(((data['original_posts'] / total) * 60) + ((data['emotional_stability'] / 10) * 40), 2)
    coh = min(round((data['task_alignment'] * 10) * (1.2 if data['is_team'] else 1.0), 2), 100)
    if eff < 45: diag, acts = "🛑 ركود حضاري", ["خصص ساعة عمل مركزة.", "قلل التصفح."]
    elif def_s < 45: diag, acts = "⚠️ جهد مكشوف", ["توقف عن الجدال.", "ابنِ محتواك الخاص."]
    elif coh < 45: diag, acts = "🧩 تشتت الجهد", ["ابحث عن شريك.", "اربط عملك بهدف."]
    else: diag, acts = "🌟 استواء حضاري", ["زكاة العلم تعليمه.", "وثّق تجربتك."]
    return eff, def_s, coh, diag, acts

# --- 4. واجهة المستخدم ---
if 'res' not in st.session_state: st.session_state['res'] = None

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2331/2331718.png", width=80)
    st.header("لوحة التحكم")
    user_name = st.text_input("الاسم", "مبادر")
    st.markdown("---")
    with st.expander("⏱️ الفعالية", expanded=True):
        d_hours = st.slider("ساعات التصفح", 0.0, 16.0, 4.0)
        p_ratio = st.slider("نسبة الإنتاج", 0.0, 1.0, 0.2)
        projects = st.number_input("مشاريع منجزة", 0, 50, 0)
        quality = st.select_slider("جودة المخرج", [1, 2, 3, 4, 5], value=3)
    with st.expander("🛡️ المناعة"):
        orig = st.number_input("منشورات أصلية", 0, 50, 1)
        replies = st.number_input("ردود", 0, 100, 5)
        emotion = st.slider("الاتزان", 0, 10, 5)
    with st.expander("🤝 التماسك"):
        align = st.slider("وضوح الغاية", 0, 10, 5)
        team = st.checkbox("عمل جماعي")
    calc_btn = st.button("🔍 تحليل النتائج")

st.title("🕌 منصة السُّنَن الرقمية")

# --- 5. عرض النتائج والـ PDF ---
if calc_btn:
    vals = {'daily_hours': d_hours, 'production_ratio': p_ratio, 'completed_projects': projects,
            'quality_score': quality, 'original_posts': orig, 'replies': replies,
            'emotional_stability': emotion, 'task_alignment': align, 'is_team': team}
    st.session_state['res'] = calculate_sunan_scores(vals)

if st.session_state['res']:
    eff, def_s, coh, diag, acts = st.session_state['res']
    c1, c2 = st.columns([1.5, 1])
    with c1:
        fig = go.Figure(go.Scatterpolar(r=[eff, def_s, coh, eff], theta=['الفعالية', 'المناعة', 'التماسك', 'الفعالية'], 
                                       fill='toself', fillcolor='rgba(45, 138, 78, 0.2)', line=dict(color='#c9a44c', width=3)))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.info(f"المستخدم: {user_name}\n\nالتشخيص: {diag}")
        for a in acts: st.warning(f"💡 {a}")
        
        # أزرار الحفظ والتحميل
        if st.button("💾 حفظ في السجل"):
            sheet = get_google_sheet()
            if sheet and user_name != "مبادر":
                sheet.append_row([user_name, datetime.now().strftime("%Y-%m-%d %H:%M"), str(eff), str(def_s), str(coh), diag])
                st.success("تم الحفظ!")
        
        pdf_bytes = create_pdf(user_name, eff, def_s, coh, diag)
        st.download_button(label="📥 تحميل التقرير (PDF)", data=pdf_bytes, file_name=f"Report_{user_name}.pdf", mime="application/pdf")

# --- 6. السجلات التاريخية والمتصدرون ---
st.markdown("---")
df_all = load_history_data()
if not df_all.empty:
    col_a, col_b = st.columns([1.5, 1])
    with col_a:
        st.header(f"📈 سجل {user_name}")
        u_df = df_all[df_all['Name'] == user_name].sort_values('Date')
        if not u_df.empty:
            st.line_chart(u_df.set_index('Date')['Score_Eff'])
    with col_b:
        st.header("🏆 المتصدرون")
        top = df_all.groupby('Name')['Score_Eff'].max().sort_values(ascending=False).head(5)
        st.table(top)
