runserver:
	make db
	python3 manage.py runserver

db:
	python3 manage.py makemigrations
	python3 manage.py migrate
