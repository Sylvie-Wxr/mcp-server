from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class AddRequest(BaseModel):
    a: int
    b: int

class ReverseRequest(BaseModel):
    text: str

@app.get("/mcp/manifest")
def get_manifest():
    return {
        "name": "Local MCP Server",
        "description": "Demo endpoints for addition and string reversal",
        "endpoints": ["/add", "/reverse"]
    }

@app.post("/add")
def add_numbers(req: AddRequest):
    return {"result": req.a + req.b}

@app.post("/reverse")
def reverse_text(req: ReverseRequest):
    return {"result": req.text[::-1]}
