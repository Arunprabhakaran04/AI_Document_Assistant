from fastapi import FastAPI
from backend.app.routers import users, chat, pdf

app = FastAPI()

app.include_router(users.router)
app.include_router(chat.router)
app.include_router(pdf.router)
