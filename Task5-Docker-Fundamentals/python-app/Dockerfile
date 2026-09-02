FROM python:3.12-slim

WORKDIR /app

# PYTHONUNBUFFERED=1 makes print()/logging appear in `docker logs` immediately
# instead of sitting in a buffer. PYTHONDONTWRITEBYTECODE avoids .pyc clutter.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# requirements.txt first, so the pip layer is cached independently of app.py.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./

EXPOSE 5000

CMD ["python", "app.py"]
