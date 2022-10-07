import typing as t
from pathlib import Path


def file_iterator(path: Path, chunk: int = 4096) -> t.Iterator[bytes]:
    with path.open('rb') as reader:
        while True:
            data = reader.read(chunk)
            if not data:
                break
            yield data
