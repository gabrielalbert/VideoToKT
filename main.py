from fastapi import FastAPI, File, UploadFile,Request,APIRouter
import uvicorn
from controller import *
from Library.postgressql import *
from contextlib import asynccontextmanager
from controller import router 
import logging
# logging.basicConfig(level=logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_postgres()
        yield
    finally:
        await close_postgres()  # Ensure proper cleanup       
app:FastAPI=FastAPI(lifespan=lifespan,title="Video to ppt FastAPI PostgreSQL")

app.include_router(router)

if __name__ == "__main__" :
    uvicorn.run('main:app',host="0.0.0.0",port=8001,reload=True)