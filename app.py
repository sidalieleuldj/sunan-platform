import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import random
import time

# --- 1. CONFIGURATION INITIALE ---
st.set_page_config(page_title="منصة السُّنَن الرقمية - Civilisation Ed.", page_icon="🕌", layout="wide")

if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# --- 2. THEME & CSS ---
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
    
    /* Elements UI */
    div[data-baseweb="slider"] > div:first-child > div:first-child {{ background: {slider_track} !important; border-radius: 10px; }}
    div[role="slider"] {{ background-color: #1e5631 !important; border: 2px solid #c9a44c !important; }}
    .ai-analysis-card {{ background: {card_bg}; border-right: 8px solid #c9a44c; border-radius: 15px; padding: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); margin-top: 10px; }}
    .challenge-box {{ background-color: {"#262626" if st.session_state.dark_mode else "#fcf3cf"}; border-radius: 15px; padding: 20px; border: 1px solid #c9a44c; margin-top: 20px; margin-bottom: 20px; }}
    .task-item {{ background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; margin-bottom: 8px; border-right: 4px solid #1e5631; font-weight: bold; }}
    .stButton>button {{ background: linear-gradient(135deg, #1e5631 0%, #2d8a4e 100%) !important; color: white !important; border-radius: 10px !important; border: none; font-weight: bold; }}
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

# --- 4. LOGIQUE & DONNÉES ---
def create_gauge(value, title):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title, 'font': {'size': 20, 'color': "#c9a44c", 'family': "Cairo"}},
        number = {'font': {'color': text_color}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': text_color},
            'bar': {'color': "#1e5631"},
            'bgcolor': "rgba(0,0,0,0)", 'borderwidth': 2, 'bordercolor': "#c9a44c",
            'steps': [{'range': [0, 45], 'color': 'rgba(255, 69, 0, 0.2)'}, {'range': [45, 75], 'color': 'rgba(255, 215, 0, 0.2)'}, {'range': [75, 100], 'color': 'rgba(30, 86, 49, 0.2)'}],
        }))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': text_color, 'family': "Cairo"}, height=220, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def get_badges(eff, def_s, history_df, user):
    badges = []
    if eff >= 90: badges.append("🎖️ جنرال الفعالية (90+)")
    if def_s >= 90: badges.append("🛡️ الحصن المنيع (90+)")
    if not history_df.empty:
        count = len(history_df[history_df['Name'] == user])
        if count >= 1: badges.append("🌱 بداية الغيث")
        if count >= 5: badges.append("💎 الخبير الرقمي")
    return badges if badges else ["👋 مرحبًا بك في رحلة الوعي"]

def get_resources(diag):
    resources = {
        "🛑 التشيؤ (Chosification)": ["📖 كتاب: مشكلة الثقافة (مالك بن نبي)", "💡 نصيحة: ارفع نقاشاتك من الأشياء إلى الأفكار", "🚫 توقف عن متابعة أخبار السلع والاستهلاك"],
        "🌪️ الهدر الزمني": ["📖 كتاب: السنن النفسية لتطور الأمم", "💡 نصيحة: طبق قانون التراكم (ابنِ على عمل الأمس)", "⏳ راجع خطتك الخمسية"],
        "🛑 ركود حضاري": ["📖 كتاب: العادات الذرية", "📱 أداة: تطبيق Forest", "💡 نصيحة: ابدأ بمهمة واحدة لمدة 5 دقائق"],
        "⚠️ جهد مكشوف": ["📖 كتاب: العمل العميق", "📺 فيديو: Dopamine Detox", "💡 نصيحة: الصيام عن الجدال الرقمي"],
        "🧩 تشتت الجهد": ["📖 كتاب: الشيء الوحيد", "📝 أداة: مصفوفة أيزنهاور", "💡 نصيحة: اربط كل مهمة بهدف أكبر"],
        "🌟 فعالية سننية": ["📖 كتاب: شروط النهضة", "💡 نصيحة: ابدأ في توريث تجربتك للآخرين"]
    }
    return resources.get(diag, ["📖 كتاب: رقائق القرآن", "💡 نصيحة: استمر في القياس للتحسين"])

def get_30_day_challenge(diag):
    challenges = {
        "🛑 التشيؤ (Chosification)": ["أسبوع 1: مقاطعة أخبار المنتجات.", "أسبوع 2: قراءة فصل في الفكر يومياً.", "أسبوع 3: مجالسة أهل العلم.", "أسبوع 4: كتابة مقال فكري."],
        "🌪️ الهدر الزمني": ["أسبوع 1: توثيق إنجازات الأمس.", "أسبوع 2: ربط كل مهمة بسابقتها.", "أسبوع 3: إلغاء المشاريع المشتتة.", "أسبوع 4: بناء روتين تراكمي."],
        "🛑 ركود حضاري": ["أسبوع 1: صيام رقمي جزئي.", "أسبوع 2: إنتاج مخرج يومي.", "أسبوع 3: إنهاء المعلقات.", "أسبوع 4: قياس الأثر."],
        "⚠️ جهد مكشوف": ["أسبوع 1: الصمت الرقمي.", "أسبوع 2: التدوين العميق.", "أسبوع 3: تحويل الجدل لنصيحة.", "أسبوع 4: المبادرة الخاصة."],
        "🌟 فعالية سننية": ["أسبوع 1: تعليم العلم.", "أسبوع 2: التوثيق.", "أسبوع 3: بناء الفريق.", "أسبوع 4: التوسع."]
    }
    return challenges.get(diag, ["أسبوع 1: تحديد الأولويات.", "أسبوع 2: العمل العميق.", "أسبوع 3: التقييم.", "أسبوع 4: التخطيط."])

def ai_logic_analysis(eff, def_s, coh, idea_focus, accumulation):
    if idea_focus == "عالم الأشياء": return "تحذير: مؤشر 'التشيؤ' مرتفع جداً. الطاقة مستنزفة في الماديات دون روح."
    if accumulation < 3: return "خلل منهجي: تفتقد لقانون التراكمية. جهودك عبارة عن جزر منعزلة لا تبني مستقبلاً."
    if eff < 40: return "انخفاض حاد في الفعالية. محرك الإنتاج يحتاج لإعادة ضبط."
    if eff >= 80 and def_s >= 80: return "مرحلة **الرشاد الحضاري**. توازن مثالي بين عالم الأفكار والعمل التراكمي."
    return "أداء متوازن، لكن يحتاج لتركيز أكبر على الجودة والمعنى."

# --- 5. SIDEBAR (CONTROLES AVANCÉS) ---
daily_tasks = [
    "📅 سُنّة اليوم: اعتزل الجدال الرقمي لمدة 24 ساعة.",
    "✍️ سُنّة اليوم: حوّل فكرة قرأتها إلى منشور بصياغتك.",
    "🔇 سُنّة اليوم: نظف قائمة متابعتك من 3 حسابات سلبية.",
    "🧠 سُنّة اليوم: اقرأ 10 صفحات في كتاب فكري عميق.",
    "🧱 سُنّة اليوم: أكمل عملاً بدأت فيه بالأمس (التراكم)."
]

if 'res' not in st.session_state: st.session_state['res'] = None

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2331/2331718.png", width=70)
    user_name = st.text_input("اسم المستخدم", "مبادر")
    
    if st.button("🌓 تغيير المظهر"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

    st.markdown("---")
    st.info(random.choice(daily_tasks))
    st.markdown("---")
    
    # NOUVEAUX PARAMÈTRES (Bennabi & Berghouth)
    st.markdown("### 🧠 المعايير السننية")
    idea_focus = st.select_slider("💡 محور التركيز (بنابي)", options=["عالم الأشياء", "عالم الأشخاص", "عالم الأفكار"], value="عالم الأشخاص")
    accumulation = st.slider("🧱 التراكمية والبناء (برغوث)", 0, 10, 5, help="هل يبني يومك على أمسك؟")

    # Paramètres Classiques (Condensés)
    with st.expander("⚙️ المعايير الرقمية التفصيلية", expanded=False):
        d_hours = st.slider("ساعات التصفح", 0.0, 16.0, 4.0)
        p_ratio = st.slider("نسبة الإنتاج", 0.0, 1.0, 0.2)
        projects = st.number_input("مشاريع منجزة", 0, 50, 0)
        quality = st.select_slider("جودة المخرج", [1, 2, 3, 4, 5], value=3)
        orig = st.number_input("بصمة أصلية", 0, 50, 1)
        replies = st.number_input("ردود", 0, 100, 5)
        emotion = st.slider("الاتزان", 0, 10, 5)
        align = st.slider("وضوح الغاية", 0, 10, 5)
        team = st.checkbox("عمل جماعي")
    
    calc_btn = st.button("🚀 تحليل الوعي الحضاري")

# --- 6. DASHBOARD PRINCIPAL ---
st.title("🕌 منصة السُّنَن الرقمية | Civilisation Ed.")

df_all = load_history_data()

if calc_btn:
    st.toast('جاري معالجة القوانين السننية...', icon='⏳')
    time.sleep(0.5)
    st.toast('تم التحليل بنجاح!', icon='✅')

    # --- MOTEUR DE CALCUL AVANCÉ ---
    # 1. Facteurs Multiplicateurs
    focus_map = {"عالم الأشياء": 0.5, "عالم الأشخاص": 0.9, "عالم الأفكار": 1.4}
    bennabi_factor = focus_map[idea_focus]
    berghouth_factor = 0.8 + (accumulation / 25) # De 0.8 à 1.2

    # 2. Calcul des Scores
    # Efficacité modifiée par l'Accumulation (Berghouth)
    raw_points = (p_ratio * 80) + (projects * 20)
    base_eff = (raw_points * (quality / 5)) - (d_hours * 3) + 15
    eff = max(min(round(base_eff * berghouth_factor, 2), 100), 5)

    # Immunité modifiée par le Monde des Idées (Bennabi)
    total_int = orig + replies + 0.1
    base_def = ((orig / total_int) * 60) + ((emotion / 10) * 40)
    def_s = max(min(round(base_def * bennabi_factor, 2), 100), 5)

    # Cohésion (Synergie)
    coh = (align * 10) * (1.2 if team else 1.0)
    if idea_focus == "عالم الأفكار" and accumulation > 7: coh += 10 # Bonus Civilisationnel
    coh = min(round(coh, 2), 100)
    
    # 3. Diagnostic Dynamique
    if idea_focus == "عالم الأشياء": diag = "🛑 التشيؤ (Chosification)"
    elif accumulation < 3: diag = "🌪️ الهدر الزمني"
    elif eff < 45: diag = "🛑 ركود حضاري"
    elif def_s < 45: diag = "⚠️ جهد مكشوف"
    elif coh < 45: diag = "🧩 تشتت الجهد"
    else: diag = "🌟 فعالية سننية"
    
    st.session_state['res'] = (eff, def_s, coh, diag, idea_focus, accumulation)

if st.session_state['res']:
    eff, def_s, coh, diag, i_focus, accum = st.session_state['res']
    ai_report = ai_logic_analysis(eff, def_s, coh, i_focus, accum)
    challenge_tasks = get_30_day_challenge(diag)
    my_badges = get_badges(eff, def_s, df_all, user_name)
    my_resources = get_resources(diag)

    # Section 1: KPIs
    st.markdown("### 📊 مؤشرات القياس الحضاري")
    k1, k2, k3 = st.columns(3)
    with k1: st.plotly_chart(create_gauge(eff, "الفعالية (الكم)"), use_container_width=True)
    with k2: st.plotly_chart(create_gauge(def_s, "المناعة (الكيف)"), use_container_width=True)
    with k3: st.plotly_chart(create_gauge(coh, "التماسك (الغاية)"), use_container_width=True)

    # Section 2: Gamification & Solutions
    st.markdown("---")
    col_badge, col_res = st.columns(2)
    with col_badge:
        st.subheader("🎖️ لوحة الإنجازات")
        for b in my_badges: st.success(b)
    with col_res:
        st.subheader(f"💊 صيدلية الحلول ({diag})")
        for r in my_resources: st.info(r)

    # Section 3: Rapport & Radar
    st.markdown("---")
    col_c, col_r = st.columns([1.2, 1])
    with col_c:
        st.markdown(f'<div class="challenge-box"><h3 style="color:#d35400;">🚀 مسار التصحيح ({diag})</h3>{"".join([f"<div class=task-item>📅 {t}</div>" for t in challenge_tasks])}</div>', unsafe_allow_html=True)
        report_txt = f"تقرير السنن الرقمية\nالمستخدم: {user_name}\nالحالة: {diag}\nالتركيز: {i_focus}\nالتراكمية: {accum}/10\nالنتائج: فعالية {eff}, مناعة {def_s}"
        st.download_button("📥 تحميل التقرير (TXT)", data=report_txt, file_name=f"Sunan_Civilisation_{user_name}.txt")
    with col_r:
        fig = go.Figure(go.Scatterpolar(r=[eff, def_s, coh, eff], theta=['الفعالية', 'المناعة', 'التماسك', 'الفعالية'], fill='toself', fillcolor='rgba(30, 86, 49, 0.2)', line=dict(color='#c9a44c', width=4)))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=text_color))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f'<div class="ai-analysis-card"><h4>🧠 التحليل السنني</h4><p>{ai_report}</p></div>', unsafe_allow_html=True)
        if st.button("💾 حفظ في الأرشيف"):
            sheet = get_google_sheet()
            if sheet and user_name != "مبادر":
                sheet.append_row([user_name, datetime.now().strftime("%Y-%m-%d"), str(eff), str(def_s), str(coh), diag])
                st.balloons(); st.success("تم الحفظ!")

# --- 7. HISTORIQUE ---
st.markdown("---")
if not df_all.empty:
    st.subheader("📈 تتبع المسار الزمني")
    u_df = df_all[df_all['Name'] == user_name].sort_values('Date')
    if not u_df.empty:
        fig_h = go.Figure(go.Scatter(x=u_df['Date'], y=u_df['Score_Eff'], line=dict(color='#c9a44c', width=3), fill='tozeroy', fillcolor='rgba(30, 86, 49, 0.1)'))
        fig_h.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=text_color), yaxis=dict(range=[0, 100]))
        st.plotly_chart(fig_h, use_container_width=True)
