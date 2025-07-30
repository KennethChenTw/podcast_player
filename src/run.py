#!/usr/bin/env python3
import os
import sys

# 確保 src 目錄在 Python path 中
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from podcast_player.main import PodcastPlayerApp

if __name__ == "__main__":
    app = PodcastPlayerApp()
    app.run()
