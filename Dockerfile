FROM python:3.12-slim

# Set the working directory inside the container.
WORKDIR /usr/src/app

# Set environment variables for production.
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 📦 Install system dependencies, Python packages, and clean up
COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc curl && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y --auto-remove gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy the entire Django project into the container.
COPY . .

# Run `collectstatic` to gather all static files into a single directory.
RUN python manage.py collectstatic --noinput

# The final command: run Gunicorn to serve the application.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "ProjectStore.wsgi:application"]

