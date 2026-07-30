from .base import BaseSource, PlatformUnavailable
from .tiktok_source import TikTokSource
from .x_source import XSource
from .youtube_source import YouTubeSource

# 平台注册表：新增平台只需在此登记
SOURCES = {
    "x": XSource,
    "tiktok": TikTokSource,
    "youtube": YouTubeSource,
}
