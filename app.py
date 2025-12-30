import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import google.generativeai as genai  # 🧠 مكتبة جوجل Gemini

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="منصة السُّنَن الرقمية",
    page_icon="🕌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; }
    .stApp { direction: ltr; }
    .stMarkdown, p, h1, h2, h3, h4, h5, span, div[data-testid="stMetricValue"], .stAlert, .stDataFrame {
        text-align: right !important; direction: rtl !important;
    }
    div[data-testid="stTable"] { direction: rtl; text-align: right; }
    table { width: 100%; text-align: right !important; }
    th, td { text-align: right !important; }
    input { text-align: right !important; direction: rtl !important; }
    .stButton>button { width: 100%; background-color: #1F618D; color: white; border-radius: 8px; }
    
    /* تنسيق خاص لرسالة المستشار الذكي */
    .ai-box {
        background-color: #e8f4f8;
        border-right: 5px solid #1F618D;
        padding: 20px;
        border-radius: 8px;
        margin-top: 20px;
        color: #2c3e50;
        font-size: 1.1em;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. الاتصال بقاعدة البيانات ---
def get_google_sheet():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_dict = st.secrets["service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet_id = "1uXX-R40l8JQrPX8lcAxWbzxeeSs8Q5zaMF_DZ-R8TmE" 
        return client.open_by_key(sheet_id).sheet1
    except: return None

def save_to_google_sheet(name, eff, def_score, coh, diagnosis):
    sheet = get_google_sheet()
    if sheet:
        try:
            row = [name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), str(eff), str(def_score), str(coh), diagnosis]
            sheet.append_row(row)
            return True
        except: return False
    return False

def smart_fix_score(val):
    try:
        s_val = str(val).replace(',', '.')
        score = float(s_val)
        if score > 100: score = score / 10
        if score > 100: score = 100.0
        return score
    except: return 0.0

def load_history_data():
    sheet = get_google_sheet()
    if sheet:
        try:
            data = sheet.get_all_values()
            df = pd.DataFrame(data)
            if df.empty or len(df.columns) < 6: return pd.DataFrame()
            df = df.iloc[:, :6]
            df.columns = ['Name', 'Date', 'Score_Eff', 'Score_Def', 'Score_Coh', 'Diagnosis']
            df = df[df['Name'] != 'Name']
            for c in ['Score_Eff', 'Score_Def', 'Score_Coh']:
                df[c] = df[c].apply(smart_fix_score)
            return df
        except: pass
    return pd.DataFrame()

# --- 🧠 4. المستشار السنني (نسخة Gemini) ---
def get_ai_consultation(name, current_eff, current_def, current_coh, diag, history_df):
    try:
        api_key = st.secrets.get("gemini_key")
        genai.configure(api_key=api_key)
        
        # اختيار الموديل المتاح
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model = genai.GenerativeModel(available_models[0])
        
        # تحويل التاريخ إلى ملخص نصي ليفهمه الذكاء الاصطناعي
        history_summary = ""
        if not history_df.empty:
            # نأخذ آخر 5 سجلات للمستخدم لنعطي الذكاء سياقاً عن تطوره
            user_history = history_df[history_df['Name'].str.strip() == name.strip()].tail(5)
            history_summary = user_history[['Date', 'Score_Eff', 'Score_Def', 'Score_Coh']].to_string()

        prompt = f"""
        أنت "خبير استراتيجي في فقه السنن"، مهمتك تحليل المسار الحضاري لـ {name}.
        
        النتائج الحالية:
        - الفعالية: {current_eff} | المناعة: {current_def} | التماسك: {current_coh}
        - التشخيص: {diag}
        
        السجل التاريخي للمستخدم (لتحليل المنحنى):
        {history_summary}
        
        المطلوب منك:
        1. قارن النتيجة الحالية بالنتائج السابقة (هل هناك تحسن أم تراجع؟).
        2. قدم بصيرة سننية تربط بين هذا المسار وبين مفاهيم مالك بن نبي (مثل: القابلية للاستعمار، أو تكديس الأشياء مقابل بناء الأفكار).
        3. أعطه "واجباً عملياً" واحداً لهذا الأسبوع لضمان استمرار الصعود.
        
        اللغة: عربية فصيحة، ملهمة، وعميقة. (4 أسطر كحد أقصى).
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ فشل تحليل المسار التاريخي: {str(e)}"
        
# --- 5. محرك السنن ---
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

# --- 6. واجهة المستخدم ---
if 'res' not in st.session_state: st.session_state['res'] = None

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2331/2331718.png", width=60)
    st.header("🎛️ لوحة التحكم")
    user_name = st.text_input("الاسم", "مبادر")
    st.markdown("---")
    with st.expander("⏱️ الفعالية", expanded=True):
        d_hours = st.slider("ساعات التصفح", 0.0, 16.0, 4.0)
        p_ratio = st.slider("نسبة الإنتاج", 0.0, 1.0, 0.2)
        projects = st.number_input("مشاريع", 0, 50, 0)
        quality = st.select_slider("الجودة", [1, 2, 3, 4, 5], value=3)
    with st.expander("🛡️ المناعة"):
        orig = st.number_input("بصمتك", 0, 50, 1)
        replies = st.number_input("ردود", 0, 100, 5)
        emotion = st.slider("الهدوء", 0, 10, 5)
    with st.expander("🤝 التماسك"):
        align = st.slider("وضوح الهدف", 0, 10, 5)
        team = st.checkbox("عمل جماعي")
    calc_btn = st.button("🔍 تحليل الموقف")

st.title("🕌 منصة السُّنَن الرقمية")

if calc_btn:
    vals = {'daily_hours': d_hours, 'production_ratio': p_ratio, 'completed_projects': projects,
            'quality_score': quality, 'original_posts': orig, 'replies': replies,
            'emotional_stability': emotion, 'task_alignment': align, 'is_team': team}
    st.session_state['res'] = calculate_sunan_scores(vals)

if st.session_state['res']:
    eff, def_s, coh, diag, acts = st.session_state['res']
    c1, c2 = st.columns([1.5, 1])
    with c1:
        fig = go.Figure(go.Scatterpolar(r=[eff, def_s, coh], theta=['الفعالية', 'المناعة', 'التماسك'], fill='toself', line_color='#1F618D'))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), margin=dict(t=40, b=40))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.info(f"النتيجة: {user_name}\n\n{diag}")
        
        # --- زر المستشار الذكي ---
        # أضفت مفتاحاً فريداً (key) للزر لضمان عدم اختفائه
        if st.button("✨ استشارة المرشد السنني (AI)", key="ai_btn"):
            with st.spinner('جاري الاتصال بـ Gemini للتحليل...'):
                advice = get_ai_consultation(user_name, eff, def_s, coh, diag)
                st.markdown(f"""
                <div class="ai-box">
                    <h4>🤖 بصيرة سننية (عبر Gemini):</h4>
                    <p>{advice}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # النصائح السريعة تظهر دائماً تحت الزر
        for a in acts: 
            st.warning(f"💡 نصيحة سريعة: {a}")
    
    if st.button("💾 حفظ النتيجة"):
        if user_name != "مبادر":
            if save_to_google_sheet(user_name, eff, def_s, coh, diag):
                st.balloons(); st.success("تم الحفظ")
        else: st.error("اكتب الاسم")

# --- 7. الرسم البياني ---
if user_name and user_name != "مبادر":
    st.markdown("---")
    st.header(f"📈 المسار التاريخي: {user_name}")
    df_history = load_history_data()
    if not df_history.empty:
        df_history['Name_Clean'] = df_history['Name'].astype(str).str.strip()
        target_name = user_name.strip()
        user_hist = df_history[df_history['Name_Clean'] == target_name].copy()
        if not user_hist.empty:
            user_hist['Date'] = pd.to_datetime(user_hist['Date'], errors='coerce')
            user_hist = user_hist.dropna(subset=['Date']).sort_values('Date')
            if not user_hist.empty:
                fig_h = go.Figure()
                fig_h.add_trace(go.Scatter(x=user_hist['Date'], y=user_hist['Score_Eff'], name='الفعالية', line=dict(color='#1F618D', width=3)))
                fig_h.add_trace(go.Scatter(x=user_hist['Date'], y=user_hist['Score_Def'], name='المناعة', line=dict(color='#E74C3C', dash='dot')))
                fig_h.add_trace(go.Scatter(x=user_hist['Date'], y=user_hist['Score_Coh'], name='التماسك', line=dict(color='#27AE60', dash='dot')))
                fig_h.update_layout(title="تطور الأداء", hovermode="x unified", yaxis=dict(range=[0, 105]))
                st.plotly_chart(fig_h, use_container_width=True)
        else: st.warning(f"لا توجد بيانات سابقة لـ {user_name}")

st.markdown("---")
st.header("🏆 المتصدرين")
if st.button("تحديث"):
    df = load_history_data()
    if not df.empty and 'Score_Eff' in df.columns:
        top = df.groupby('Name')['Score_Eff'].max().sort_values(ascending=False).head(3)
        data = [{"المركز":f"{i+1}","الاسم":n,"الفعالية":f"{s:.1f}%"} for i,(n,s) in enumerate(top.items())]
        st.table(pd.DataFrame(data))











