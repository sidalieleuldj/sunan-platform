أعتذر منك جداً، يبدو أن الانتقال للكود الكامل في المرة الأخيرة كان "مختصراً" أكثر من اللازم مما أدى لفقدان بعض الميزات والجماليات التي بنيناها معاً، وتسبب في تعطل الأزرار.

لقد قمت الآن بإعادة بناء الكود بالكامل، مع دمج **كل الميزات**: (التنسيق الجمالي القديم، لوحة التحكم الكاملة، نظام Gemini المتطور الذي يقرأ التاريخ، وإصلاح الأزرار).

### 🛠️ الكود الذهبي (الإصدار الشامل والمستقر)

**انسخ هذا الكود وضعه في `app.py` بالكامل:**

```python
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import google.generativeai as genai

# --- 1. إعدادات الصفحة (الهوية البصرية الكاملة) ---
st.set_page_config(
    page_title="منصة السُّنَن الرقمية",
    page_icon="🕌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS المطور (لإرجاع الواجهة الجميلة) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; }
    .stApp { direction: ltr; }
    .stMarkdown, p, h1, h2, h3, h4, h5, span, div[data-testid="stMetricValue"], .stAlert, .stDataFrame {
        text-align: right !important; direction: rtl !important;
    }
    div[data-testid="stTable"] { direction: rtl; text-align: right; }
    .stButton>button { width: 100%; background-color: #1F618D; color: white; border-radius: 8px; font-weight: bold; }
    .ai-box { background-color: #f0f8ff; border-right: 5px solid #1F618D; padding: 20px; border-radius: 10px; margin-top: 20px; color: #000; text-align: right; }
</style>
""", unsafe_allow_html=True)

# --- 3. وظائف قاعدة البيانات (المستقرة) ---
def get_google_sheet():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_dict = st.secrets["service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet_id = "1uXX-R40l8JQrPX8lcAxWbzxeeSs8Q5zaMF_DZ-R8TmE" 
        return client.open_by_key(sheet_id).sheet1
    except Exception as e:
        return None

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
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            return df
        except: return pd.DataFrame()
    return pd.DataFrame()

def save_to_google_sheet(name, eff, def_score, coh, diagnosis):
    sheet = get_google_sheet()
    if sheet:
        try:
            row = [name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), str(eff), str(def_score), str(coh), diagnosis]
            sheet.append_row(row)
            return True
        except: return False
    return False

# --- 4. المستشار الذكي المتطور (تعديل الـ Arguments) ---
def get_ai_consultation(name, eff, def_s, coh, diag, history_df):
    try:
        api_key = st.secrets.get("gemini_key")
        if not api_key: return "⚠️ مفتاح AI مفقود في الإعدادات."
        genai.configure(api_key=api_key)
        
        # اختيار الموديل المتاح تلقائياً
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model = genai.GenerativeModel(available_models[0])
        
        # تحليل التاريخ للمستشار
        hist_context = ""
        if not history_df.empty:
            user_hist = history_df[history_df['Name'].str.strip() == name.strip()].tail(3)
            if not user_hist.empty:
                hist_context = f"المسار السابق للمستخدم: {user_hist[['Date', 'Score_Eff']].to_string()}"

        prompt = f"""أنت مستشار حضاري خبير في فكر مالك بن نبي. المستخدم {name} لديه النتائج: فعالية {eff}، مناعة {def_s}، تماسك {coh}. التشخيص الحالي: {diag}. {hist_context}. قدم نصيحة سننية عميقة تربط المسار التاريخي بالواقع الحالي في 3 أسطر."""
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ عذراً، تعذر التحليل الذكي: {str(e)}"

# --- 5. محرك الحساب السنني (الأصلي) ---
def calculate_sunan_scores(data):
    raw_points = (data['production_ratio'] * 80) + (data['completed_projects'] * 20)
    quality_factor = data['quality_score'] / 5
    eff = (raw_points * quality_factor) - (data['daily_hours'] * 3) + 15
    eff = max(min(round(eff, 2), 100), 5)
    
    total = data['original_posts'] + data['replies'] + 0.1
    def_s = round(((data['original_posts'] / total) * 60) + ((data['emotional_stability'] / 10) * 40), 2)
    coh = min(round((data['task_alignment'] * 10) * (1.2 if data['is_team'] else 1.0), 2), 100)
    
    if eff < 45: diag = "🛑 ركود حضاري"
    elif def_s < 45: diag = "⚠️ جهد مكشوف"
    elif coh < 45: diag = "🧩 تشتت الجهد"
    else: diag = "🌟 استواء حضاري"
    return eff, def_s, coh, diag

# --- 6. بناء الواجهة (إرجاع لوحة التحكم الكاملة) ---
df_history = load_history_data() # تحميل البيانات فورياً

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2331/2331718.png", width=60)
    st.header("🎛️ لوحة التحكم")
    user_name = st.text_input("الاسم", "مبادر")
    st.markdown("---")
    with st.expander("⏱️ الفعالية", expanded=True):
        d_hours = st.slider("ساعات الهدر", 0.0, 16.0, 4.0)
        p_ratio = st.slider("نسبة الإنتاج", 0.0, 1.0, 0.2)
        projects = st.number_input("مشاريع منجزة", 0, 50, 0)
        quality = st.select_slider("الجودة", [1, 2, 3, 4, 5], value=3)
    with st.expander("🛡️ المناعة"):
        orig = st.number_input("بصمة خاصة", 0, 50, 1)
        replies = st.number_input("ردود", 0, 100, 5)
        emotion = st.slider("هدوء نفسي", 0, 10, 5)
    with st.expander("🤝 التماسك"):
        align = st.slider("وضوح الهدف", 0, 10, 5)
        team = st.checkbox("عمل جماعي")
    
    calc_btn = st.button("🔍 تحليل الموقف")

st.title("🕌 منصة السُّنَن الرقمية")

if 'res' not in st.session_state: st.session_state.res = None

if calc_btn:
    vals = {'daily_hours': d_hours, 'production_ratio': p_ratio, 'completed_projects': projects,
            'quality_score': quality, 'original_posts': orig, 'replies': replies,
            'emotional_stability': emotion, 'task_alignment': align, 'is_team': team}
    st.session_state.res = calculate_sunan_scores(vals)

if st.session_state.res:
    eff, def_s, coh, diag = st.session_state.res
    c1, c2 = st.columns([1.5, 1])
    
    with c1:
        fig = go.Figure(go.Scatterpolar(r=[eff, def_s, coh], theta=['الفعالية', 'المناعة', 'التماسك'], fill='toself', line_color='#1F618D'))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
        st.plotly_chart(fig, use_container_width=True)
        
    with c2:
        st.info(f"النتيجة: {user_name}\n\n{diag}")
        
        # الزر الأول: استشارة AI (مع تمرير df_history)
        if st.button("✨ استشارة المرشد السنني (AI)"):
            with st.spinner('جاري تحليل المسار...'):
                advice = get_ai_consultation(user_name, eff, def_s, coh, diag, df_history)
                st.markdown(f'<div class="ai-box"><b>بصيرة المسار التاريخي:</b><br>{advice}</div>', unsafe_allow_html=True)
        
        # الزر الثاني: حفظ النتيجة
        if st.button("💾 حفظ النتيجة في السجل"):
            if save_to_google_sheet(user_name, eff, def_s, coh, diag):
                st.balloons()
                st.success("تم الحفظ وتحديث المسار التاريخي")
                st.rerun()

# --- 7. الرسوم التاريخية والمتصدرين ---
st.markdown("---")
col_hist, col_top = st.columns([2, 1])

with col_hist:
    if not df_history.empty:
        user_hist = df_history[df_history['Name'].str.strip() == user_name.strip()]
        if not user_hist.empty:
            st.subheader(f"📈 المسار التاريخي لـ {user_name}")
            user_hist['Date'] = pd.to_datetime(user_hist['Date'])
            st.line_chart(user_hist.set_index('Date')[['Score_Eff', 'Score_Def', 'Score_Coh']])

with col_top:
    st.subheader("🏆 المتصدرون")
    if not df_history.empty:
        top = df_history.groupby('Name')['Score_Eff'].max().sort_values(ascending=False).head(5)
        st.table(top)

```

### 💡 ما الذي فعلناه لإصلاح كل شيء؟

1. **إرجاع لوحة التحكم:** أعدت بناء الـ `Sidebar` بكل الـ `sliders` والـ `expanders` التي كانت موجودة سابقاً.
2. **إصلاح تعارض الأزرار:** المشكلة في الكود السابق كانت في دالة الـ AI، قمت بتصحيحها لتستقبل البيانات التاريخية بشكل صحيح دون التسبب في انهيار التطبيق.
3. **إرجاع التنسيق البصري:** أضفت كود الـ CSS من جديد ليعود الخط العربي الجميل والتنسيق من اليمين لليسار.

**يرجى تجربة الكود الآن، وسيعود كل شيء كما كان وأفضل بإذن الله!**
