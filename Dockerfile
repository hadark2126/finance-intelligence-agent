FROM python:3.13-slim

WORKDIR /app

# Install CPU-only torch first (saves ~500MB vs default GPU build)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bake FinBERT into the image so the container starts instantly
RUN python -c "from transformers import pipeline; pipeline('text-classification', model='ProsusAI/finbert')"

# Copy application code (.env excluded via .dockerignore)
COPY . .

EXPOSE 8000

CMD ["uvicorn", "backend_main:app", "--host", "0.0.0.0", "--port", "8000"]