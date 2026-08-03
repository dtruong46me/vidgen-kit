"""AssetLoader — resolves an Asset's real duration/resolution/fps from
disk (Layer 2).

This is the first and only point a media file referenced by a bare
``Asset(path=...)`` (as created by ``TimelineBuilder``) actually gets
inspected. Called by ``RenderStrategy`` at render time, never by
``TimelineBuilder`` itself — see docs/ARCHITECTURE.md for why that split
matters (it keeps Layer 1 free of any MoviePy/Pillow dependency).
"""

from dataclasses import replace

from moviepy import AudioFileClip, VideoFileClip
from PIL import Image

from vidgen.domain.asset import Asset
from vidgen.strategies.errors import AssetResolutionError


class AssetLoader:
    """Reads real file metadata for an ``Asset`` created with only a path."""

    def resolve(self, asset: Asset) -> Asset:
        """Return an ``Asset`` with ``duration``/``resolution``/``fps`` filled in.

        Idempotent: if ``asset.duration`` is already set, ``asset`` is
        returned unchanged. Otherwise a **new** ``Asset`` is returned —
        the input is never mutated in place, so a ``Timeline``'s
        original ``Asset`` objects stay exactly what the builder
        created.

        Raises:
            AssetResolutionError: the underlying file could not be read.
        """
        if asset.duration is not None:
            return asset

        try:
            if asset.type == "video":
                return self._resolve_video(asset)
            if asset.type == "image":
                return self._resolve_image(asset)
            return self._resolve_audio(asset)
        except (FileNotFoundError, OSError) as exc:
            raise AssetResolutionError(
                f"could not resolve metadata for asset at {asset.path!r}: {exc}"
            ) from exc

    def _resolve_video(self, asset: Asset) -> Asset:
        clip = VideoFileClip(asset.path)
        try:
            return replace(
                asset,
                duration=clip.duration,
                resolution=tuple(clip.size),
                fps=clip.fps,
            )
        finally:
            clip.close()

    def _resolve_image(self, asset: Asset) -> Asset:
        with Image.open(asset.path) as image:
            return replace(asset, resolution=image.size, duration=None, fps=None)

    def _resolve_audio(self, asset: Asset) -> Asset:
        clip = AudioFileClip(asset.path)
        try:
            return replace(asset, duration=clip.duration, resolution=None, fps=None)
        finally:
            clip.close()
