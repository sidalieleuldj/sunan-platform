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

# --- 2. التصميم العصري الشامل (Modern UI CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    
    /* الأساسيات */
    html, body, [class*="css"] { 
        font-family: 'Cairo', sans-serif; 
        text-align: right; 
        background-color: #f0f2f6;
    }
    
    .stApp { direction: ltr; }
    
    /* حاويات البطاقات العصرية */
    div[data-testid="stExpander"], .stMetric, div.stBlock {
        background: rgba(255, 255, 255, 0.8) !important;
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07) !important;
        backdrop-filter: blur(4px) !important;
        margin-bottom: 15px !important;
    }

    /* تحسين السلايدر - لمسة احترافية */
    div[role="slider"] {
        background-color: #1e5631 !important; 
        border: 3px solid #c9a44c !important;
        height: 22px !important; width: 22px !important;
    }
    div[data-baseweb="slider"] > div:first-child > div:first-child {
        background: linear-gradient(90deg, #c9a44c 0%, #1e5631 100%) !important;
        height: 8px !important;
    }

    /* الأزرار العصرية */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #1e5631 0%, #2d8a4e 100%) !important;
        color: white !important;
        border-radius: 15px !important;
        border: none !important;
        padding: 18px !important;
        font-weight: 800 !important;
        letter-spacing: 1px;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(30, 86, 49, 0.2) !important;
    }
    .stButton>button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 25px rgba(30, 86, 49, 0.4) !important;
    }

    /* العناوين والتقسيمات */
    h1 { color: #1e5631; font-weight: 800; border-right: 8px solid #c9a44c; padding-right: 15px; }
    .stMarkdown, p, span { direction: rtl !important; text-align: right !important; }
    
    /* الجداول */
    .stTable { 
        border-radius: 15px !important; 
        overflow: hidden !important; 
        direction: rtl !important; 
    }
</style>
""", unsafe_allow_html=True)

# --- 3. الدوال البرمجية (قاعدة البيانات والتحليل) ---
def get_google_sheet():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_info = dict(st.secrets["service_account"])
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)
        # تأكد أن هذا هو الـ ID الصحيح لملفك
        return client.open_by_key("1uXX-R40l8JQrPX8lcAxWbzxeeSs8Q5zaMF_DZ-R8TmE").sheet1
    except Exception as e:
        return None

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

def calculate_sunan_scores(data):
    # معادلة الفعالية الحضارية
    raw_points = (data['production_ratio'] * 80) + (data['completed_projects'] * 20)
    quality_factor = data['quality_score'] / 5
    eff = (raw_points * quality_factor) - (data['daily_hours'] * 3) + 15
    eff = max(min(round(eff, 2), 100), 5)
    
    # معادلة المناعة والتماسك
    total = data['original_posts'] + data['replies'] + 0.1
    def_s = round(((data['original_posts'] / total) * 60) + ((data['emotional_stability'] / 10) * 40), 2)
    coh = min(round((data['task_alignment'] * 10) * (1.2 if data['is_team'] else 1.0), 2), 100)
    
    # التشخيص
    if eff < 45: diag, acts = "🛑 ركود حضاري", ["خصص ساعة عمل مركزة.", "قلل التصفح السلبي."]
    elif def_s < 45: diag, acts = "⚠️ جهد مكشوف", ["توقف عن الجدال.", "ابنِ محتواك الخاص."]
    elif coh < 45: diag, acts = "🧩 تشتت الجهد", ["ابحث عن شريك عمل.", "اربط عملك بغاية كبرى."]
    else: diag, acts = "🌟 استواء حضاري", ["زكاة العلم تعليمه.", "وثّق تجربتك للآخرين."]
    
    return eff, def_s, coh, diag, acts

# --- 4. القائمة الجانبية (Input Panel) ---
if 'res' not in st.session_state: st.session_state['res'] = None

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2331/2331718.png", width=100)
    st.markdown("<h2 style='text-align: center; color: #1e5631;'>المختبر الرقمي</h2>", unsafe_allow_html=True)
    user_name = st.text_input("اسم المبادر", "زائر")
    st.markdown("---")
    
    with st.expander("⏱️ معايير الفعالية", expanded=True):
        d_hours = st.slider("ساعات التصفح", 0.0, 16.0, 4.0)
        p_ratio = st.slider("نسبة الإنتاج", 0.0, 1.0, 0.2)
        projects = st.number_input("مشاريع منجزة", 0, 50, 0)
        quality = st.select_slider("جودة المخرج", [1, 2, 3, 4, 5], value=3)
        
    with st.expander("🛡️ معايير المناعة"):
        orig = st.number_input("بصمة أصلية", 0, 50, 1)
        replies = st.number_input("تفاعلات", 0, 100, 5)
        emotion = st.slider("الاتزان النفسي", 0, 10, 5)
        
    with st.expander("🤝 معايير التماسك"):
        align = st.slider("وضوح الهدف", 0, 10, 5)
        team = st.checkbox("عمل جماعي")
    
    calc_btn = st.button("🔍 تشخيص الحالة")

# --- 5. الواجهة الرئيسية والعرض ---
st.title("🕌 منصة السُّنَن الرقمية")

if calc_btn:
    vals = {'daily_hours': d_hours, 'production_ratio': p_ratio, 'completed_projects': projects,
            'quality_score': quality, 'original_posts': orig, 'replies': replies,
            'emotional_stability': emotion, 'task_alignment': align, 'is_team': team}
    st.session_state['res'] = calculate_sunan_scores(vals)

if st.session_state['res']:
    eff, def_s, coh, diag, acts = st.session_state['res']
    
    col_chart, col_info = st.columns([1.4, 1])
    
    with col_chart:
        fig = go.Figure(go.Scatterpolar(
            r=[eff, def_s, coh, eff], 
            theta=['الفعالية', 'المناعة', 'التماسك', 'الفعالية'], 
            fill='toself', fillcolor='rgba(45, 138, 78, 0.2)',
            line=dict(color='#c9a44c', width=4)
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor="#eee")),
            margin=dict(t=20, b=20), paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col_info:
        st.markdown(f"""
            <div style="background: white; padding: 25px; border-radius: 20px; border-right: 10px solid #c9a44c; box-shadow: 0 10px 30px rgba(0,0,0,0.05);">
                <h2 style="color: #1e5631; margin-bottom: 5px;">{user_name}</h2>
                <h4 style="color: #2d8a4e;">{diag}</h4>
                <hr>
                <p style="color: #666;">التوصيات العملية:</p>
            </div>
        """, unsafe_allow_html=True)
        for a in acts: st.success(f"📌 {a}")
        
        if st.button("💾 توثيق النتيجة في السجل"):
            sheet = get_google_sheet()
            if sheet and user_name != "زائر":
                sheet.append_row([user_name, datetime.now().strftime("%Y-%m-%d %H:%M"), str(eff), str(def_s), str(coh), diag])
                st.balloons(); st.success("تم الحفظ بنجاح")
            else: st.warning("يرجى إدخال اسمك لحفظ النتيجة")

# --- 6. السجلات التاريخية والمتصدرين (عرض دائم) ---
st.markdown("<br><hr><br>", unsafe_allow_html=True)
df_hist = load_history_data()

if not df_hist.empty:
    c_hist, c_top = st.columns([1.4, 1])
    
    with c_hist:
        st.markdown(f"### 📈 المسار التاريخي لـ {user_name}")
        u_df = df_hist[df_hist['Name'] == user_name].sort_values('Date')
        if not u_df.empty:
            fig_h = go.Figure()
            fig_h.add_trace(go.Scatter(x=u_df['Date'], y=u_df['Score_Eff'], 
                                     mode='lines+markers', name="الفعالية", 
                                     line=dict(color='#1e5631', width=3),
                                     fill='tozeroy', fillcolor='rgba(30, 86, 49, 0.1)'))
            fig_h.update_layout(hovermode="x unified", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_h, use_container_width=True)
        else: st.info("لا توجد سجلات سابقة لهذا الاسم.")

    with c_top:
        st.markdown("### 🏆 قائمة المتصدرين")
        top = df_hist.groupby('Name')['Score_Eff'].max().sort_values(ascending=False).head(5).reset_index()
        top.columns = ['المبادر', 'أعلى فعالية %']
        st.table(top)
        if st.button("🔄 تحديث البيانات"): st.rerun()
