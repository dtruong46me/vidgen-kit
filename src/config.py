from pathlib import Path

# Thư mục gốc của dự án
BASE_DIR = Path(__file__).resolve().parent.parent

# Cấu hình các đường dẫn Assets
ASSETS_DIR = BASE_DIR / "assets"
CLIPS_DIR = ASSETS_DIR / "clips"
MUSIC_DIR = ASSETS_DIR / "music"
FONTS_DIR = ASSETS_DIR / "fonts"
METADATA_DIR = ASSETS_DIR / "metadata"

# Cấu hình file Metadata
CLIPS_JSON_PATH = METADATA_DIR / "clips.json"

# Cấu hình Input/Output
INPUT_DIR = BASE_DIR / "input"
SCRIPTS_DIR = INPUT_DIR / "scripts"
OUTPUT_DIR = BASE_DIR / "output"
VIDEOS_DIR = OUTPUT_DIR / "videos"
THUMBNAILS_DIR = OUTPUT_DIR / "thumbnails"

# Cấu hình thư mục Tạm
TEMP_DIR = BASE_DIR / "temp"
VOICES_DIR = TEMP_DIR / "voices"
SUBTITLES_DIR = TEMP_DIR / "subtitles"

# Cấu hình Video chung
DEFAULT_FPS = 30
DEFAULT_TRANSITION_DURATION = 0.5  # giây
DEFAULT_FONT_NAME = "msyh.ttc"  # Sử dụng font hỗ trợ tiếng Trung trên Windows
