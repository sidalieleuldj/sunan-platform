import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="منصة السُّنَن الرقمية", page_icon="🕌", layout="wide")

# --- 2. التصميم الفاخر (CSS المطور للذكاء الاصطناعي) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Cairo', sans-serif; 
        text-align: right; 
        background-color: #f4f7f6;
    }
    .stApp { direction: ltr; }
    .stMarkdown, p, h1, h2, h3, h4, .stAlert { text-align: right !important; direction: rtl !important; }
    
    /* تصميم السلايدر (الأخضر والذهبي) */
    div[role="slider"] { background-color: #1e5631 !important; border: 3px solid #c9a44c !important; }
    div[data-baseweb="slider"] > div:first-child > div:first-child {
        background: linear-gradient(90deg, #c9a44c 0%, #1e5631 100%) !important;
    }
    
    /* تصميم الأزرار الفاخرة */
    .stButton>button {
        background: linear-gradient(135deg, #1e5631 0%, #2d8a4e 100%) !important;
        color: white !important; border-radius: 12px !important; font-weight: bold !important;
        padding: 15px 30px !important; border: none !important; transition: 0.4s ease;
        box-shadow: 0 4px 15px rgba(30, 86, 49, 0.2);
    }
    .stButton>button:hover { transform: translateY(-3px); box-shadow: 0 8px 25px rgba(30, 86, 49, 0.4); }
    
    /* صندوق تحليل الذكاء الاصطناعي المستقبلي */
    .ai-analysis-card {
        background: rgba(255, 255, 255, 0.9);
        border-right: 10px solid #c9a44c;
        border-radius: 20px;
        padding: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        margin-top: 20px;
        position: relative;
        overflow: hidden;
    }
    .ai-analysis-card::before {
        content: "AI Analysis";
        position: absolute; top: -10px; left: -10px;
        font-size: 40px; color: rgba(30, 86, 49, 0.03); font-weight: 900;
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

# خوارزمية الذكاء الاصطناعي للتحليل العميق
def ai_logic_engine(eff, def_s, coh):
    if eff > 80 and def_s > 80:
        return "🤖 تحليل الذكاء الاصطناعي: أنت الآن في مرحلة **'النضج الحضاري'**. توازنك بين الإنتاج وحماية وقتك يجعلك نموذجاً ملهماً. استمر في توثيق منهجيتك."
    elif eff < 40:
        return "🤖 تحليل الذكاء الاصطناعي: نلاحظ وجود **'هدر طاقة رقمي'**. ساعات التصفح تبتلع قدرتك على الإنجاز. القاعدة الذهبية الآن: (لا تفتح المنصات إلا بعد إنهاء أهم مهمتين في يومك)."
    elif def_s < 50:
        return "🤖 تحليل الذكاء الاصطناعي: تشخيصنا يشير إلى **'انكشاف دفاعي'**. ردود أفعالك تطغى على أفعالك الأصلية. النصيحة: قلل استجابتك للتنبيهات وركز على بناء 'أصل رقمي' خاص بك."
    elif coh < 50:
        return "🤖 تحليل الذكاء الاصطناعي: يوجد **'تشتت في البوصلة'**. مجهودك قوي لكنه غير مترابط. النصيحة: حدد 'كلمة واحدة' تصف هدفك لهذا الشهر واجعل كل أعمالك تدور حولها."
    else:
        return "🤖 تحليل الذكاء الاصطناعي: أداء مستقر ولكن **'نمطي'**. تحتاج إلى 'قفزة نوعية' عبر تعلم مهارة جديدة أو العمل في بيئة جماعية لكسر الرتابة."

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

# --- 4. واجهة التحكم (Sidebar) ---
if 'res' not in st.session_state: st.session_state['res'] = None

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2331/2331718.png", width=80)
    st.title("لوحة التحكم")
    user_name = st.text_input("اسم المبادر", "زائر")
    st.markdown("---")
    with st.expander("⏱️ الفعالية", expanded=True):
        d_hours = st.slider("ساعات التصفح", 0.0, 16.0, 4.0)
        p_ratio = st.slider("نسبة الإنتاج", 0.0, 1.0, 0.2)
        projects = st.number_input("المشاريع المنجزة", 0, 50, 0)
        quality = st.select_slider("جودة المخرج", [1, 2, 3, 4, 5], value=3)
    with st.expander("🛡️ المناعة"):
        orig = st.number_input("منشورات أصلية", 0, 50, 1)
        replies = st.number_input("ردود", 0, 100, 5)
        emotion = st.slider("الاتزان", 0, 10, 5)
    with st.expander("🤝 التماسك"):
        align = st.slider("وضوح الغاية", 0, 10, 5)
        team = st.checkbox("عمل جماعي")
    calc_btn = st.button("🔍 تحليل البيانات الذكي")

st.title("🕌 منصة السُّنَن الرقمية")

# --- 5. العرض الرئيسي والنتائج ---
if calc_btn:
    vals = {'daily_hours': d_hours, 'production_ratio': p_ratio, 'completed_projects': projects,
            'quality_score': quality, 'original_posts': orig, 'replies': replies,
            'emotional_stability': emotion, 'task_alignment': align, 'is_team': team}
    st.session_state['res'] = calculate_sunan_scores(vals)

if st.session_state['res']:
    eff, def_s, coh, diag = st.session_state['res']
    ai_report = ai_logic_engine(eff, def_s, coh)
    
    c1, c2 = st.columns([1.5, 1])
    with c1:
        # الرسم البياني القطبي الفاخر
        fig = go.Figure(go.Scatterpolar(
            r=[eff, def_s, coh, eff], 
            theta=['الفعالية', 'المناعة', 'التماسك', 'الفعالية'], 
            fill='toself', fillcolor='rgba(45, 138, 78, 0.2)',
            line=dict(color='#c9a44c', width=4)
        ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), margin=dict(t=40, b=40))
        st.plotly_chart(fig, use_container_width=True)
    
    with c2:
        # بطاقة النتيجة
        st.markdown(f"""
            <div style="background: white; padding: 25px; border-radius: 20px; border-right: 10px solid #1e5631; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                <h2 style="color: #1e5631; margin: 0;">{user_name}</h2>
                <h4 style="color: #2d8a4e; margin-top: 5px;">{diag}</h4>
            </div>
            <div class="ai-analysis-card">
                <p style="color: #333; line-height: 1.8; font-size: 1.1em;">{ai_report}</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("💾 توثيق النتيجة في السجل الحضاري"):
            sheet = get_google_sheet()
            if sheet and user_name != "زائر":
                sheet.append_row([user_name, datetime.now().strftime("%Y-%m-%d %H:%M"), str(eff), str(def_s), str(coh), diag])
                st.balloons(); st.success("تم الحفظ بنجاح!")

# --- 6. الإحصائيات التاريخية والمتصدرون ---
st.markdown("---")
df_all = load_history_data()

if not df_all.empty:
    col_a, col_b = st.columns([1.6, 1])
    with col_a:
        st.header(f"📈 مسار التطور: {user_name}")
        u_df = df_all[df_all['Name'] == user_name].sort_values('Date')
        if not u_df.empty:
            fig_h = go.Figure(go.Scatter(x=u_df['Date'], y=u_df['Score_Eff'], 
                                       line=dict(color='#1e5631', width=4), 
                                       fill='tozeroy', fillcolor='rgba(30, 86, 49, 0.1)'))
            fig_h.update_layout(hovermode="x unified", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_h, use_container_width=True)
        else: st.info("لا توجد بيانات مسجلة لهذا الاسم حتى الآن.")
        
    with col_b:
        st.header("🏆 قائمة المتصدرين")
        top = df_all.groupby('Name')['Score_Eff'].max().sort_values(ascending=False).head(5).reset_index()
        top.columns = ['المبادر', 'أعلى درجة %']
        st.table(top)
        if st.button("🔄 تحديث السجل"): st.rerun()
