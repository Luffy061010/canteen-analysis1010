FROM python:3.11-slim
WORKDIR /app

# Install runtime deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# The FastAPI app is in main.py and exposes `app`
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
