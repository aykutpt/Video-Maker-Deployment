from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import uuid
import aiofiles
from video_maker import create_video_from_image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Photo → Video (Ken Burns) for Etsy")
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload", response_class=HTMLResponse)
async def upload(request: Request, file: UploadFile = File(...), duration: float = Form(12.0)):
    """Upload an image and create a video.

    duration: desired video duration in seconds (default 12.0). Recommend 10-15 for Etsy.
    """
    # validate file type
    if not file.content_type.startswith("image/"):
        return templates.TemplateResponse("index.html", {"request": request, "error": "Lütfen bir resim dosyası yükleyin."})

    filename = f"{uuid.uuid4().hex}_{file.filename}"
    upload_path = os.path.join(UPLOAD_DIR, filename)

    # save upload
    async with aiofiles.open(upload_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    # create output path
    out_name = f"video_{uuid.uuid4().hex}.mp4"
    out_path = os.path.join(OUTPUT_DIR, out_name)

    try:
        # call sync function in thread pool (moviepy is CPU-bound)
        from concurrent.futures import ThreadPoolExecutor
        import asyncio

        loop = asyncio.get_event_loop()
        def run():
            create_video_from_image(upload_path, out_path, duration=duration)
        await loop.run_in_executor(None, run)

        download_url = f"/outputs/{out_name}"
        return templates.TemplateResponse("index.html", {"request": request, "video_url": download_url, "success": "Video oluşturuldu!"})
    except Exception as e:
        return templates.TemplateResponse("index.html", {"request": request, "error": f"Video oluşturulurken hata: {e}"})


@app.get("/download/{fname}")
async def download(fname: str):
    path = os.path.join(OUTPUT_DIR, fname)
    if os.path.exists(path):
        return FileResponse(path, filename=fname, media_type='video/mp4')
    return {"error": "Dosya bulunamadı"}
