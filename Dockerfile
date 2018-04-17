FROM python:3-onbuild

ENV FLASK_APP run.py

CMD ["flask", "run"]