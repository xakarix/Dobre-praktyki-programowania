from fastapi import FastAPI, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta
import csv
import os
import json
from contextlib import asynccontextmanager

# Próba importu modułów lokalnych
try:
    from . import database, schemas, auth
except ImportError:
    import database, schemas, auth


# Pomocnicza funkcja do ładnego formatowania JSON (Pretty Print)
def pretty_json_response(data):
    # Generuje czytelny JSON z wcięciami
    return Response(content=json.dumps(data, indent=4), media_type="application/json")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicjalizacja bazy i ładowanie danych przy starcie [cite: 101]
    database.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    try:
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        csv_configs = [
            (database.Movie, "movies.csv"),
            (database.Link, "links.csv"),
            (database.Rating, "ratings.csv"),
            (database.Tag, "tags.csv"),
        ]

        for model, filename in csv_configs:
            if db.query(model).count() == 0:
                path = os.path.join(data_dir, filename)
                if os.path.exists(path):
                    with open(path, encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            processed = {}
                            for k, v in row.items():
                                if v == "" or v is None:
                                    processed[k] = None
                                elif "Id" in k or k == "timestamp":
                                    processed[k] = int(v)
                                elif k == "rating":
                                    processed[k] = float(v)
                                else:
                                    processed[k] = v
                            db.add(model(**processed))
                    db.commit()

        # Tworzenie admina, jeśli nie istnieje [cite: 243-247, 297]
        if (
            db.query(database.User).filter(database.User.username == "admin").first()
            is None
        ):
            admin_user = database.User(
                username="admin",
                hashed_password=auth.hash_password("admin123"),
                roles=["ROLE_ADMIN", "ROLE_USER"],
            )
            db.add(admin_user)
            db.commit()
    finally:
        db.close()
    yield


app = FastAPI(lifespan=lifespan)


# --- ENDPOINT POWITALNY ---
@app.get("/")
def read_root():
    # Zwraca prosty komunikat powitalny
    return pretty_json_response({"hello": "world"})


# --- UWIERZYTELNIANIE (AUTH) ---
@app.post("/login", response_model=schemas.Token)
def login(data: schemas.LoginData, db: Session = Depends(database.get_db)):
    # Weryfikacja użytkownika i generowanie tokena JWT [cite: 177, 263-278, 295]
    user = (
        db.query(database.User).filter(database.User.username == data.username).first()
    )
    if not user or not auth.verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = auth.create_access_token(
        data={"sub": user.username, "roles": user.roles},
        expires_delta=timedelta(hours=1),
    )
    return {"access_token": token, "token_type": "bearer"}


@app.post("/users", response_model=schemas.UserResponse, status_code=201)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(database.get_db),
    current_user=Depends(auth.require_admin),
):
    # Tworzenie nowego użytkownika - tylko dla ROLE_ADMIN [cite: 298, 302]
    if db.query(database.User).filter(database.User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    new_user = database.User(
        username=user.username, hashed_password=auth.hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.get("/user_details", response_model=schemas.UserDetails)
def get_user_details(current_user: database.User = Depends(auth.get_current_user)):
    # Zwraca dane zalogowanego użytkownika [cite: 303]
    return {"username": current_user.username, "roles": current_user.roles}


# --- MOVIES CRUD ---
@app.get("/movies")
def get_movies(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(database.get_db),
    _=Depends(auth.get_current_user),
):
    # Lista zasobu ze statusem 200 [cite: 146]
    items = db.query(database.Movie).offset(skip).limit(limit).all()
    results = [
        {"id": str(i.movieId), "title": i.title, "genres": i.genres} for i in items
    ]
    return pretty_json_response(results)


@app.get("/movies/{movie_id}")
def get_movie(
    movie_id: int,
    db: Session = Depends(database.get_db),
    _=Depends(auth.get_current_user),
):
    # Pojedynczy element; 404 jeśli nie znaleziono [cite: 158, 166]
    item = db.query(database.Movie).filter(database.Movie.movieId == movie_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Movie not found")
    return pretty_json_response(
        {"id": str(item.movieId), "title": item.title, "genres": item.genres}
    )


@app.post("/movies", status_code=201)
def post_movie(
    movie: schemas.MovieCreate,
    db: Session = Depends(database.get_db),
    _=Depends(auth.get_current_user),
):
    # Dodawanie nowego filmu [cite: 145, 157, 167]
    db_item = database.Movie(**movie.model_dump())
    db.add(db_item)
    db.commit()
    return pretty_json_response(movie.model_dump())


@app.put("/movies/{movie_id}")
def put_movie(
    movie_id: int,
    movie: schemas.MovieBase,
    db: Session = Depends(database.get_db),
    _=Depends(auth.get_current_user),
):
    # Aktualizacja danych [cite: 147, 159, 168]
    db_item = (
        db.query(database.Movie).filter(database.Movie.movieId == movie_id).first()
    )
    if not db_item:
        raise HTTPException(status_code=404)
    for k, v in movie.model_dump().items():
        setattr(db_item, k, v)
    db.commit()
    return pretty_json_response(movie.model_dump())


@app.delete("/movies/{movie_id}", status_code=204)
def delete_movie(
    movie_id: int,
    db: Session = Depends(database.get_db),
    _=Depends(auth.get_current_user),
):
    # Usuwanie elementu [cite: 148, 160]
    db_item = (
        db.query(database.Movie).filter(database.Movie.movieId == movie_id).first()
    )
    if not db_item:
        raise HTTPException(status_code=404)
    db.delete(db_item)
    db.commit()
    return Response(status_code=204)


# --- LINKS CRUD ---
@app.get("/links")
def get_links(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(database.get_db),
    _=Depends(auth.get_current_user),
):
    items = db.query(database.Link).offset(skip).limit(limit).all()
    results = [
        {"id": str(i.movieId), "imdbId": i.imdbId, "tmdbId": i.tmdbId} for i in items
    ]
    return pretty_json_response(results)


@app.get("/links/{movie_id}")
def get_link(
    movie_id: int,
    db: Session = Depends(database.get_db),
    _=Depends(auth.get_current_user),
):
    item = db.query(database.Link).filter(database.Link.movieId == movie_id).first()
    if not item:
        raise HTTPException(status_code=404)
    return pretty_json_response(
        {"id": str(item.movieId), "imdbId": item.imdbId, "tmdbId": item.tmdbId}
    )


@app.post("/links", status_code=201)
def post_link(
    link: schemas.LinkCreate,
    db: Session = Depends(database.get_db),
    _=Depends(auth.get_current_user),
):
    db_item = database.Link(**link.model_dump())
    db.add(db_item)
    db.commit()
    return pretty_json_response(link.model_dump())


@app.put("/links/{movie_id}")
def put_link(
    movie_id: int,
    link: schemas.LinkBase,
    db: Session = Depends(database.get_db),
    _=Depends(auth.get_current_user),
):
    db_item = db.query(database.Link).filter(database.Link.movieId == movie_id).first()
    if not db_item:
        raise HTTPException(status_code=404)
    for k, v in link.model_dump().items():
        setattr(db_item, k, v)
    db.commit()
    return pretty_json_response(link.model_dump())


@app.delete("/links/{movie_id}", status_code=204)
def delete_link(
    movie_id: int,
    db: Session = Depends(database.get_db),
    _=Depends(auth.get_current_user),
):
    db_item = db.query(database.Link).filter(database.Link.movieId == movie_id).first()
    if not db_item:
        raise HTTPException(status_code=404)
    db.delete(db_item)
    db.commit()
    return Response(status_code=204)


# --- RATINGS CRUD ---
@app.get("/ratings")
def get_ratings(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(database.get_db),
    _=Depends(auth.get_current_user),
):
    items = db.query(database.Rating).offset(skip).limit(limit).all()
    results = [
        {
            "id": i.id,
            "userId": i.userId,
            "movieId": i.movieId,
            "rating": i.rating,
            "timestamp": i.timestamp,
        }
        for i in items
    ]
    return pretty_json_response(results)


@app.get("/ratings/{id}")
def get_rating(
    id: int, db: Session = Depends(database.get_db), _=Depends(auth.get_current_user)
):
    item = db.query(database.Rating).filter(database.Rating.id == id).first()
    if not item:
        raise HTTPException(status_code=404)
    return pretty_json_response(
        {
            "id": item.id,
            "userId": item.userId,
            "movieId": item.movieId,
            "rating": item.rating,
            "timestamp": item.timestamp,
        }
    )


@app.post("/ratings", status_code=201)
def post_rating(
    rating: schemas.RatingCreate,
    db: Session = Depends(database.get_db),
    _=Depends(auth.get_current_user),
):
    db_item = database.Rating(**rating.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return pretty_json_response({"id": db_item.id, **rating.model_dump()})


@app.put("/ratings/{id}")
def put_rating(
    id: int,
    rating: schemas.RatingCreate,
    db: Session = Depends(database.get_db),
    _=Depends(auth.get_current_user),
):
    db_item = db.query(database.Rating).filter(database.Rating.id == id).first()
    if not db_item:
        raise HTTPException(status_code=404)
    for k, v in rating.model_dump().items():
        setattr(db_item, k, v)
    db.commit()
    return pretty_json_response(rating.model_dump())


@app.delete("/ratings/{id}", status_code=204)
def delete_rating(
    id: int, db: Session = Depends(database.get_db), _=Depends(auth.get_current_user)
):
    db_item = db.query(database.Rating).filter(database.Rating.id == id).first()
    if not db_item:
        raise HTTPException(status_code=404)
    db.delete(db_item)
    db.commit()
    return Response(status_code=204)


# --- TAGS CRUD ---
@app.get("/tags")
def get_tags(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(database.get_db),
    _=Depends(auth.get_current_user),
):
    items = db.query(database.Tag).offset(skip).limit(limit).all()
    results = [
        {
            "id": i.id,
            "userId": i.userId,
            "movieId": i.movieId,
            "tag": i.tag,
            "timestamp": i.timestamp,
        }
        for i in items
    ]
    return pretty_json_response(results)


@app.get("/tags/{id}")
def get_tag(
    id: int, db: Session = Depends(database.get_db), _=Depends(auth.get_current_user)
):
    item = db.query(database.Tag).filter(database.Tag.id == id).first()
    if not item:
        raise HTTPException(status_code=404)
    return pretty_json_response(
        {
            "id": item.id,
            "userId": item.userId,
            "movieId": item.movieId,
            "tag": item.tag,
            "timestamp": item.timestamp,
        }
    )


@app.post("/tags", status_code=201)
def post_tag(
    tag: schemas.TagCreate,
    db: Session = Depends(database.get_db),
    _=Depends(auth.get_current_user),
):
    db_item = database.Tag(**tag.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return pretty_json_response({"id": db_item.id, **tag.model_dump()})


@app.put("/tags/{id}")
def put_tag(
    id: int,
    tag: schemas.TagCreate,
    db: Session = Depends(database.get_db),
    _=Depends(auth.get_current_user),
):
    db_item = db.query(database.Tag).filter(database.Tag.id == id).first()
    if not db_item:
        raise HTTPException(status_code=404)
    for k, v in tag.model_dump().items():
        setattr(db_item, k, v)
    db.commit()
    return pretty_json_response(tag.model_dump())


@app.delete("/tags/{id}", status_code=204)
def delete_tag(
    id: int, db: Session = Depends(database.get_db), _=Depends(auth.get_current_user)
):
    db_item = db.query(database.Tag).filter(database.Tag.id == id).first()
    if not db_item:
        raise HTTPException(status_code=404)
    db.delete(db_item)
    db.commit()
    return Response(status_code=204)
