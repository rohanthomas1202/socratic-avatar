.PHONY: install dev test bench clean

install:
	cd server && pip install -e ".[dev]"
	cd client && npm install

dev:
	@echo "Starting server and client..."
	@trap 'kill 0' INT; \
	(cd server && uvicorn main:app --reload --port 8050) & \
	(cd client && npm run dev) & \
	wait

test:
	cd server && python -m pytest ../tests/ -v

bench:
	cd server && python ../benchmarks/run_benchmark.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf client/.next
	rm -rf server/*.egg-info
