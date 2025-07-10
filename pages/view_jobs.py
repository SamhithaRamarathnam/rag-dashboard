import streamlit as st
import os
import psycopg2
import pandas as pd

DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ["DB_PORT"]
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASS = os.environ["DB_PASS"]

def get_connection():
  return psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASS
  )

st.set_page_config(page_title="View Jobs", layout="wide")
st.title("View Training Jobs")

subject_filter = st.selectbox("Filter by Subject", ["All", "Physics", "Computer Science", "Electrical Engineering"])
status_filter = st.selectbox("Filter by Status", ["All", "pending", "immediate"])

try:
  conn = get_connection()
  cursor = conn.cursor()

  query = "SELECT * FROM training_jobs"
  filters = []
  values = []

  if subject_filter != "All":
    filters.append("subject = %s")
    values.append(subject_filter)

  if status_filter != "All":
    filters.append("status = %s")
    values.append(status_filter)

  if filters:
    query += " WHERE " + " ADD ".join(filters)

  query += " ORDER BY created_at DESC"

  cursor.execute(query, tuple(values))
  rows = cursor.fetchall()

  columns = ["Job ID", "Subject", "Uploaded By", "Input Type", "Input Source", "Status", "Created At", "Scheduled For"]
  df = pd.DataFrame(rows, columns=columns)

  st.dataframe(df, use_container_width=True)

  cursor.close()
  conn.close()

except Exception as e:
  st.error(f"Failed to load training jobs: {e}")

