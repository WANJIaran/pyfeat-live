"""pyfeatlive_core — framework-neutral facial-expression pipeline.

Houses the parts of pyfeat-live that don't depend on a particular UI
framework: detector loading, the streaming recorder, on-disk session
schema, identity tracking, annotations, pipeline presets, and research-only
facial behavior indices.

Imported by ``backend`` (FastAPI) for v2, and reusable from notebooks
or other Python entry points.
"""

__version__ = "2.0.0-dev"

from pyfeatlive_core import indices

__all__ = ["indices"]
