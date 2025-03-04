FROM python:3.13.2-alpine3.21

WORKDIR /app
COPY requirements.txt /app/

RUN apk add --no-cache postgresql-libs postgresql-dev
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
