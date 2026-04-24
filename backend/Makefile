.PHONY: help build test cov lint quality loop clean

help:
	@echo "=== Python Dev Loop ==="
	@echo "  build      - Lint + check syntax"
	@echo "  test       - Run tests (no coverage)"
	@echo "  cov        - Run tests with coverage"
	@echo "  lint       - Run ruff check + black --check"
	@echo "  quality    - Full quality gate pipeline"
	@echo "  loop       - AI-assisted coverage improvement"
	@echo "  clean      - Remove generated artifacts"

build:
	python -m compileall app/ || true

test:
	pytest tests/ -v --no-cov --tb=short -q

cov:
	pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html:htmlcov --cov-report=json:coverage.json --tb=short

lint:
	ruff check app/ && black --check app/

quality: lint test cov
	@python3 -c "\
import json; \
j = json.load(open('coverage.json')); \
pct = j['totals']['lines']['pct_covered']; \
if pct < 70: raise SystemExit(f'Coverage {pct:.1f}% < 70% threshold'); \
print(f'Coverage: {pct:.1f}% [PASS]') \
"

loop:
	@echo "=== Loop Mode ==="
	@echo "Run 'make cov' first, then ask AI to analyze coverage gaps and generate test skeletons."

clean:
	rm -rf htmlcov/ coverage.json .coverage __pycache__/
	find app/ -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
