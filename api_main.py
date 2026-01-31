from fastapi import FastAPI, Response
import csv
import json

app = FastAPI()

# --- MODELE DANYCH ---


class Movie:
    def __init__(self, movie_id, title, genres):
        self.id = movie_id
        self.title = title
        self.genres = genres


class Link:
    def __init__(self, movie_id, imdb_id, tmdb_id):
        self.id = movie_id
        self.imdbId = imdb_id
        self.tmdbId = tmdb_id


class Rating:
    def __init__(self, user_id, movie_id, rating, timestamp):
        self.userId = user_id
        self.movieId = movie_id
        self.rating = rating
        self.timestamp = timestamp


class Tag:
    def __init__(self, user_id, movie_id, tag, timestamp):
        self.userId = user_id
        self.movieId = movie_id
        self.tag = tag
        self.timestamp = timestamp


# --- ENDPOINTY ---


@app.get("/")
def read_root():
    data = {"hello": "world"}
    return Response(content=json.dumps(data, indent=4), media_type="application/json")


@app.get("/movies")
def get_movies():
    movies_list = []
    try:
        # Pobieranie danych z pliku
        with open("data/movies.csv", mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                movie_obj = Movie(row["movieId"], row["title"], row["genres"])
                movies_list.append(movie_obj.__dict__)

        formatted_json = json.dumps(movies_list, indent=4)
        return Response(content=formatted_json, media_type="application/json")

    except FileNotFoundError:
        return {"error": "Nie znaleziono pliku data/movies.csv"}


@app.get("/links")
def get_links():
    links_list = []
    try:
        with open("data/links.csv", mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                link_obj = Link(row["movieId"], row["imdbId"], row["tmdbId"])
                links_list.append(link_obj.__dict__)

        return Response(
            content=json.dumps(links_list, indent=4), media_type="application/json"
        )
    except FileNotFoundError:
        return {"error": "Nie znaleziono pliku data/links.csv"}


@app.get("/ratings")
def get_ratings():
    ratings_list = []
    try:
        with open("data/ratings.csv", mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                rating_obj = Rating(
                    row["userId"], row["movieId"], row["rating"], row["timestamp"]
                )
                ratings_list.append(rating_obj.__dict__)

        return Response(
            content=json.dumps(ratings_list, indent=4), media_type="application/json"
        )
    except FileNotFoundError:
        return {"error": "Nie znaleziono pliku data/ratings.csv"}


@app.get("/tags")
def get_tags():
    tags_list = []
    try:
        with open("data/tags.csv", mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                tag_obj = Tag(
                    row["userId"], row["movieId"], row["tag"], row["timestamp"]
                )
                tags_list.append(tag_obj.__dict__)

        return Response(
            content=json.dumps(tags_list, indent=4), media_type="application/json"
        )
    except FileNotFoundError:
        return {"error": "Nie znaleziono pliku data/tags.csv"}
