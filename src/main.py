from fastapi import FastAPI

from views.api import api_router

app = FastAPI(debug=True)

app.include_router(api_router)
