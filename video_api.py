from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import uuid
import os
import requests
import cloudinary
import cloudinary.uploader

app = FastAPI()

cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True
)

class VideoRequest(BaseModel):
    video_url: str

@app.get("/")
def home():
    return {"status": "FFmpeg API is running"}

@app.post("/process")
def process_video(data: VideoRequest):
    filename = f"{uuid.uuid4()}.mp4"

    try:
        r = requests.get(data.video_url, timeout=120)
        r.raise_for_status()
       
        with open("input_video", "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
      
        subprocess.run([
            "ffmpeg", "-y", "-i", "input_video",
            "-t", "35",
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            "-c:v", "libx264", "-c:a", "aac",
            filename
        ], check=True, timeout=300)

        result = cloudinary.uploader.upload(
            filename,
            resource_type="video"
        )

        return {
            "status": "success",
            "video_url": result["secure_url"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        for f in [filename, "input_video"]:
            if os.path.exists(f):
                os.remove(f)
