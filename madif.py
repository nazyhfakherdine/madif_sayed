import streamlit as st
import sqlite3
import pandas as pd

DB_FILE = "donations.db"
PASSWORD = "zeina"  # كلمة المرور المطلوبة

# ---------- قاعدة البيانات ----------
def init_db():
    with sqlite3.connect(DB_FILE, timeout=10) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS donations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_name TEXT,
                location TEXT,
                collected TEXT,
                amount REAL,
                notes TEXT
            )
        """)
        conn.commit()

def add_donation(store_name, location, collected, amount, notes):
    with sqlite3.connect(DB_FILE, timeout=10) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO donations (store_name, location, collected, amount, notes) VALUES (?, ?, ?, ?, ?)",
            (store_name, location, collected, amount, notes)
        )
        conn.commit()

def get_donations():
    with sqlite3.connect(DB_FILE, timeout=10) as conn:
        df = pd.read_sql_query("SELECT * FROM donations ORDER BY id", conn)
    if "amount" in df.columns:
        df["amount"] = df["amount"].fillna(0.0)
    if "notes" in df.columns:
        df["notes"] = df["notes"].fillna("")
    return df

def update_donation(record_id, store_name, location, collected, amount, notes):
    with sqlite3.connect(DB_FILE, timeout=10) as conn:
        c = conn.cursor()
        c.execute(
            "UPDATE donations SET store_name=?, location=?, collected=?, amount=?, notes=? WHERE id=?",
            (store_name, location, collected, amount, notes, record_id)
        )
        conn.commit()

def delete_donation(record_id):
    with sqlite3.connect(DB_FILE, timeout=10) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM donations WHERE id=?", (record_id,))
        conn.commit()

# ---------- تهيئة ----------
init_db()
st.set_page_config(page_title="سجل القجج", layout="centered")
st.title("📦 سجل القجج - المضيف")

# ---------- إضافة ----------
with st.form("add_form"):
    st.subheader("➕ إضافة قجة جديدة")
    col1, col2 = st.columns(2)
    store_name = col1.text_input("اسم المحل", key="add_store")
    location = col2.text_input("الموقع", key="add_location")
    collected = col1.selectbox("هل سُحبت القجة؟", ["لا", "نعم"], key="add_collected")
    amount = col2.number_input("قيمة المبلغ بالقجة", min_value=0.0, step=1.0, key="add_amount")
    notes = st.text_area("ملاحظات", key="add_notes")
    password_add = st.text_input("كلمة المرور", type="password", key="pass_add")
    submit = st.form_submit_button("إضافة")

if submit and store_name:
    if password_add == PASSWORD:
        try:
            add_donation(store_name, location, collected, amount, notes)
            st.success("✅ تمت الإضافة بنجاح")
            st.rerun()
        except Exception as e:
            st.error(f"خطأ أثناء الإضافة: {e}")
    else:
        st.error("❌ كلمة المرور غير صحيحة. العملية أُلغيت.")

# ---------- عرض ----------
st.subheader("📋 قائمة القجج")
df = get_donations()
if df.empty:
    st.info("لا توجد بيانات بعد.")
else:
    st.dataframe(df)

def make_options(df):
    return [f"{row['store_name']} — {row['location']} (#{row['id']})" for _, row in df.iterrows()]

# ---------- تعديل ----------
if not df.empty:
    st.subheader("✏ تعديل بيانات")
    options = make_options(df)
    selected = st.selectbox("اختر المحل للتعديل", options, key="edit_select")
    sel_idx = options.index(selected)
    record = df.iloc[sel_idx]
    record_id = int(record["id"])

    new_store = st.text_input("اسم المحل (تعديل)", value=record["store_name"], key=f"edit_store_{record_id}")
    new_location = st.text_input("الموقع (تعديل)", value=record["location"], key=f"edit_location_{record_id}")
    collected_index = 0 if str(record["collected"]).strip() == "لا" else 1
    new_collected = st.selectbox("هل سُحبت القجة؟ (تعديل)", ["لا", "نعم"], index=collected_index, key=f"edit_collected_{record_id}")
    new_amount = st.number_input("قيمة المبلغ بالقجة (تعديل)", value=float(record["amount"]), step=1.0, key=f"edit_amount_{record_id}")
    new_notes = st.text_area("ملاحظات (تعديل)", value=record["notes"], key=f"edit_notes_{record_id}")
    password_edit = st.text_input("كلمة المرور للتعديل", type="password", key=f"pass_edit_{record_id}")

    if st.button("💾 حفظ التعديلات", key=f"save_btn_{record_id}"):
        if password_edit == PASSWORD:
            try:
                update_donation(record_id, new_store, new_location, new_collected, new_amount, new_notes)
                st.success("✅ تم التعديل بنجاح")
                st.rerun()
            except Exception as e:
                st.error(f"فشل التعديل: {e}")
        else:
            st.error("❌ كلمة المرور غير صحيحة. العملية أُلغيت.")

# ---------- حذف ----------
if not df.empty:
    st.subheader("🗑 حذف بيانات")
    del_options = make_options(df)
    selected_del = st.selectbox("اختر المحل للحذف", del_options, key="delete_select")
    del_idx = del_options.index(selected_del)
    del_id = int(df.iloc[del_idx]["id"])
    password_del = st.text_input("كلمة المرور للحذف", type="password", key=f"pass_delete_{del_id}")

    if st.button("🚨 تأكيد الحذف", key=f"delete_btn_{del_id}"):
        if password_del == PASSWORD:
            try:
                delete_donation(del_id)
                st.warning(f"❌ تم حذف السجل #{del_id}")
                st.rerun()
            except Exception as e:
                st.error(f"فشل الحذف: {e}")
        else:
            st.error("❌ كلمة المرور غير صحيحة. العملية أُلغيت.")
# ---------- نهاية التطبيق ----------