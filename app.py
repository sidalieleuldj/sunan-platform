import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import random

# --- 1. CONFIGURATION & ÉTAT ---
st.set_page_config(page_title="منصة السُّنَن الرقمية", page_icon="🕌", layout="wide")

if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# --- 2. MISSIONS QUOTIDIENNES (ورد اليوم) ---
daily_tasks = [
    "📅 سُنّة اليوم: اعتزل الجدال الرقمي لمدة 24 ساعة وانظر لأثره على صفاء ذهنك.",
    "✍️ سُنّة اليوم: حوّل فكرة واحدة قرأتها اليوم إلى منشور نافع بصياغتك الخاصة.",
    "🔇 سُنّة اليوم: قم بإلغاء متابعة 3 حسابات تسبب لك تشتتاً أو مشاعر سلبية.",
    "⏳ سُنّة اليوم: طبق قاعدة الـ 10 دقائق (لا تفتح هاتفك إلا بعد 10 دقائق من الاستيقاظ).",
    "🛡️ سُنّة اليوم: رُد على استفسار واحد في مجالك بنيّة زكاة العلم.",
    "🚀 سُنّة اليوم: خصص ساعة 'عمل عميق' (Deep Work) بدون أي إشعارات نهائياً."
]

# --- 3. DESIGN DYNAMIQUE (CSS) ---
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
    
    /* Design Sliders */
    div[data-baseweb="slider"] > div:first-child > div:first-child {{ background: {slider_track} !important; }}
    div[role="slider"] {{ background-color: #1e5631 !important; border: 3px solid #c9a44c !important; }}
    
    /* Design Cartes */
    .ai-analysis-card {{ background: {card_bg}; border-right: 10px solid #c9a44c; border-radius: 20px; padding: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); margin-top: 20px; }}
    .challenge-box {{ background-color: {"#2d2d2d" if st.session_state.dark_mode else "#fcf3cf"}; border-radius: 15px; padding: 25px; border: 2px solid #c9a44c; margin-top: 20px; margin-bottom: 20px; }}
    .task-item {{ background: rgba(255,255,255,0.1); padding: 12px; border-radius: 10px; margin-bottom: 10px; border-right: 5px solid #1e5631; font-weight: bold; }}
    
    /* Boutons */
    .stButton>button {{ background: linear-gradient(135deg, #1e5631 0%, #2d8a4e 100%) !important; color: white !important; border-radius: 12px !important; width: 100%; }}
</style>
""", unsafe_allow_html=True)

# --- 4. LOGIQUE DES DONNÉES ---
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

# --- 5. INTERFACE BARRE LATÉRALE (SIDEBAR) ---
if 'res' not in st.session_state: st.session_state['res'] = None

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2331/2331718.png", width=80)
    user_name = st.text_input("اسم المستخدم", "مبادر")
    
    # Bouton Mode Sombre
    if st.button("🌓 تبديل الوضع (ليلي/نهاري)"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

    # MISSION DU JOUR (NOUVEAU)
    st.markdown("---")
    st.info(random.choice(daily_tasks))

    st.markdown("---")
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
    calc_btn = st.button("🔍 تحليل وبناء الخطة")

# --- 6. AFFICHAGE PRINCIPAL ---
st.title("🕌 منصة السُّنَن الرقمية")

if calc_btn:
    # (Logique de calcul identique à ton code précédent)
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
    
    # Zone Challenge & Graphiques (comme avant avec adaptation couleurs)
    st.markdown(f'<div class="challenge-box"><h3>🚀 مسار الـ 30 يوماً للتغيير (حالة: {diag})</h3></div>', unsafe_allow_html=True)
    
    col_g, col_t = st.columns([1.5, 1])
    with col_g:
        fig = go.Figure(go.Scatterpolar(r=[eff, def_s, coh, eff], theta=['الفعالية', 'المناعة', 'التماسك', 'الفعالية'], fill='toself', fillcolor='rgba(30, 86, 49, 0.2)', line=dict(color='#c9a44c', width=4)))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=text_color))
        st.plotly_chart(fig, use_container_width=True)
    
    with col_t:
        st.markdown(f'<div class="ai-analysis-card"><h2>{user_name}</h2><h4>التشخيص: {diag}</h4></div>', unsafe_allow_html=True)
        if st.button("💾 توثيق النتيجة"):
            sheet = get_google_sheet()
            if sheet:
                sheet.append_row([user_name, datetime.now().strftime("%Y-%m-%d %H:%M"), str(eff), str(def_s), str(coh), diag])
                st.balloons()
