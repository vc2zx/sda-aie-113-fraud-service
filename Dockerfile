FROM python:3.12-slim AS builder

WORKDIR /build

COPY pyproject.toml .

RUN python -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); print('\n'.join(d['project']['dependencies']))" > requirements.txt \
    && python -m pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

COPY src ./src

RUN python -m pip wheel --no-cache-dir --no-deps --wheel-dir /wheels .


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system app \
    && adduser --system --ingroup app app

COPY --from=builder /wheels /wheels

RUN python -m pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels

COPY --chown=app:app models ./models

USER app

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/v1/ready', timeout=2)"

CMD ["uvicorn", "fraud_service.api.app:app", "--host", "0.0.0.0", "--port", "8000"]