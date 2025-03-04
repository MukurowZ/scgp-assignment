# SCGP Assignment

## Please read before proceed

1. This is just an assignment for SCGP, **do not run it on any production environment.**
2. **Before proceeding with anything**, please copy **`.env.example`** and rename it to **`.env`**.
3. This project is already bundled with a **Docker Compose** file, so you can just compose up.
   - It already exposes ports to the local machine.
   - You can access the API via `localhost:8000`.
   - The UI is available at `localhost:5173`.
4. **Before executing anything, don't forget to run the migration.**
5. The **Frontend** is built with **Vue** and uses [Pug](https://pugjs.org/api/getting-started.html) for templates.
6. In case you want to run only **Vue** project with Node runtime, don't forget to create **`.env`** for it. There already **`.env.example`** provided in `frontend` directory.
7. Also if you want to run only **Python Backend**, please don't forget to to create **`.env`** for it. There already **`.env.example`** provided in `backend` directory.


## For who just want to run this application
```
$ docker compose up -d
```

## Rebuild this application
```
$ docker compose up --build --force-recreate
```

## To get your container ID
```
$ docker ps
```

## Execute command on API container
```
$ docker exec -it <YOUR_API_CONTAINER_ID> sh
```
or
```
$ docker exec -it <YOUR_API_CONTAINER_ID> bash
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

## To running only Frontend locally

#### Install dependencies, Recommend to use bun
```
bun i
```

#### Run the project
```
bun run dev
```


## To running only Backend locally

#### Install packages, please make sure you have Python in machine.
```
pip install -r requirements.txt
```

#### Run the project
```
python manage.py runserver
```