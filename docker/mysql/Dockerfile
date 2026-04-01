FROM mysql:8.0

ENV TZ=Asia/Shanghai

# First-time DB init scripts.
COPY models/scripts /docker-entrypoint-initdb.d
