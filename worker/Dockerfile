FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy
WORKDIR /workspace
COPY pyproject.toml .
COPY src ./src
COPY data ./data
RUN pip install --no-cache-dir -e .
CMD ["youbuyfirst-worker", "serve"]

