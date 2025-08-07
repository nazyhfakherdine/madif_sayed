import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# إعداد الصفحة
st.set_page_config(page_title="نظام تسجيل القجات", layout="wide")
st.title("🧾 نظام تسجيل القجات")

# إعداد الاتصال مع Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
import json
creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

client = gspread.authorize(creds)

SHEET_NAME = "donation_data"
sheet = client.open(SHEET_NAME).sheet1

# تحميل البيانات من الشيت
def load_data():
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# حفظ البيانات إلى الشيت
def save_data(df):
    sheet.clear()
    sheet.insert_row(["اسم المحل", "الموقع", "تم السحب", "المبلغ", "ملاحظات"], 1)
    for row in df.values.tolist():
        sheet.append_row(row)

# تحميل البيانات الحالية
data = load_data()

# تخزين رقم الصف المراد تعديله أو حذفه
if "edit_index" not in st.session_state:
    st.session_state.edit_index = None
if "delete_index" not in st.session_state:
    st.session_state.delete_index = None

# ---- النموذج ----
with st.form("donation_form", clear_on_submit=True):
    st.subheader("📝 إضافة / تعديل قجة")

    if st.session_state.edit_index is not None:
        row_data = data.iloc[st.session_state.edit_index]
        shop_name = st.text_input("اسم المحل", value=row_data["اسم المحل"])
        location = st.text_input("الموقع", value=row_data["الموقع"])
        collected = st.selectbox("هل تم سحب القجة؟", ["لا", "نعم"], index=1 if row_data["تم السحب"] == "نعم" else 0)
        amount = st.number_input("قيمة المبلغ (ل.ل)", min_value=0, step=1000, value=int(row_data["المبلغ"]))
        notes = st.text_area("ملاحظات", value=row_data["ملاحظات"])
    else:
        shop_name = st.text_input("اسم المحل")
        location = st.text_input("الموقع")
        collected = st.selectbox("هل تم سحب القجة؟", ["لا", "نعم"])
        amount = st.number_input("قيمة المبلغ (ل.ل)", min_value=0, step=1000)
        notes = st.text_area("ملاحظات")

    submit_btn = st.form_submit_button("💾 حفظ")

    if submit_btn:
        if not shop_name or not location:
            st.warning("يرجى إدخال اسم المحل والموقع.")
        else:
            new_data = {
                "اسم المحل": shop_name,
                "الموقع": location,
                "تم السحب": collected,
                "المبلغ": amount,
                "ملاحظات": notes
            }

            if st.session_state.edit_index is not None:
                data.iloc[st.session_state.edit_index] = new_data
                st.session_state.edit_index = None
                st.success("✅ تم تحديث البيانات.")
            else:
                data = pd.concat([data, pd.DataFrame([new_data])], ignore_index=True)
                st.success("✅ تم حفظ البيانات.")

            save_data(data)
            st.rerun()

# ---- واجهة البحث والترتيب ----
st.subheader("🔎 بحث وترتيب")

search_query = st.text_input("🔍 ابحث باسم المحل:")
filter_collected = st.selectbox("🗂️ فلترة حسب حالة القجة", ["الكل", "نعم", "لا"])
sort_order = st.radio("↕️ ترتيب حسب المبلغ", ["بدون ترتيب", "تصاعدي", "تنازلي"], horizontal=True)

filtered_data = data.copy()

# تطبيق البحث
if search_query:
    filtered_data = filtered_data[filtered_data["اسم المحل"].str.contains(search_query, case=False, na=False)]

# تطبيق الفلترة
if filter_collected != "الكل":
    filtered_data = filtered_data[filtered_data["تم السحب"] == filter_collected]

# تطبيق الترتيب
if sort_order == "تصاعدي":
    filtered_data = filtered_data.sort_values(by="المبلغ", ascending=True)
elif sort_order == "تنازلي":
    filtered_data = filtered_data.sort_values(by="المبلغ", ascending=False)

# ---- عرض البيانات ----
st.subheader("📊 قائمة القجات")

if filtered_data.empty:
    st.info("لا توجد بيانات مطابقة.")
else:
    for i in range(len(filtered_data)):
        row = filtered_data.iloc[i]
        original_index = data[data["اسم المحل"] == row["اسم المحل"]].index[0]  # للحصول على index الأصلي
        cols = st.columns((2, 2, 1, 1, 3, 1, 1))

        cols[0].markdown(f"**{row['اسم المحل']}**")
        cols[1].markdown(row["الموقع"])
        cols[2].markdown(row["تم السحب"])
        cols[3].markdown(f"{row['المبلغ']:,}")
        cols[4].markdown(row["ملاحظات"] or "-")

        if cols[5].button("✏️ تعديل", key=f"edit_{original_index}"):
            st.session_state.edit_index = original_index
            st.rerun()

        if cols[6].button("🗑️ حذف", key=f"delete_{original_index}"):
            st.session_state.delete_index = original_index

# ---- تأكيد الحذف ----
if st.session_state.delete_index is not None:
    with st.expander("⚠️ تأكيد الحذف", expanded=True):
        st.error("هل أنت متأكد أنك تريد حذف هذا السجل؟ لا يمكن التراجع بعد الحذف.")
        confirm_col1, confirm_col2 = st.columns(2)
        if confirm_col1.button("✅ نعم، احذف", key="confirm_delete"):
            data = data.drop(index=st.session_state.delete_index).reset_index(drop=True)
            save_data(data)
            st.session_state.delete_index = None
            st.success("🗑️ تم حذف السجل.")
            st.rerun()
        if confirm_col2.button("❌ إلغاء", key="cancel_delete"):
            st.session_state.delete_index = None
            st.info("تم إلغاء الحذف.")
