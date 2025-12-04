# Dockerfile for PDF Viewer app
# Uses a slim Python base image and installs system deps commonly needed by imaging libraries

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV FLASK_APP=app.py

# Install system packages required for building wheels and image processing
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libjpeg-dev \
       zlib1g-dev \
       libfreetype6-dev \
       liblcms2-dev \
       libopenjp2-7 \
       poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt /app/requirements.txt

# Install Python dependencies and gunicorn
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt gunicorn

# Copy the rest of the application
COPY . /app

# Create thumbnails dir and ensure permissions
RUN mkdir -p /app/pdfs/thumbnails \
    && useradd -m appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

# Attempt to run via gunicorn, fallback to flask development server if gunicorn can't import the app
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:5000 app:app --workers 2 --threads 4 || flask run --host=0.0.0.0"]
