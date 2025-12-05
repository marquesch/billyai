from fastapi import FastAPI

from views import api

app = FastAPI(debug=True)

app.include_router(api_router)
