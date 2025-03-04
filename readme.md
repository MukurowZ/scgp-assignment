# SCGP Assignment

## For who just want to run this application
```
$ docker compose up -d
```

## Rebuild this application
```
$ docker compose up --build --force-recreate
```

## To migrate please using Django-admin
```
// on ./backend directory

$ python manage.py migrate
// or
$ django-admin migrate
```

## Format of data that import must be in .csv file that consists of 4 columns
```
timestamp, temperature, humidity, air_quality
```