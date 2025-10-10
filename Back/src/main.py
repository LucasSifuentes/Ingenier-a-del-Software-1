from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.database.db import init_db
from src.api import api_router

# Llama a la función que crea la base de datos y las tablas al inicio
init_db()

app = FastAPI()

# Configuración de CORS
origins = ["*"] 
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
