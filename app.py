import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import random
import time

# --- 1. CONFIGURATION INITIALE ---
st.set_page_config(page_title="منصة السُّنَن الرقمية - Ultimate", page_icon="🕌", layout="wide")

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
    .metric-card {{ background-color: {card_bg}; border: 1px solid #333; padding: 15px; border-radius: 10px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
    
    /* Cycle de vie */
    .cycle-bar {{ width: 100%; height: 20px; background-color: #ddd; border-radius: 10px; margin-top: 10px; overflow: hidden; }}
    .cycle-fill {{ height: 100%; text-align: center; color: white; font-size: 12px; line-height: 20px; transition: width 1s ease-in-out; }}
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

# --- 4. LOGIQUE & INTELLIGENCE ---
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

def calculate_time_audit(daily_hours):
    """Calcule le coût d'opportunité du temps perdu (Bennabi's Equation)"""
    monthly_hours = daily_hours * 30
    books_lost = int(monthly_hours / 7) # Moyenne 7h pour un livre moyen
    quran_khatm = int(monthly_hours / 15) # Moyenne 15h pour une Khatma rapide
    return monthly_hours, books_lost, quran_khatm

def get_civilization_stage(eff, def_s, coh):
    """Détermine le stade civilisationnel (Ibn Khaldoun Cycle)"""
    avg = (eff + def_s + coh) / 3
    if avg < 30: return "🌑 مرحلة السبات (Mawat)", 15, "#7f8c8d"
    if avg < 50: return "🌱 مرحلة الميلاد (Milad)", 40, "#27ae60"
    if avg < 75: return "🚀 مرحلة الصعود (Ourooj)", 70, "#f39c12"
    if avg < 90: return "🏰 مرحلة الاستواء (Istiwâ)", 90, "#2980b9"
    return "⚖️ مرحلة الرشد (Rochd)", 100, "#8e44ad"

def get_resources(diag):
    resources = {
        "🛑 التشيؤ (Chosification)": ["📖 كتاب: مشكلة الثقافة (مالك بن نبي)", "💡 نصيحة: ارفع نقاشاتك من الأشياء إلى الأفكار"],
        "🌪️ الهدر الزمني": ["📖 كتاب: قيمة الزمن عند العلماء", "💡 نصيحة: طبق قانون التراكم (ابنِ على عمل الأمس)"],
        "🛑 ركود حضاري": ["📖 كتاب: العادات الذرية", "📱 أداة: تطبيق Forest"],
        "⚠️ جهد مكشوف": ["📖 كتاب: العمل العميق", "📺 فيديو: Dopamine Detox"],
        "🌟 فعالية سننية": ["📖 كتاب: شروط النهضة", "💡 نصيحة: ابدأ في توريث تجربتك"]
    }
    return resources.get(diag, ["📖 كتاب: رقائق القرآن", "💡 نصيحة: استمر في القياس"])

# --- 5. SIDEBAR ---
daily_tasks = ["📅 سُنّة اليوم: اعتزل الجدال الرقمي.", "✍️ سُنّة اليوم: حوّل فكرة لمنشور.", "🧱 سُنّة اليوم: أكمل عملاً بدأت فيه بالأمس."]

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
    
    st.markdown("### 🧠 المعايير السننية")
    idea_focus = st.select_slider("💡 محور التركيز (بنابي)", options=["عالم الأشياء", "عالم الأشخاص", "عالم الأفكار"], value="عالم الأشخاص")
    accumulation = st.slider("🧱 التراكمية (برغوث)", 0, 10, 5, help="هل يبني يومك على أمسك؟")

    with st.expander("⚙️ المعايير الرقمية", expanded=False):
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
st.title("🕌 منصة السُّنَن الرقمية | Ultimate Ed.")

df_all = load_history_data()

if calc_btn:
    st.toast('جاري حساب معادلة الزمن...', icon='⏳')
    time.sleep(0.5)
    
    # CALCULS
    focus_map = {"عالم الأشياء": 0.5, "عالم الأشخاص": 0.9, "عالم الأفكار": 1.4}
    bennabi_factor = focus_map[idea_focus]
    berghouth_factor = 0.8 + (accumulation / 25)

    raw_points = (p_ratio * 80) + (projects * 20)
    eff = max(min(round(((raw_points * (quality / 5)) - (d_hours * 3) + 15) * berghouth_factor, 2), 100), 5)
    
    total_int = orig + replies + 0.1
    def_s = max(min(round((((orig / total_int) * 60) + ((emotion / 10) * 40)) * bennabi_factor, 2), 100), 5)
    
    coh = min(round(((align * 10) * (1.2 if team else 1.0)) + (10 if idea_focus == "عالم الأفكار" and accumulation > 7 else 0), 2), 100)
    
    if idea_focus == "عالم الأشياء": diag = "🛑 التشيؤ (Chosification)"
    elif accumulation < 3: diag = "🌪️ الهدر الزمني"
    elif eff < 45: diag = "🛑 ركود حضاري"
    elif def_s < 45: diag = "⚠️ جهد مكشوف"
    else: diag = "🌟 فعالية سننية"
    
    st.session_state['res'] = (eff, def_s, coh, diag, d_hours)

if st.session_state['res']:
    eff, def_s, coh, diag, d_h = st.session_state['res']
    
    # 1. TIME AUDIT (NOUVEAU) - Équation du temps de Bennabi
    lost_h, lost_books, lost_khatm = calculate_time_audit(d_h)
    
    st.markdown("### ⏳ تدقيق الزمن (معادلة بن نبي)")
    c1, c2, c3 = st.columns(3)
    c1.metric("الساعات المهدرة شهرياً", f"{int(lost_h)}h", delta="- وقت ضائع", delta_color="inverse")
    c2.metric("كتب ضائعة", f"{lost_books} كتاب", delta="فرصة معرفية", delta_color="off")
    c3.metric("ختمات قرآن ضائعة", f"{lost_khatm} ختمة", delta="فرصة روحية", delta_color="off")
    
    st.markdown("---")

    # 2. CIVILIZATION CYCLE (NOUVEAU) - Cycle d'Ibn Khaldoun
    stage_name, stage_val, stage_color = get_civilization_stage(eff, def_s, coh)
    st.markdown(f"### 🔄 موقعك في الدورة الحضارية: {stage_name}")
    st.markdown(f"""
        <div class="cycle-bar">
            <div class="cycle-fill" style="width: {stage_val}%; background-color: {stage_color};">{stage_val}%</div>
        </div>
        <p style="font-size:0.9em; opacity:0.7;">الميلاد -> الصعود -> الاستواء -> الرشد</p>
    """, unsafe_allow_html=True)

    # 3. KPIs Classiques
    st.markdown("---")
    k1, k2, k3 = st.columns(3)
    with k1: st.plotly_chart(create_gauge(eff, "الفعالية"), use_container_width=True)
    with k2: st.plotly_chart(create_gauge(def_s, "المناعة"), use_container_width=True)
    with k3: st.plotly_chart(create_gauge(coh, "التماسك"), use_container_width=True)

    # 4. Rapport & Comparatif
    col_c, col_r = st.columns([1.2, 1])
    with col_c:
        my_res = get_resources(diag)
        st.markdown(f'<div class="challenge-box"><h3 style="color:#d35400;">🚀 خطة الإنقاذ ({diag})</h3>{"".join([f"<div class=task-item>💊 {r}</div>" for r in my_res])}</div>', unsafe_allow_html=True)
        
    with col_r:
        fig = go.Figure(go.Scatterpolar(r=[eff, def_s, coh, eff], theta=['الفعالية', 'المناعة', 'التماسك', 'الفعالية'], fill='toself', fillcolor='rgba(30, 86, 49, 0.2)', line=dict(color='#c9a44c', width=4)))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color=text_color))
        st.plotly_chart(fig, use_container_width=True)
        
        if st.button("💾 حفظ في الأرشيف الحضاري"):
            sheet = get_google_sheet()
            if sheet and user_name != "مبادر":
                sheet.append_row([user_name, datetime.now().strftime("%Y-%m-%d"), str(eff), str(def_s), str(coh), diag])
                st.balloons(); st.success("تم التوثيق!")

# --- 7. RANKING RELATIF & HISTORIQUE (CORRIGÉ) ---
st.markdown("---")
if not df_all.empty:
    st.subheader("📊 موقعك مقارنة بالجيل الرقمي")
    
    # Filtrage sécurisé (supprime les espaces inutiles)
    clean_user = user_name.strip()
    u_df = df_all[df_all['Name'] == clean_user].copy()
    
    # Calcul des moyennes globales
    avg_cohort = df_all['Score_Eff'].mean()
    
    # 1. Comparaison (Ranking)
    col_rank1, col_rank2 = st.columns(2)
    with col_rank1:
        st.info(f"متوسط فعالية الجيل: {int(avg_cohort)}%")
    
    with col_rank2:
        if not u_df.empty:
            my_max = u_df['Score_Eff'].max()
            diff = int(my_max - avg_cohort)
            if diff > 0:
                st.success(f"أنت تتفوق على المتوسط بـ +{diff}% 🚀")
            else:
                st.warning(f"تحتاج لزيادة الجهد لتلحق بالركب ({diff}%)")
        else:
            st.warning("سجل بياناتك الأولى لتظهر في التصنيف")

    # 2. Graphique Historique (CORRIGÉ)
    if not u_df.empty:
        # TRI OBLIGATOIRE par date pour éviter le chaos visuel
        u_df = u_df.sort_values('Date')
        
        fig_h = go.Figure()
        
        # Ajout de la courbe avec 'lines+markers' pour voir même un seul point
        fig_h.add_trace(go.Scatter(
            x=u_df['Date'], 
            y=u_df['Score_Eff'],
            mode='lines+markers', # Correction critique : affiche les points même s'il n'y en a qu'un
            name='الفعالية',
            line=dict(color='#c9a44c', width=3),
            marker=dict(size=8, color='#1e5631'), # Points verts sur ligne dorée
            fill='tozeroy', 
            fillcolor='rgba(201, 164, 76, 0.1)'
        ))

        fig_h.update_layout(
            title="📈 مسار تطورك التاريخي",
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)', 
            font=dict(color=text_color, family="Cairo"),
            yaxis=dict(range=[0, 100], title="نقطة الفعالية"),
            xaxis=dict(title="التاريخ"),
            hovermode="x unified"
        )
        st.plotly_chart(fig_h, use_container_width=True)
    else:
        st.info("👋 لا توجد بيانات تاريخية لهذا الاسم بعد. اضغط على 'حفظ' لبدء الرسم البياني.")
else:
    st.warning("⚠️ قاعدة البيانات فارغة حالياً.")

