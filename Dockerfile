FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock LICENSE ./
COPY src ./src
RUN uv sync --locked
COPY . .
ENV PATH="/app/.venv/bin:${PATH}"
RUN chmod +x entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
