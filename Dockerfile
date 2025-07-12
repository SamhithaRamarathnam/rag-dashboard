# Use official Python image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Copy all files into the container
COPY . .

# Install pip dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variable so Python doesn't buffer logs
ENV PYTHONUNBUFFERED=1

# Command to run your script
CMD ["python", "job_processor.py"]
