FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY . .

CMD ["python", "-c", "import os, uvicorn; uvicorn.run('backend.main:app', host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))"]
