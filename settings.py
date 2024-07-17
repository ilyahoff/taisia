from pydantic import BaseSettings


class Settings(BaseSettings):
    ffmpeg_path: str
    music_files_folder: str
    simp_files_folder: str
    face_file_folder: str
    access_token: str
    mongodb_dsn: str
    token: str

    class Config:
        env_prefix = 'taisia_' 
        env_file = '.env'