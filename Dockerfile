FROM python:3.12.14-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python -m unittest discover -s tests -v
CMD ["python", "src/benchmark.py", "--config", "configs/sample.json"]
