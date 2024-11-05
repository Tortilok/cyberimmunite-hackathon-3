MODULES := payment_system \
			cars \
			mobile_client \
			management_system 

dev_install:
	sudo apt install python3-venv
	python3 -m venv .venv
	.venv/bin/python3 -m pip install -U pip
	.venv/bin/pip install -r requirements.txt

all:
	docker compose up -d

logs:
	docker compose logs -f --tail 100
	
test:
	docker compose up -d
	sleep 15
	python3 -m pytest tests/e2e-test/test_base_scheme.py
	docker compose down

clean:
	docker compose down 
	for MODULE in ${MODULES}; do \
		docker rmi $${MODULE};  \
	done