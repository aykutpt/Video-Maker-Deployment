# Copilot Instructions: Photo to Video Generator

## Project Overview
A FastAPI-based web service that converts static images into Ken Burns-style MP4 videos optimized for Etsy product previews. The application provides a simple web UI for uploading images and downloads the generated video.

**Key Technologies:** FastAPI, moviepy (video processing), ffmpeg (encoding), Jinja2 templates

## Architecture

### Component Structure
- **main.py**: FastAPI web server handling uploads and file management
  - `/` (GET): Serves HTML form
  - `/upload` (POST): Accepts image + duration, triggers video generation in thread pool
  - `/download/{fname}` (GET): Downloads MP4 files
- **video_maker.py**: Core video generation logic (Ken Burns animation with pan/zoom)
- **templates/index.html**: Turkish UI with form for image upload and duration control
- **outputs/**: Static directory serving generated MP4 files
- **uploads/**: Temporary storage for uploaded images

### Data Flow
User uploads image → saved to `uploads/` → `create_video_from_image()` processes in async thread pool → MP4 written to `outputs/` → served via `/outputs/` static mount

## Critical Developer Workflows

### Setup & Dependencies
Requires `ffmpeg` on system PATH (not a Python package). Install via:
- Windows: `choco install ffmpeg` or download binary
- Linux: `apt install ffmpeg`
- macOS: `brew install ffmpeg`

Python dependencies: `fastapi uvicorn moviepy aiofiles python-multipart`

### Running the Application
```bash
uvicorn main:app --reload  # Development with hot-reload
uvicorn main:app --host 0.0.0.0 --port 8000  # Production
```
Access at `http://localhost:8000`

### Video Generation Process
`create_video_from_image()` produces Ken Burns effect:
1. Scales image to fill 1920×1080 (configurable) with 15% extra zoom room
2. Animates smooth pan using sinusoidal easing (top-left → bottom-right)
3. Adds 0.6s fade-in/fade-out for polish
4. Encodes with libx264 at 8000k bitrate, 30fps (4 threads)
5. Returns output path

**Performance Note**: moviepy is CPU-bound; async executor prevents blocking UI during encoding.

## Project-Specific Patterns

### Async/Sync Boundary Management
VideoMaking is CPU-heavy and synchronous (moviepy limitation). Pattern in `main.py`:
```python
loop = asyncio.get_event_loop()
await loop.run_in_executor(None, run)  # Runs sync function in thread pool
```
This keeps FastAPI responsive while long video encoding happens.

### File Organization
- Use `uuid.uuid4().hex` for unique filenames (prevents collisions)
- Input files: `{uuid}_{original_filename}` → outputs immediately deleted after processing
- Output files: `video_{uuid}.mp4` → served via HTTP

### Video Parameters (in `video_maker.py`)
- **zoom_scale**: 1.15 (15% extra room for Ken Burns pan—adjust for zoom intensity)
- **resolution**: (1920, 1080) hardcoded; change here for different aspect ratios
- **bitrate**: "8000k" (HD quality; higher = larger files, increase for 4K)
- **duration**: User-controlled via form (10-15s recommended for Etsy)

### Turkish Localization
UI is in Turkish (`index.html`, error messages). Update all user-facing strings in:
- `templates/index.html`: Form labels, instructions
- `main.py`: Error messages (e.g., "Lütfen bir resim dosyası yükleyin")

## Integration Points & Dependencies

### External Libraries
- **moviepy**: Video composition, effects (fadein/fadeout)
- **ffmpeg**: Actual encoding (called by moviepy, must be on PATH)
- **FastAPI**: Web framework
- **Jinja2**: HTML templating

### File System Dependencies
- Output directory auto-created at startup (`os.makedirs(OUTPUT_DIR, exist_ok=True)`)
- Static file serving requires `outputs/` folder to exist
- Uploaded files temporary; consider cleanup task for old uploads

## Common Modifications

When extending this codebase, consider:
- **Add audio**: Pass `audio=AudioFileClip(path)` to `create_video_from_image()`; update form to accept audio upload
- **Support multiple images/slides**: Modify `video_maker.py` to concatenate multiple clips
- **Queue long jobs**: Replace thread pool with Celery/RQ for scalability
- **Persist metadata**: Track generated videos in a database instead of relying on filesystem
