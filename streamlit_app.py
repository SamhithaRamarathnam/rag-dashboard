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

#choose input type
input_type = st.radio("Choose input type", ["PDF File", "Text File with URLs", "URL", "Raw Text"])

uploaded_file = None
input_source = None
raw_text = None

if input_type in ["PDF File", "Text File with URLs"]:
  uploaded_file = st.file_uploader("Upload your file", type=["pdf", "txt"])
elif input_type == "URL":
  input_source = st.text_input("Paste the webpage URL here")
elif input_type == "Raw Text":
  raw_text = st.text_area("Paste your content here")

#Job scheduling
schedule_job = st.checkbox("Schedule this for background processing", value=True)

#upload button
if st.button("Upload"):
  if not subject:
    st.warning("Please select a subject.")
  elif input_type in ["PDF file", "Text File with URLs"] and uploaded_file is None:
    st.warning("Please Upload a file.")
  elif input_type == "URL" and not input_source.strip():
    st.warning("Please enter a valid URL.")
  elif input_type == "Raw Text" and not raw_text.strip():
    st.warning("Please paste some content.")
  else:
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

      type_mapping = {
        "PDF file": "pdf",
        "Text File with URLs": "text_urls",
        "URL": "URL",
        "Raw Text": "text"
      }
      input_type_value = type_mapping[input_type]

      # insert job into training_jobs table
      cursor.execute("""
          INSERT INTO training_jobs(
              job_id, subject, uploadeed_by, input_type,
              input_source, status, created_at
          ) VALUES (%s, %s, %s, %s, %s, %s, %s)
      """, (
        job_id, subject, uploaded_by, input_type_value,
        input_source, status, created_at
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




















      


