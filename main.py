from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
from sqlalchemy.orm import sessionmaker
from models import Base, Person
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI()

# Montar el directorio de archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Obtener las credenciales de la base de datos desde las variables de entorno
DATABASE_HOST = os.getenv("Host")
DATABASE_NAME = os.getenv("Database")
DATABASE_USER = os.getenv("User")
DATABASE_PORT = os.getenv("Port")
DATABASE_PASSWORD = os.getenv("Password")

# Construir la URL de conexión a la base de datos
DATABASE_URL = f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

# Crear la instancia del motor de la base de datos
engine = create_engine(DATABASE_URL)

# Crear una sesión de base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Configurar las plantillas HTML
templates = Jinja2Templates(directory="templates")


# Define las rutas para mostrar el formulario HTML y procesar el formulario para crear una nueva persona
@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})


@app.post("/create_person", response_class=HTMLResponse)
async def create_person(request: Request):
    form_data = await request.form()
    nombre = form_data.get("name")
    telefono = form_data.get("tel")
    edad = form_data.get("age")

    db = SessionLocal()
    try:
        person = Person(nombre=nombre, edad=edad, telefono=telefono)
        db.add(person)
        db.commit()
        db.refresh(person)
        return templates.TemplateResponse("form.html", {"request": request, "message": "Persona registrada correctamente"})
    finally:
        db.close()


# Define la ruta para mostrar todas las personas
@app.get("/people", response_class=HTMLResponse)
async def read_people(request: Request):
    db = SessionLocal()
    people = db.query(Person).all()
    db.close()

    return templates.TemplateResponse("people.html", {"request": request, "people": people})


# Ruta para obtener los detalles de una persona por su ID
@app.get("/people/{person_id}/details", response_class=JSONResponse)
async def get_person_details(person_id: int):
    db = SessionLocal()
    person = db.query(Person).filter(Person.id == person_id).first()
    db.close()

    if person:
        return {"id": person.id, "nombre": person.nombre, "edad": person.edad, "telefono": person.telefono}
    else:
        raise HTTPException(status_code=404, detail="Person not found")


# Modelo de formulario para actualizar una persona
class PersonUpdate(BaseModel):
    nombre: str
    edad: int
    telefono: str


@app.post("/people/{person_id}/edit/")
async def update_person(person_id: int, person: PersonUpdate):
    db = SessionLocal()
    db_person = db.query(Person).filter(Person.id == person_id).first()
    if db_person:
        db_person.nombre = person.nombre
        db_person.edad = person.edad
        db_person.telefono = person.telefono
        db.commit()
        db.close()
        return {"message": "Person updated successfully"}
    raise HTTPException(status_code=404, detail="Person not found")


@app.post("/people/{person_id}/delete/")
async def delete_person(person_id: int):
    db = SessionLocal()
    db_person = db.query(Person).filter(Person.id == person_id).first()
    if db_person:
        db.delete(db_person)
        db.commit()
        db.close()
        return {"message": "Person deleted successfully"}
    raise HTTPException(status_code=404, detail="Person not found")
