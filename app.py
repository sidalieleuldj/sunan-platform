import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import random
import time

# --- 1. CONFIGURATION INITIALE ---
st.set_page_config(page_title="منصة السُّنَن الرقمية - Enterprise", page_icon="🕌", layout="wide")

if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# --- 2. THEME & CSS (Mode Sombre/Clair) ---
bg_color = "#121212" if st.session_state.dark_mode else "#f8f9fa"
text_color = "#ffffff" if st.session_state.dark_mode else "#000000"
card_bg = "#1e1e1e" if st.session_state.dark_mode else "#ffffff"
slider_track = "linear-gradient(90deg, #ffd700 0%, #4caf50 100%)" if st.session_state.dark_mode else "linear-gradient(90deg, #c9a44c 0%, #1e5631 100%)"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
    
    html, body, [class*="css"] {{ font-family: 'Cairo', sans-serif; text-align: right; background-color: {bg_color}; color: {text_color}; }}
    .stApp {{ direction: ltr; background-color: {bg_color}; }}
    .stMarkdown, p, h1, h2, h3, h4, label, .stAlert {{ text-align: right !important; direction: rtl !important; color: {text_color} !important; }}
    
    /* Slider Pro */
    div[data-baseweb="slider"] > div:first-child > div:first-child {{ background: {slider_track} !important; border-radius: 10px; }}
    div[role="slider"] {{ background-color: #1e5631 !important; border: 2px solid #c9a44c !important; box-shadow: 0 0 10px rgba(0,0,0,0.2); }}
    
    /* Cartes & Boites */
    .ai-analysis-card {{ background: {card_bg}; border-right: 8px solid #c9a44c; border-radius: 15px; padding: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); margin-top: 10px; }}
    .challenge-box {{ background-color: {"#262626" if st.session_state.dark_mode else "#fcf3cf"}; border-radius: 15px; padding: 20px; border: 1px solid #c9a44c; margin-top: 20px; margin-bottom: 20px; }}
    .task-item {{ background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; margin-bottom: 8px; border-right: 4px solid #1e5631; font-weight: bold; }}
    
    /* Boutons */
    .stButton>button {{ background: linear-gradient(135deg, #1e5631 0%, #2d8a4e 100%) !important; color: white !important; border-radius: 10px !important; border: none; font-weight: bold; }}
    
    /* KPI Gauges Background */
    .js-plotly-plot .plotly .modebar {{ display: none !important; }}
</style>
""", unsafe_allow_html=True)

# --- 3. FONCTIONS UTILITAIRES ---
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

# --- 4. FONCTIONS PRO (Jauges & Logique) ---
def create_gauge(value, title):
    """Création d'une jauge style tableau de bord"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title, 'font': {'size': 20, 'color': "#c9a44c", 'family': "Cairo"}},
        number = {'font': {'color': text_color}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': text_color},
            'bar': {'color': "#1e5631"},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "#c9a44c",
            'steps': [
                {'range': [0, 45], 'color': 'rgba(255, 69, 0, 0.2)'},
                {'range': [45, 75], 'color': 'rgba(255, 215, 0, 0.2)'},
                {'range': [75, 100], 'color': 'rgba(30, 86, 49, 0.2)'}],
        }))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': text_color, 'family': "Cairo"}, height=220, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def get_badges(eff, def_s, history_df, user):
    """Logique de Gamification"""
    badges = []
    if eff >= 90: badges.append("🎖️ جنرال الفعالية (Score 90+)")
    if def_s >= 90: badges.append("🛡️ الحصن المنيع (Score 90+)")
    
    if not history_df.empty:
        user_entries = history_df[history_df['Name'] == user]
        count = len(user_entries)
        if count >= 1: badges.append("🌱 بداية الغيث (أول تحليل)")
        if count >= 5: badges.append("🔥 المثابر (5 تحليلات)")
        if count >= 10: badges.append("💎 الخبير الرقمي (10+ تحليلات)")
        
    return badges if badges else ["👋 مرحبًا بك في رحلة الوعي"]

def get_resources(diag):
    """Pharmacie Numérique : Suggestions selon le diagnostic"""
    resources = {
        "🛑 ركود حضاري": [
            "📖 كتاب: العادات الذرية (James Clear)",
            "📱 أداة: تطبيق 'Forest' لقتل التشتت",
            "💡 نصيحة: ابدأ بمهمة واحدة فقط لمدة 5 دقائق"
        ],
        "⚠️ جهد مكشوف": [
            "📖 كتاب: العمل العميق (Cal Newport)",
            "📺 فيديو: 'دوبامين ديتوكس' (Dopamine Detox)",
            "💡 نصيحة: ألغِ جميع الإشعارات غير البشرية"
        ],
        "🧩 تشتت الجهد": [
            "📖 كتاب: الشيء الوحيد (Gary Keller)",
            "📝 أداة: مصفوفة أيزنهاور للأولويات",
            "💡 نصيحة: اربط كل مهمة بهدفك الأكبر"
        ]
    }
    return resources.get(diag, ["📖 كتاب: رقائق القرآن", "💡 نصيحة: استمر في القياس للتحسين"])

def ai_logic_analysis(eff, def_s, coh):
    if eff < 40: return f"انخفاض حاد في 'الفعالية' ({eff}%). محرك الإنتاج يحتاج لإعادة ضبط فوري."
    if def_s < 45: return f"حالة 'انكشاف دفاعي' ({def_s}%). أنت تستهلك أكثر مما تنتج. طبق قاعدة 1:3."
    if coh < 50: return f"تعاني من 'تشتت الغاية' ({coh}%). جهودك مبعثرة، اربطها بهدف واحد."
    if eff >= 75 and def_s >= 70: return "مرحلة **النضج الحضاري**. توازن ممتاز بين البناء والحماية."
    return f"أداء متوازن ({eff}%) ولكن يحتاج لقفزة نوعية في جودة المخرجات."

def get_30_day_challenge(diag):
    challenges = {
        "🛑 ركود حضاري": ["الأسبوع 1: صيام رقمي جزئي.", "الأسبوع 2: إنتاج مخرج واحد يومياً.", "الأسبوع 3: إنهاء المعلقات.", "الأسبوع 4: قياس الأثر."],
        "⚠️ جهد مكشوف": ["الأسبوع 1: الصمت الرقمي.", "الأسبوع 2: التدوين العميق.", "الأسبوع 3: تحويل الجدل لنصيحة.", "الأسبوع 4: المبادرة الخاصة."],
        "🧩 تشتت الجهد": ["الأسبوع 1: هدف واحد فقط.", "الأسبوع 2: العمل العميق (Deep Work).", "الأسبوع 3: التخلص من الزوائد.", "الأسبوع 4: تقييم البوصلة."]
    }
    return challenges.get(diag, ["الأسبوع 1: تعليم العلم.", "الأسبوع 2: التوثيق.", "الأسبوع 3: بناء الفريق.", "الأسبوع 4: التوسع."])

# --- 5. SIDEBAR (CONTROLES) ---
daily_tasks = [
    "📅 سُنّة اليوم: اعتزل الجدال الرقمي لمدة 24 ساعة.",
    "✍️ سُنّة اليوم: حوّل فكرة قرأتها إلى منشور بصياغتك.",
    "🔇 سُنّة اليوم: نظف قائمة متابعتك من 3 حسابات سلبية.",
    "⏳ سُنّة اليوم: لا تلمس هاتفك أول 20 دقيقة من الصباح.",
    "🚀 سُنّة اليوم: ساعة تركيز كاملة (بدون نت)."
]

if 'res' not in st.session_state: st.session_state['res'] = None

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2331/2331718.png", width=70)
    user_name = st.text_input("اسم المستخدم", "مبادر")
    
    # Toggle Dark Mode
    if st.button("🌓 تغيير المظهر (ليلي/نهاري)"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

    # Mission du jour
    st.markdown("---")
    st.info(random.choice(daily_tasks))
    st.markdown("---")

    # Inputs
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
    
    calc_btn = st.button("🚀 تحليل البيانات الشامل")

# --- 6. DASHBOARD PRINCIPAL ---
st.title("🕌 منصة السُّنَن الرقمية | Enterprise")

# Chargement données pour historique et badges
df_all = load_history_data()

if calc_btn:
    st.toast('جاري معالجة البيانات...', icon='⏳')
    time.sleep(0.5)
    st.toast('تم إنشاء لوحة القيادة!', icon='✅')

    # Calculs
    raw_points = (p_ratio * 80) + (projects * 20)
    eff = max(min(round((raw_points * (quality / 5)) - (d_hours * 3) + 15, 2), 100), 5)
    total = orig + replies + 0.1
    def_s = round(((orig / total) * 60) + ((emotion / 10) * 40), 2)
    coh = min(round((align * 10) * (1.2 if team else 1.0), 2), 100)
    
    if eff < 45: diag = "🛑 ركود حضاري"
    elif def_s < 45: diag = "⚠️ جهد مكشوف"
    elif coh < 45: diag = "🧩 تشتت الجهد"
    else: diag = "🌟 استواء حضاري"
    
    st.session_state['res'] = (eff, def_s, coh, diag)

if st.session_state['res']:
    eff, def_s, coh, diag = st.session_state['res']
    ai_report = ai_logic_analysis(eff, def_s, coh)
    challenge_tasks = get_30_day_challenge(diag)
    
    # Calcul des badges et ressources
    my_badges = get_badges(eff, def_s, df_all, user_name)
    my_resources = get_resources(diag)

    # --- SECTION 1: JAUGES (KPIs) ---
    st.markdown("### 📊 مؤشرات الأداء الحيوية")
    k1, k2, k3 = st.columns(3)
    with k1: st.plotly_chart(create_gauge(eff, "الفعالية"), use_container_width=True)
    with k2: st.plotly_chart(create_gauge(def_s, "المناعة"), use_container_width=True)
    with k3: st.plotly_chart(create_gauge(coh, "التماسك"), use_container_width=True)

    # --- SECTION 2: GAMIFICATION & RESSOURCES (NOUVEAU) ---
    st.markdown("---")
    col_badge, col_res = st.columns(2)
    
    with col_badge:
        st.subheader("🎖️ لوحة الإنجازات")
        for b in my_badges:
            st.success(b) # Affichage vert
            
    with col_res:
        st.subheader(f"💊 صيدلية الحلول ({diag})")
        for r in my_resources:
            st.info(r) # Affichage bleu

    # --- SECTION 3: CHALLENGE & RADAR ---
    st.markdown("---")
    col_c, col_r = st.columns([1.2, 1])
    
    with col_c:
        st.markdown(f"""
        <div class="challenge-box">
            <h3 style="margin-top:0; color:#d35400;">🚀 مسار الـ 30 يوماً ({diag})</h3>
            {"".join([f'<div class="task-item">📅 {t}</div>' for t in challenge_tasks])}
        </div>
        """, unsafe_allow_html=True)
        
        # Bouton Téléchargement
        report_txt = f"تقرير السنن الرقمية\nالمستخدم: {user_name}\nالتاريخ: {datetime.now().date()}\n---\nالنتائج:\nالفعالية: {eff}%\nالمناعة: {def_s}%\nالتماسك: {coh}%\nالإنجازات: {', '.join(my_badges)}"
        st.download_button("📥 تحميل التقرير الكامل (TXT)", data=report_txt, file_name=f"Sunan_Report_{user_name}.txt")

    with col_r:
        fig = go.Figure(go.Scatterpolar(r=[eff, def_s, coh, eff], theta=['الفعالية', 'المناعة', 'التماسك', 'الفعالية'], fill='toself', fillcolor='rgba(30, 86, 49, 0.2)', line=dict(color='#c9a44c', width=4)))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=text_color))
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown(f'<div class="ai-analysis-card"><h4>🧠 التحليل الذكي</h4><p>{ai_report}</p></div>', unsafe_allow_html=True)
        
        if st.button("💾 حفظ في قاعدة البيانات"):
            sheet = get_google_sheet()
            if sheet and user_name != "مبادر":
                sheet.append_row([user_name, datetime.now().strftime("%Y-%m-%d %H:%M"), str(eff), str(def_s), str(coh), diag])
                st.balloons(); st.success("تم الحفظ!")

# --- 7. HISTORIQUE ---
st.markdown("---")
if not df_all.empty:
    ca, cb = st.columns([2, 1])
    with ca:
        st.subheader("📈 تتبع المسار الزمني")
        u_df = df_all[df_all['Name'] == user_name].sort_values('Date')
        if not u_df.empty:
            fig_h = go.Figure(go.Scatter(x=u_df['Date'], y=u_df['Score_Eff'], line=dict(color='#c9a44c', width=3), fill='tozeroy', fillcolor='rgba(30, 86, 49, 0.1)'))
            fig_h.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=text_color), yaxis=dict(range=[0, 100]))
            st.plotly_chart(fig_h, use_container_width=True)
    with cb:
        st.subheader("🏆 لوحة الشرف")
        top = df_all.groupby('Name')['Score_Eff'].max().sort_values(ascending=False).head(5).reset_index()
        top.columns = ['المبادر', 'النقاط']
        st.dataframe(top, use_container_width=True, hide_index=True)
