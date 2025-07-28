from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.services.query_file.file_sql import createDataFrame, cleanColumns, analyzeData, queryDataframe, processFile
import tempfile
import os
import pandas as pd

app = FastAPI()

# Mount static files (eg.: JS, CSS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

UPLOADED_DF = {"df":None, "info":None}

@app.post("/upload", response_class=HTMLResponse)
async def upload_file(request:Request, file:UploadFile = File(...)):
    suffix = os.path.splitext(file.filename)[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        temp_path = tmp.name

    try:
        df, info = processFile(temp_path)
        UPLOADED_DF['df'], UPLOADED_DF['info'] = df, info
        msg = f"File uploaded and processed. Rows: {len(df)} | Info: {info}"
    except Exception as e:
        msg = f"Error: {e}"
    finally:
        os.remove(temp_path)
    return msg    


@app.post("/run-query", response_class=HTMLResponse)
async def run_query(request:Request, query:str = Form(...)):
    try:
        result=queryDataframe(df=UPLOADED_DF["df"], sql=query)
        
        if result is None or result.empty:
            return "<p> No results returned for query"
        html_table = result.head(20).to_html(classes="table-auto border-collapse border border-gray-300", index=False)
        return html_table
    except Exception as e:
        return f"<p style='color:red;'>Error running query: {e}</p>"