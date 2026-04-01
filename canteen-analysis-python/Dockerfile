FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DEFAULT_TIMEOUT=120

COPY requirements.txt ./
RUN set -eux; \
		ok=0; \
		for i in 1 2 3; do \
			pip install --no-cache-dir \
				--timeout 120 \
				--retries 10 \
				-i https://pypi.tuna.tsinghua.edu.cn/simple \
				--extra-index-url https://mirrors.aliyun.com/pypi/simple \
				--extra-index-url https://pypi.org/simple \
				--trusted-host pypi.tuna.tsinghua.edu.cn \
				--trusted-host mirrors.aliyun.com \
				--trusted-host pypi.org \
				-r requirements.txt && ok=1 && break; \
			echo "pip install failed, retrying... ($i/3)"; \
			sleep 10; \
		done; \
		if [ "$ok" -ne 1 ]; then \
			echo "pip dependency install failed after retries"; \
			exit 1; \
		fi; \
		python -c "import fastapi"

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
