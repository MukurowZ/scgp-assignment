# SCGP Assignment

Please read before proceed
1. This is just an assignment for SCGP, please not run it on any production environment.
2. This project already bundle with Docker-compose file, so you can just compose up.
   1. Also, it already expose port to local machine.
   2. You can execute API via host localhost:8000
   3. For the UI at host localhost:
3. Before execute anythings please don't forget to run migration
4. For Frontend directory, it write on Vue, and [Pug](https://pugjs.org/api/getting-started.html) template


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