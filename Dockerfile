FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 ARENA_DATABASE=/data/arena.sqlite3
COPY requirements.lock pyproject.toml README.md LICENSE ./
RUN pip install --no-cache-dir -r requirements.lock
COPY jaeger_arena ./jaeger_arena
RUN pip install --no-cache-dir --no-deps . && useradd --uid 10001 --create-home arena && mkdir /data && chown arena:arena /data
USER arena
VOLUME ["/data"]
EXPOSE 8792
CMD ["python", "-m", "jaeger_arena", "serve", "--host", "0.0.0.0", "--port", "8792"]
