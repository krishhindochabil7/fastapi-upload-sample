from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List
import os
from loading import loading_graph

app = FastAPI()

# Create the "Temporary" folder if it doesn't exist
TEMP_DIR = "Temporary"
os.makedirs(TEMP_DIR, exist_ok=True)

# Setup templates directory
templates = Jinja2Templates(directory="templates")

# Home page
@app.get("/", response_class=HTMLResponse)
async def home_page():
    return templates.TemplateResponse("home.html", {"request": {}})

# Upload page
@app.get("/upload", response_class=HTMLResponse)
async def upload_page():
    return templates.TemplateResponse("upload.html", {"request": {}})

# File upload handler
@app.post("/upload_file")
async def upload_file(files: List[UploadFile] = File(...)):
    results = []

    for file in files:
        try:
            # Save the uploaded file to the "Temporary" folder
            file_location = os.path.join(TEMP_DIR)
            with open(file_location, "wb") as f:
                f.write(await file.read())

            # Pass the file path to the loading_graph function
            answer = loading_graph(file_location)
            results.append(f"{file.filename}: {answer}")

        except Exception as e:
            results.append(f"{file.filename}: Error - {e}")

    return templates.TemplateResponse("result.html", {"request": {}, "results": results})