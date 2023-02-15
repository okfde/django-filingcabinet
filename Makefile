messages:
	django-admin makemessages -l de --ignore public --ignore node_modules --ignore htmlcov --add-location file

requirements: requirements-production.in
	pip-compile requirements-production.in
