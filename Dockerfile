FROM python:3-onbuild

ENV FLASK_APP app.py

CMD ["flask", "run"]