FROM python:3.11-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

ARG PIP_INDEX_URL=https://pypi.org/simple
ARG PIP_EXTRA_INDEX_URL=
ARG PIP_TIMEOUT=120
ARG PIP_RETRIES=10

COPY canteen-analysis-python/requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip && \
		python -m pip install \
			--no-cache-dir \
			--timeout ${PIP_TIMEOUT} \
			--retries ${PIP_RETRIES} \
			--index-url ${PIP_INDEX_URL} \
			${PIP_EXTRA_INDEX_URL:+--extra-index-url ${PIP_EXTRA_INDEX_URL}} \
			-r /app/requirements.txt \
		|| python -m pip install \
			--no-cache-dir \
			--timeout ${PIP_TIMEOUT} \
			--retries ${PIP_RETRIES} \
			--index-url https://pypi.tuna.tsinghua.edu.cn/simple \
			-r /app/requirements.txt

COPY canteen-analysis-python /app

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]