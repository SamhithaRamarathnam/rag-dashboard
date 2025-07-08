import streamlit as st
import os
import psycopg2
from datetime import datetime
import uuid

DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ["DB_PORT"]
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASS = os.environ["DB_PASS"]

def get_connection():
  return psycopg2.connect(
    host = DB_HOST,
    port = DB_PORT,
    dbname = DB_NAME,
    user = DB_USER,
    password = DB_PASS
  )

st.set_page_config(page_title="Upload Content", layout="centered")
st.title("Upload Content")

#choose subject
subject = st.selectbox("Select subject", ["Physics", "Computer Science", "Electrical Engineering"])
subject = st.selectbox("Select subject", subject_options, index=0)

#choose input type
input_type = st.radio("Choose input type", ["PDF File", "Text File with URLs", "URL", "Raw Text"])
selected_input_type = st.radio("Select how you want to upload content:", list(input_types.keys()), index=None)

uploaded_file = None
input_source = None
raw_text = None

if selected_input_type == "PDF File":
    uploaded_file = st.file_uploader("Upload your PDF file", type=["pdf"])
elif selected_input_type == "Text File with URLs":
    uploaded_file = st.file_uploader("Upload your .txt file", type=["txt"])
elif selected_input_type == "URL":
    input_source = st.text_input("Paste the webpage URL here")
elif selected_input_type == "Raw Text":
    raw_text = st.text_area("Paste your content here")

#Job scheduling
schedule_job = st.checkbox("Schedule this for background processing", value=False)

scheduled_datetime = None
if schedule_job:
  scheduled_date = st.date_input("Select run date")
  scheduled_time = st.time_input("Select run time")
  scheduled_datetime = datetime.combine(scheduled_date, scheduled_time)

all_inputs_filled = (
  subject != "Select a subject" and
  selected_input_type is not None and(
    (selected_input_type in ["PDF File", "Text File with URLs"] and uploaded_file is not None) or
    (selected_input_type == "URL" and input_source and input_source.strip()) or
    (selected_input_type == "Raw Text" and raw_text and raw_text.strip())
  )
)
#upload button
if not all_inputs_filled:
  st.button("Upload",disabled=True)
else:
  if st.button("Upload"):
    try:
      conn = get_connection()
      cursor = conn.cursor()

      job_id = str(uuid.uuid4())
      uploaded_by = "Samhitha"
      created_at = datetime.utcnow()
      status = "pending" if schedule_job else "immediate"

      #for tracking
      if input_type in ["PDF file", "Text File with URLs"]:
        input_source = uploaded_file.name
      elif input_type == "Raw Text":
        input_source = "raw_text_" + raw_text.strip()[:30]

      input_type_value = input_types[selected_input_type]

      # insert job into training_jobs table
      cursor.execute("""
          INSERT INTO training_jobs(
              job_id, subject, uploaded_by, input_type,
              input_source, status, created_at, scheduled_for
          ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
      """, (
        job_id, subject, uploaded_by, input_type_value,
        input_source, status, created_at, scheduled_datetime
      ))

      conn.commit()
      cursor.close()
      conn.close()

      st.success("Upload successful!")
      st.info(f"""
**Subject:** {subject}
**Job Type:** {status.upper()}
**Job ID:** {job_id}
""")
    except Exception as e:
      st.error(f"Upload failed: {e}")




















      


