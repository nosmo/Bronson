virtualenv_run:
	virtualenv virtualenv_run --python=python3
	virtualenv_run/bin/pip install --upgrade pip setuptools wheel
	virtualenv_run/bin/pip install -r requirements.txt

clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete
	rm -rf .tox .taskproc
	rm -rf dist build
