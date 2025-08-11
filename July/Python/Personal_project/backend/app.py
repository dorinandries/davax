from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers import router
from database import init_db, loadDefaultUser

app = FastAPI(
    title="Proiect AI + Threejs",
    version="1.0.0",
    description="OpenAI API + ThreeJS & React"
)

# Activează CORS pentru frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
init_db()
loadDefaultUser()
