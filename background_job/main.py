import os
import psycopg2
import pg8000
import requests
import bs4
import uuid
import time
from datetime import datetime
from langchain_community.document_loaders import WebBaseLoader, PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.pgvector import PGVector
from langchain_core.documents import Document

DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ["DB_PORT"]
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASS = os.environ["DB_PASS"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
os.environ["USER_AGENT"] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

def get_pg8000_conn():
  return pg8000.connect(
    host=DB_HOST,
    port=int(DB_PORT),
    user=DB_USER,
    password=DB_PASS,
    database=DB_NAME
  )

def get_psycopg2_conn():
  return psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASS
  )

def ensure_subject_column():
  conn = get_pg8000_conn()
  cursor = conn.cursor()
  cursor.execute("""
      SELECT column_name 
      FROM information_schema.columns
      WHERE table_name = 'langchain_pg_embedding' AND column_name = 'subject';
  """)
  result = cursor.fetchone()
  if not result:
    cursor.execute("ALTER TABLE langchain_pg_embedding ADD COLUMN subject TEXT;")
  conn.commit()
  cursor.close()
  conn.close()

def update_subject_column_from_cmetadata():
  conn = get_pg8000_conn()
  cursor = conn.cursor()
  cursor.execute("""
      UPDATE langchain_pg_embedding
      SET subject = cmetadata->>'subject'
      WHERE cmetadata->>'subject' IS NOT NULL;
  """)
  conn.commit()
  cursor.close()
  conn.close()

def split_documents(docs):
  splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
  return splitter.split_documents(docs)

def embed_chunks(chunks, subject, collection_name="rag_chunks"):
  ensure_subject_column()
  docs = [Document(page_content=doc.page_content, metadata={"subject":subject}) for doc in chunks]
  store = PGVector(
    connection_string=f"postgresql+pg8000://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    use_jsonb=True,
    embedding_function=OpenAIEmbeddings(),
    engine_args={"creator":get_pg8000_conn},
    collection_name=collection_name,
  )
  for i in range(0, len(docs), 100):
    batch = docs[i:i+100]
    print(f"Embedding batch {i} to {i+len(batch)}")
    store.add_documents(batch)
    time.sleep(1)

  update_subject_column_from_cmetadata()
  print(f"Embedded {len(docs)} chunks for subject: {subject}")

def process_url_job(url, subject):
  print(f"Processing URL: {url}")
  loader = WebBaseLoader(
    web_paths=[url],
    bs_kwargs={"parse_only": bs4.SoupStrainer(class_=("mt-content-container", "title"))}
  )
  docs=loader.load()
  chunks = split_documents(docs)
  embed_chunks(chunks, subject)

def process_pdf_job(file_path, subject):
  print(f"Processing PDF: {file_path}")
  loader = PyMuPDFLoader(file_path)
  docs = loader.load()
  chunks = split_documents(docs)
  embed_chunks(chunks, subject)

def process_text_file_with_urls(file_path, subject):
  with open(file_path, "r") as f:
    urls = [line.strip() for line in f if line.strip()]
  print(f"Processeing {len(urls)} urls from file: {file_path}")
  for url in urls:
    process_url_job(url, subject)

def process_raw_text_job(text, subject):
  print(f"Processing raw text ({len(text)} characters)")
  doc = Document(page_content=text)
  chunks = split_documents([doc])
  embed_chunks(chunks, subject)

def main(request):
  run_job_processor_internal()

def run_job_processor_internal():
  print("\n Starting background job processor...\n")
  conn = get_psycopg2_conn()
  cursor = conn.cursor()
  cursor.execute("""
      SELECT job_id, subject, uploaded_by, input_type, input_source
      FROM training_jobs
      WHERE status = 'pending'
      ORDER BY created_at
  """)
  jobs = cursor.fetchall()
  
  if not jobs:
    print("No pending jobs.")
    return
  for job in jobs:
    job_id, subject, uploaded_by, input_type, input_source = job
    print(f"\n Job {job_id} | Type: {input_type} | Subject: {subject}")
    
    try:
      if input_type =="url":
        process_url_job(input_source, subject)
      elif input_type == "pdf":
        process_pdf_job(f"uploads/{input_source}", subject)
      elif input_type == "text_urls":
        process_text_file_with_urls(f"uploads/{input_source}", subject)
      elif input_type == "text":
        process_raw_text_job(input_source, subject)
      else:
        raise ValueError(f"Unsupported input_type: {input_type}")

      cursor.execute("UPDATE training_jobs SET status = 'completed' WHERE job_id = %s", (job_id,))
      conn.commit()
      print(f"Job {job_id} marked as completed.")

    except Exception as e:
      print(f" Failed to process job {job_id}: {e}")

  cursor.close()
  conn.close()
  print("\n All jobs processed!\n")

