from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}

@app.get("/hello")
def read_root():
    return {"message": "Hello world!"}

@app.get("/isalive")
def read_root():
    return {"message": "Alive"}

@app.get("/isready")
def read_root():
    return {"message": "Ready"}
