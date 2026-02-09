1. Add a fallback import for `chromadb.Client` in `[edge-agent/app/retrieval/ask.py](edge-agent/app/retrieval/ask.py)` so `Client` is defined even if the dependency is missing.
2. Adjust `_build_client` to raise a clear `RuntimeError` when called without a real client, ensuring tests/imports still work but failures remain obvious.
