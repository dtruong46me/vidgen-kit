"""Asset-metadata resolution — the only place a bare Asset(path=...) is
ever inspected on disk."""

from vidgen.strategies.asset.loader import AssetLoader

__all__ = ["AssetLoader"]
