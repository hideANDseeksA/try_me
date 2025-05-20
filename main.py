



from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, certificates, enrollments,generator
from models import schema
from utils import helpers


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(enrollments.router)
app.include_router(certificates.router)
app.include_router(generator.router)
