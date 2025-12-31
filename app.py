import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="منصة السُّنَن الرقمية", page_icon="🕌", layout="wide")

# --- 2. CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; }
    .stApp { direction: ltr; }
    .stMarkdown, p, h1, h2, h3, h4, h5, div[data-testid="stMetricValue"] { text-align: right !important; direction: rtl !important; }
    div[data-testid="stTable"] { direction: rtl; }
</style>
""", unsafe_allow_html=True)

# --- 3. وظائف الاتصال ---
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
        data = sheet.get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=['Name', 'Date', 'Score_Eff', 'Score_Def', 'Score_Coh', 'Diagnosis'])
            # تحويل الأرقام
            for col in ['Score_Eff', 'Score_Def', 'Score_Coh']:
                df[col] = pd.to_numeric(df[col].str.replace(',', '.'), errors='coerce').fillna(0)
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            return df
    return pd.DataFrame()

# --- 4. واجهة التحكم (Sidebar) ---
with st.sidebar:
    st.header("🎛️ الإعدادات")
    user_name = st.text_input("الاسم", "مبادر")
    eff_val = st.slider("الفعالية", 0, 100, 50)
    def_val = st.slider("المناعة", 0, 100, 50)
    coh_val = st.slider("التماسك", 0, 100, 50)
    diag_text = "🌟 استواء حضاري" if eff_val > 50 else "🛑 ركود حضاري"
    
    if st.button("💾 حفظ النتيجة"):
        sheet = get_google_sheet()
        if sheet and user_name != "مبادر":
            row = [user_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), str(eff_val), str(def_val), str(coh_val), diag_text]
            sheet.append_row(row)
            st.success("تم الحفظ!")
            st.rerun()

st.title("🕌 منصة السُّنَن الرقمية")

# --- 5. عرض الرسوم البيانية التاريخية ---
st.header(f"📈 المسار التاريخي: {user_name}")
df_all = load_history_data()

if not df_all.empty:
    user_df = df_all[df_all['Name'] == user_name].sort_values('Date')
    if not user_df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=user_df['Date'], y=user_df['Score_Eff'], name="الفعالية", line=dict(color='#1F618D')))
        fig.add_trace(go.Scatter(x=user_df['Date'], y=user_df['Score_Def'], name="المناعة", line=dict(color='#E74C3C')))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("لا توجد بيانات مسجلة لهذا الاسم بعد.")

# --- 6. جدول المتصدرين ---
st.markdown("---")
st.header("🏆 قائمة المتصدرين")
if st.button("🔄 تحديث القائمة"):
    df_all = load_history_data()

if not df_all.empty:
    # حساب أعلى نتيجة لكل مستخدم
    leaderboard = df_all.groupby('Name')['Score_Eff'].max().sort_values(ascending=False).reset_index()
    leaderboard.columns = ['الاسم', 'أعلى درجة فعالية']
    st.table(leaderboard.head(5))
