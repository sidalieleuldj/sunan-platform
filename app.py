import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import google.generativeai as genai

# --- 1. إعدادات الصفحة والذكاء الاصطناعي ---
st.set_page_config(page_title="منصة السُّنَن الرقمية - Gemini Edition", page_icon="🕌", layout="wide")

# إعداد Gemini API من Secrets
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.warning("⚠️ ملاحظة: مفتاح GEMINI_API_KEY غير موجود في Secrets. سيتم استخدام التحليل التقليدي.")

# --- 2. التصميم الشامل (CSS) - محمي ومحفظ بالكامل ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; background-color: #f8f9fa; }
    .stApp { direction: ltr; }
    .stMarkdown, p, h1, h2, h3, h4, .stAlert { text-align: right !important; direction: rtl !important; }
    
    /* تصميم السلايدر المطور */
    div[role="slider"] { background-color: #1e5631 !important; border: 3px solid #c9a44c !important; }
    div[data-baseweb="slider"] > div:first-child > div:first-child { background: linear-gradient(90deg, #c9a44c 0%, #1e5631 100%) !important; }
    .stSlider label { color: #1e5631 !important; font-weight: bold; font-size: 1.1em; }
    
    /* أزرار عصرية */
    .stButton>button { background: linear-gradient(135deg, #1e5631 0%, #2d8a4e 100%) !important; color: white !important; border-radius: 12px !important; padding: 15px 30px !important; font-weight: 900 !important; }
    
    /* صندوق تحليل Gemini الذكي */
    .ai-response-box {
        background: linear-gradient(135deg, #ffffff 0%, #f1f8e9 100%);
        border-right: 10px solid #1e5631; border-radius: 20px;
        padding: 30px; box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        margin-top: 20px; border: 1px solid #e0e0e0;
    }
    .challenge-box { background-color: #fcf3cf; border-radius: 15px; padding: 25px; border: 2px solid #c9a44c; margin-top: 20px; margin-bottom: 20px; color: #1b4f72; }
    .task-item { background: rgba(255,255,255,0.7); padding: 12px; border-radius: 10px; margin-bottom: 10px; border-right: 5px solid #1e5631; font-weight: bold; }
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

# دالة الاستعلام من Gemini AI الحقيقي
def get_gemini_analysis(user_name, diag, eff, def_s, coh):
    prompt = f"""
    أنت 'المستشار الحضاري الرقمي لمنصة السنن'. 
    المستخدم: {user_name}
    التشخيص: {diag}
    النتائج: الفعالية {eff}%، المناعة {def_s}%، التماسك {coh}%
    المطلوب: قدم تحليلاً فلسفياً ملهماً لحالته في فقرة واحدة، ثم اقترح 4 مهام أسبوعية محددة جداً لتحدي الـ 30 يوماً القادم.
    اجعل الأسلوب فخماً، مهنياً، وباللغة العربية الفصحى.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return f"🤖 تحليل تقليدي: حالتك هي {diag}. فعاليتك ({eff}%) تتطلب منك التركيز على الإنتاج بدلاً من الاستهلاك."

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

# --- 4. واجهة المستخدم (Sidebar) ---
if 'res' not in st.session_state: st.session_state['res'] = None

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2331/2331718.png", width=80)
    user_name = st.text_input("اسم المستخدم", "مبادر")
    st.markdown("---")
    d_hours = st.slider("ساعات التصفح", 0.0, 16.0, 4.0)
    p_ratio = st.slider("نسبة الإنتاج", 0.0, 1.0, 0.2)
    projects = st.number_input("مشاريع منجزة", 0, 50, 0)
    quality = st.select_slider("جودة المخرج", [1, 2, 3, 4, 5], value=3)
    orig = st.number_input("منشورات أصلية", 0, 50, 1)
    replies = st.number_input("ردود", 0, 100, 5)
    emotion = st.slider("الاتزان", 0, 10, 5)
    align = st.slider("وضوح الغاية", 0, 10, 5)
    team = st.checkbox("عمل جماعي")
    calc_btn = st.button("🚀 استشارة Gemini AI")

st.title("🕌 منصة السُّنَن الرقمية - AI Edition")

if calc_btn:
    vals = {'hours': d_hours, 'p_ratio': p_ratio, 'projects': projects, 'quality': quality, 'orig': orig, 'replies': replies, 'emotion': emotion, 'align': align, 'team': team}
    st.session_state['res'] = calculate_scores(vals)

if st.session_state['res']:
    eff, def_s, coh, diag = st.session_state['res']
    
    # الحصول على تحليل Gemini الحقيقي
    with st.spinner('يتم الآن تحليل بياناتك بواسطة Gemini 1.5...'):
        full_ai_report = get_gemini_analysis(user_name, diag, eff, def_s, coh)
    
    # عرض تقرير الذكاء الاصطناعي في صندوق فخم
    st.markdown(f"""
    <div class="ai-response-box">
        <h3 style="margin-top:0; color:#1e5631;">🤖 التقرير الحضاري الذكي (بواسطة Gemini)</h3>
        <p style="font-size:1.1em; line-height:1.7;">{full_ai_report}</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_g, col_t = st.columns([1.5, 1])
    with col_g:
        fig = go.Figure(go.Scatterpolar(r=[eff, def_s, coh, eff], theta=['الفعالية', 'المناعة', 'التماسك', 'الفعالية'], fill='toself', fillcolor='rgba(30, 86, 49, 0.2)', line=dict(color='#c9a44c', width=4)))
        st.plotly_chart(fig, use_container_width=True)
    with col_t:
        st.info(f"المبادر: {user_name} | التشخيص المبدئي: {diag}")
        if st.button("💾 توثيق النتيجة"):
            sheet = get_google_sheet()
            if sheet and user_name != "مبادر":
                sheet.append_row([user_name, datetime.now().strftime("%Y-%m-%d %H:%M"), str(eff), str(def_s), str(coh), diag])
                st.balloons(); st.success("تم الحفظ!")

st.markdown("---")
df_all = load_history_data()
if not df_all.empty:
    ca, cb = st.columns([1.5, 1])
    with ca:
        st.subheader("📈 مسار التطور")
        u_df = df_all[df_all['Name'] == user_name].sort_values('Date')
        if not u_df.empty: st.line_chart(u_df.set_index('Date')['Score_Eff'])
    with cb:
        st.subheader("🏆 المتصدرون")
        st.table(df_all.groupby('Name')['Score_Eff'].max().sort_values(ascending=False).head(5))
