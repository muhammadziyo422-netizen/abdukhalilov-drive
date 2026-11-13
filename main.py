import os
import shutil
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()

# Maxfiy parolingiz:
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "uzb778899")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

class NoteItem(BaseModel):
    title: str
    content: str

class LoginItem(BaseModel):
    password: str

def verify_token(x_token: str = Header(None)):
    if x_token != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Parol noto'g'ri!")

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

@app.post("/api/login")
async def login(item: LoginItem):
    if item.password == ADMIN_PASSWORD:
        return {"status": "ok", "token": ADMIN_PASSWORD}
    raise HTTPException(status_code=401, detail="Parol xato!")

@app.get("/api/files", dependencies=[Depends(verify_token)])
async def list_files():
    files_list = []
    for filename in os.listdir(UPLOAD_DIR):
        filepath = os.path.join(UPLOAD_DIR, filename)
        if os.path.isfile(filepath):
            stats = os.stat(filepath)
            files_list.append({
                "name": filename,
                "size": round(stats.st_size / 1024, 1),
                "date": datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M"),
                "ext": os.path.splitext(filename)[1].lower()
            })
    return sorted(files_list, key=lambda x: x["date"], reverse=True)

@app.post("/api/upload", dependencies=[Depends(verify_token)])
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"message": "Yuklandi", "filename": file.filename}

@app.post("/api/note", dependencies=[Depends(verify_token)])
async def create_note(note: NoteItem):
    safe_title = "".join(c for c in note.title if c.isalnum() or c in (' ', '_', '-')).strip()
    if not safe_title:
        safe_title = f"qayd_{int(datetime.now().timestamp())}"
    filename = f"{safe_title}.txt"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(note.content)
    return {"message": "Saqlandi", "filename": filename}

@app.get("/api/read/{filename}", dependencies=[Depends(verify_token)])
async def read_text_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Topilmadi")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return {"content": f.read()}
    except:
        return {"content": "Bu faylni matn ko'rinishida ochib bo'lmaydi."}

# Faylni yuklab olmasdan brauzerda ko'rish (Video, Rasm, Audio, PDF)
@app.get("/api/view/{filename}")
async def view_file(filename: str, token: str = ""):
    if token != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Ruxsat yo'q")
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Topilmadi")
    return FileResponse(file_path)

# Faylni yuklab olish
@app.get("/api/download/{filename}")
async def download_file(filename: str, token: str = ""):
    if token != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Ruxsat yo'q")
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Topilmadi")
    return FileResponse(file_path, filename=filename)

@app.delete("/api/delete/{filename}", dependencies=[Depends(verify_token)])
async def delete_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return {"message": "O'chirildi"}
    raise HTTPException(status_code=404, detail="Topilmadi")