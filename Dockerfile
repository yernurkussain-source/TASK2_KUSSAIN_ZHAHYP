FROM python:3.12.14-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 MPLBACKEND=Agg
COPY requirements.txt requirements-lock.txt ./
RUN pip install --no-cache-dir -r requirements-lock.txt
COPY . .
RUN python -m unittest discover -s tests -v
# Default: analysis + figures from the committed processed data and benchmark log.
# Re-collect timings in an isolated container with, for example:
#   docker run --rm --cpus=2 --memory=2g -v "$PWD/data:/app/data" task3 python src/collector.py
CMD ["python", "src/run_pipeline.py", "--config", "configs/research.yaml"]
