.PHONY: install scan dashboard api dev test lint docker clean

install:
	pip install -r requirements.txt

scan:
	python scanner.py --tier 1

dashboard:
	python dashboard/app.py

api:
	python api_server.py

dev:
	@echo "dashboard :8000 + api :8001 + scanner"
	@python dashboard/app.py &
	@python api_server.py &
	@python scanner.py --tier 1

test:
	python -m compileall -q .
	python test_filters.py
	python scholar_ollama_test.py

lint:
	python -m compileall -q .
	@echo "lint ok"

docker:
	docker-compose up --build -d
	@echo "Dashboard http://localhost:8000  API http://localhost:8001"

clean:
	rm -rf output/*.xlsx __pycache__ fetchers/__pycache__
