## Summary

- 

## Work Unit

- Related work-unit doc: 
- Scope kept intentionally small: yes/no

## Verification

- [ ] `git diff --check`
- [ ] Backend tests: `docker run --rm -v "${PWD}\backend:/workspace" -w /workspace maven:3.9-eclipse-temurin-21 mvn test`
- [ ] Worker tests: `docker run --rm -v "${PWD}\worker:/workspace" -w /workspace python:3.10-slim sh -lc "pip install -e .[test] >/tmp/pip.log && pytest"`
- [ ] Docker smoke test, if runtime changed: `docker compose up --build -d`

## Risk

- Data/schema risk:
- Crawler policy risk:
- Follow-up tasks:

