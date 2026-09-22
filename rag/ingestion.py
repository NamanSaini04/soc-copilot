from dataclasses import dataclass
from pathlib import Path


@dataclass
class Chunk:
    source_id: str
    title: str
    section: str
    text: str
    path: str


def chunk_markdown(path: Path, max_chars: int = 1200, overlap: int = 150) -> list[Chunk]:
    text = path.read_text(encoding="utf-8")
    title = path.stem.replace("_", " ").title()
    chunks: list[Chunk] = []
    section = "Overview"
    buffer = ""
    for line in text.splitlines():
        if line.startswith("#"):
            section = line.lstrip("# ")
        if len(buffer) + len(line) > max_chars and buffer:
            chunks.append(Chunk(f"{path.stem}:{len(chunks)+1}", title, section, buffer.strip(), str(path)))
            buffer = buffer[-overlap:] + "\n" + line
        else:
            buffer += line + "\n"
    if buffer.strip():
        chunks.append(Chunk(f"{path.stem}:{len(chunks)+1}", title, section, buffer.strip(), str(path)))
    return chunks


def ingest_directory(directory: str | Path) -> list[Chunk]:
    return [chunk for path in sorted(Path(directory).glob("*.md")) for chunk in chunk_markdown(path)]

