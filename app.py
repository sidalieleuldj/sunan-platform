import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title="منصة السُّنَن الرقمية",
    page_icon="🕌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS (التصميم المستقر) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; }
    
    /* الحفاظ على الهيكل LTR */
    .stApp { direction: ltr; }

    /* تعريب النصوص والعناوين */
    .stMarkdown, p, h1, h2, h3, h4, h5, span, div[data-testid="stMetricValue"], .stAlert, .stDataFrame {
        text-align: right !important; direction: rtl !important;
    }
    
    /* ضبط السلايدر */
    .stSlider > label {
        width: 100%; text-align: right !important; direction: rtl !important; display: block;
    }
    
    /* القائمة الجانبية */
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] h1 {
        text-align: right !important; direction: rtl !important;
    }
    
    input { text-align: right !important; direction: rtl !important; }
    .stButton>button { width: 100%; background-color: #1F618D; color: white; border-radius: 8px; }
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

# --- 🧹 الفلتر الذكي لإصلاح الأرقام ---
def smart_fix_score(val):
    try:
        s_val = str(val).replace(',', '.')
        score = float(s_val)
        if score > 100: score = score / 10 # إصلاح الفاصلة الضائعة
        if score > 100: score = 100.0 # سقف النتيجة
        return score
    except:
        return 0.0

def load_history_data():
    sheet = get_google_sheet()
    if sheet:
        try:
            data = sheet.get_all_records()
            df = pd.DataFrame(data)
            if not df.empty:
                cols = ['Score_Eff', 'Score_Def', 'Score_Coh']
                for c in cols:
                    if c in df.columns:
                        df[c] = df[c].apply(smart_fix_score)
            return df
        except Exception as e:
            st.error(f"خطأ: {e}")
    return pd.DataFrame()

# --- 4. محرك السنن ---
def calculate_sunan_scores(data):
    raw_points = (data['production_ratio'] * 80) + (data['completed_projects'] * 20)
    quality_factor = data['quality_score'] / 5
    eff = (raw_points * quality_factor) - (data['daily_hours'] * 3) + 15
    eff = max(min(round(eff, 2), 100), 5)
    
    total = data['original_posts'] + data['replies'] + 0.1
    def_s = round(((data['original_posts'] / total) * 60) + ((data['emotional_stability'] / 10) * 40), 2)
    
    coh = min(round((data['task_alignment'] * 10) * (1.2 if data['is_team'] else 1.0), 2), 100)
    
    if eff < 45: 
        diag = "🛑 ركود حضاري: تستهلك أكثر مما تنتج."
        acts = ["خصص ساعة عمل مركزة.", "قلل التصفح."]
    elif def_s < 45: 
        diag = "⚠️ جهد مكشوف: مستنزف في ردود الأفعال."
        acts = ["توقف عن الجدال.", "ابنِ محتواك الخاص."]
    elif coh < 45: 
        diag = "🧩 تشتت الجهد: ذرة قوية لكن منعزلة."
        acts = ["ابحث عن شريك.", "اربط عملك بهدف."]
    else: 
        diag = "🌟 حالة متوازنة (الاستواء الحضاري): استمر."
        acts = ["زكاة العلم تعليمه.", "وثّق تجربتك."]
        
    return eff, def_s, coh, diag, acts

# --- 5. واجهة المستخدم ---
if 'res' not in st.session_state: st.session_state['res'] = None

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2331/2331718.png", width=60)
    st.header("🎛️ لوحة التحكم")
    
    st.markdown("### 👤 بيانات المستخدم")
    user_name = st.text_input("سجل اسمك هنا", "مبادر")
    st.markdown("---")
    
    with st.expander("⏱️ 1. محور الفعالية", expanded=True):
        d_hours = st.slider("ساعات التصفح", 0.0, 16.0, 4.0)
        p_ratio = st.slider("نسبة الإنتاج", 0.0, 1.0, 0.2)
        projects = st.number_input("مشاريع مكتملة", 0, 50, 0)
        quality = st.select_slider("جودة الأثر", options=[1, 2, 3, 4, 5], value=3)
        
    with st.expander("🛡️ 2. محور المناعة"):
        orig = st.number_input("بصمتك (أصلي)", 0, 50, 1)
        replies = st.number_input("ردود أفعال", 0, 100, 5)
        emotion = st.slider("الهدوء النفسي", 0, 10, 5)
        
    with st.expander("🤝 3. محور التماسك"):
        align = st.slider("وضوح الهدف", 0, 10, 5)
        team = st.checkbox("عمل جماعي")
        
    calc_btn = st.button("🔍 تحليل الموقف")

st.title("🕌 منصة السُّنَن الرقمية")

if calc_btn:
    vals = {
        'daily_hours': d_hours, 'production_ratio': p_ratio, 'completed_projects': projects,
        'quality_score': quality, 'original_posts': orig, 'replies': replies,
        'emotional_stability': emotion, 'task_alignment': align, 'is_team': team
    }
    st.session_state['res'] = calculate_sunan_scores(vals)

if st.session_state['res']:
    eff, def_s, coh, diag, acts = st.session_state['res']
    
    col_chart, col_info = st.columns([1.5, 1])
    with col_chart:
        fig = go.Figure(go.Scatterpolar(r=[eff, def_s, coh], theta=['الفعالية', 'المناعة', 'التماسك'], fill='toself', line_color='#1F618D'))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), margin=dict(t=40, b=40))
        st.plotly_chart(fig, use_container_width=True)
        
    with col_info:
        st.subheader(f"نتيجة: {user_name}")
        st.info(diag)
        if acts:
            for a in acts: st.warning(f"💡 {a}")
            
    if st.button("💾 تدوين النتيجة"):
        if user_name and user_name != "مبادر":
            if save_to_google_sheet(user_name, eff, def_s, coh, diag):
                st.balloons(); st.success(f"تم التسجيل لـ {user_name}")
        else:
            st.error("يرجى كتابة الاسم.")

st.markdown("---")

# --- 6. لوحة المتصدرين (بتصميم الجدول الأنيق) ---
st.header("🏆 لوحة الشرف")

if st.button("🔄 تحديث القائمة"):
    df = load_history_data()
    if not df.empty:
        try:
            # 1. عرض السجل الكامل (اختياري، في الأسفل)
            with st.expander("📂 عرض سجل البيانات التفصيلي"):
                st.dataframe(df, use_container_width=True)
            
            # 2. جدول المتصدرين المخصص
            if 'Name' in df.columns and 'Score_Eff' in df.columns:
                leaderboard = df.groupby('Name')['Score_Eff'].max().sort_values(ascending=False).head(3)
                
                # إعداد كود HTML للجدول
                html_table = """
                <table style="width:100%; direction: rtl; text-align: right; border-collapse: collapse; font-family: 'Cairo', sans-serif;">
                  <thead>
                    <tr style="background-color: #f0f2f6; border-bottom: 2px solid #1F618D;">
                      <th style="padding: 10px; color: #1F618D;">المركز</th>
                      <th style="padding: 10px; color: #1F618D;">الاسم</th>
                      <th style="padding: 10px; color: #1F618D;">الفعالية</th>
                    </tr>
                  </thead>
                  <tbody>
                """
                
                medals = ["🥇 الأول", "🥈 الثاني", "🥉 الثالث"]
                
                # تعبئة الجدول
                for i, (name, score) in enumerate(leaderboard.items()):
                    medal = medals[i] if i < 3 else f"{i+1}"
                    row_color = "#ffffff" # خلفية بيضاء
                    html_table += f"""
                    <tr style="background-color: {row_color}; border-bottom: 1px solid #ddd;">
                      <td style="padding: 12px; font-weight: bold;">{medal}</td>
                      <td style="padding: 12px;">{name}</td>
                      <td style="padding: 12px; font-weight: bold; color: #2e7bcf;">{score:.1f}%</td>
                    </tr>
                    """
                
                html_table += "</tbody></table>"
                
                # عرض الجدول
                st.markdown(html_table, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"خطأ: {e}")
    else:
        st.info("السجل فارغ.")
