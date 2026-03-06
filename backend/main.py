from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, organizations, api_keys, conversations, files, qdrant

app = FastAPI()

# CORS Configuration
origins = [
    "http://localhost:5173",  # Vite default port
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(organizations.router)
app.include_router(api_keys.router)
app.include_router(conversations.router)
app.include_router(files.router)
app.include_router(qdrant.router)

@app.get("/")
def read_root():
    return {"message": "Nexus API is running"}
