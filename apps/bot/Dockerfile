FROM python:3.9-slim

WORKDIR /app

# ✅ КРИТИЧНО: добавить PYTHONPATH для импорта пакетов
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ✅ Для API используйте uvicorn (не python main.py)
CMD ["python", "main.py"]