    FROM python:3.12
    WORKDIR /app
    COPY EntiTrack_API/requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt
    COPY EntiTrack_API .
    EXPOSE 8080
    CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app