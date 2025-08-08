import streamlit as st
import sqlite3
import pandas as pd

DB_FILE = "donations.db"

# ---------- قاعدة البيانات ----------
def init_db():
    conn = sqlite3.connect(DB_FILE)
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
    conn.close()

def add_donation(store_name, location, collected, amount, notes):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO donations (store_name, location, collected, amount, notes) VALUES (?, ?, ?, ?, ?)",
              (store_name, location, collected, amount, notes))
    conn.commit()
    conn.close()

def get_donations():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM donations", conn)
    conn.close()
    return df

def update_donation(record_id, store_name, location, collected, amount, notes):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""UPDATE donations SET store_name=?, location=?, collected=?, amount=?, notes=? WHERE id=?""",
              (store_name, location, collected, amount, notes, record_id))
    conn.commit()
    conn.close()

def delete_donation(record_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM donations WHERE id=?", (record_id,))
    conn.commit()
    conn.close()

# ---------- تهيئة ----------
init_db()
st.set_page_config(page_title="سجل القجج", layout="centered")
st.title("📦 سجل القجج - المضيف")

# ---------- إضافة ----------
with st.form("add_form"):
    st.subheader("➕ إضافة قجة جديدة")
    col1, col2 = st.columns(2)
    store_name = col1.text_input("اسم المحل")
    location = col2.text_input("الموقع")
    collected = col1.selectbox("هل سُحبت القجة؟", ["لا", "نعم"])
    amount = col2.number_input("قيمة المبلغ بالقجة", min_value=0.0, step=1.0)
    notes = st.text_area("ملاحظات")
    submit = st.form_submit_button("إضافة")

if submit and store_name:
    add_donation(store_name, location, collected, amount, notes)
    st.success("✅ تمت الإضافة بنجاح")

# ---------- عرض ----------
st.subheader("📋 قائمة القجج")
df = get_donations()
if df.empty:
    st.info("لا توجد بيانات بعد.")
else:
    st.dataframe(df)

# ---------- تعديل ----------
if not df.empty:
    st.subheader("✏ تعديل بيانات")
    record_id = st.selectbox("اختر السجل للتعديل", df["id"])
    record = df[df["id"] == record_id].iloc[0]

    new_store = st.text_input("اسم المحل", record["store_name"])
    new_location = st.text_input("الموقع", record["location"])
    new_collected = st.selectbox("هل سُحبت القجة؟", ["لا", "نعم"], index=["لا", "نعم"].index(record["collected"]))
    new_amount = st.number_input("قيمة المبلغ بالقجة", value=float(record["amount"]), step=1.0)
    new_notes = st.text_area("ملاحظات", record["notes"])

    if st.button("💾 حفظ التعديلات"):
        update_donation(record_id, new_store, new_location, new_collected, new_amount, new_notes)
        st.success("✅ تم التعديل بنجاح")

# ---------- حذف ----------
if not df.empty:
    st.subheader("🗑 حذف بيانات")
    delete_id = st.selectbox("اختر السجل للحذف", df["id"], key="delete")
    if st.button("🚨 تأكيد الحذف"):
        delete_donation(delete_id)
        st.warning("❌ تم حذف السجل")
