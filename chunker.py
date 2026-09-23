"""
Stage 2 of the pipeline: splitting documents into chunks.

⚠️ THIS IS THE FILE YOU CHANGE IN MILESTONE 3.

`split_documents` below is deliberately plain. It cuts every document into
fixed-size pieces with a fixed overlap and pays no attention to where sentences
or paragraphs end. It works, and it is not good.

On a corpus of short posts it may not cut anything at all: `campus_life` comes
out as 88 documents and 88 chunks, because almost nothing in it reaches 800
characters. That is the baseline, not a bug — Milestone 3 is where you decide
whether one post should stay one chunk.

Your job in Milestone 3 is to replace the *body* of `split_documents` with a
strategy that fits the documents you actually read in Milestone 1. Keep the
name and the shape of what it returns — the rest of the pipeline calls it, and
your README has to name the function that produced your chunks.

If you get stuck for 30 minutes, `fallback_split` is the original. Switch back
to it, write down what you saw, and move on. That's a real observation about
your pipeline, not giving up.
"""

import re
from dataclasses import dataclass

import config
from ingest import Document

# A section shorter than this is a heading with almost nothing under it, so it
# gets merged forward into the next section rather than becoming its own chunk.
# The smallest real section in city_guides is 174 characters; everything below
# that measured as a bare heading.
MIN_SECTION_CHARS = 120

# Separates the context prefix from the section body.
CONTEXT_SEP = " — "


@dataclass
class Chunk:
    """One piece of one document."""

    text: str
    source: str        # which file it came from
    index: int         # which chunk within that file, starting at 0
    produced_by: str   # the function that made it — cite this in your README

    @property
    def label(self) -> str:
        return f"{self.source}#{self.index}"


def fallback_split(
    documents: list[Document],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """
    The starter's original chunker. Fixed-size character windows with overlap.

    Keep this function. Milestone 3's stop rule points back at it, and having
    something to compare your own strategy against is useful in unit 2.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP

    if overlap >= chunk_size:
        raise ValueError("overlap has to be smaller than chunk_size")

    chunks: list[Chunk] = []
    for doc in documents:
        start = 0
        index = 0
        while start < len(doc.text):
            piece = doc.text[start : start + chunk_size].strip()
            if piece:
                chunks.append(
                    Chunk(
                        text=piece,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::fallback_split",
                    )
                )
                index += 1
            start += chunk_size - overlap

    return chunks


def _parse_sections(text: str) -> tuple[str, list[tuple[str, str]]]:
    """
    Break one markdown document into (title, [(heading, body), ...]).

    The title is the `# ` line. Everything after it is split at `##` headings.
    Text before the first `##` comes back with an empty heading, since the
    opening paragraph of these guides is a real chunk in its own right.
    """
    lines = text.split("\n")
    title = ""
    start = 0
    for i, line in enumerate(lines):
        if line.startswith("# "):
            title = line[2:].strip()
            start = i + 1
            break

    sections: list[tuple[str, str]] = []
    heading = ""
    buffer: list[str] = []
    for line in lines[start:]:
        if re.match(r"^#{2,6}\s+", line):
            sections.append((heading, "\n".join(buffer).strip()))
            heading = line.lstrip("#").strip()
            buffer = []
        else:
            buffer.append(line)
    sections.append((heading, "\n".join(buffer).strip()))

    return title, [(h, b) for h, b in sections if b or h]


def _merge_small(sections: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """
    Fold a section with almost no body into the one after it.

    Without this, a heading like `## Difficult` that sits directly above
    another heading becomes a chunk of pure heading with nothing to retrieve.
    """
    merged: list[tuple[str, str]] = []
    pending: list[tuple[str, str]] = []

    for heading, body in sections:
        if len(body) < MIN_SECTION_CHARS:
            pending.append((heading, body))
            continue
        if pending:
            heads = [h for h, _ in pending if h] + ([heading] if heading else [])
            bodies = [b for _, b in pending if b] + [body]
            merged.append((" / ".join(heads), "\n\n".join(bodies)))
            pending = []
        else:
            merged.append((heading, body))

    if pending:  # trailing stubs with nothing after them to merge into
        heads = [h for h, _ in pending if h]
        bodies = [b for _, b in pending if b]
        if bodies:
            if merged:  # attach to the previous chunk rather than stranding it
                ph, pb = merged[-1]
                merged[-1] = (ph, pb + "\n\n" + "\n\n".join(bodies))
            else:
                merged.append((" / ".join(heads), "\n\n".join(bodies)))

    return merged


def _cap(body: str, limit: int) -> list[str]:
    """
    Keep a section under `limit`, splitting at paragraph breaks and then at
    sentence ends. Never cuts mid-word, which is what the fallback does.
    """
    if len(body) <= limit:
        return [body]

    units = [p.strip() for p in body.split("\n\n") if p.strip()]
    pieces: list[str] = []
    current = ""

    for unit in units:
        if len(unit) > limit:  # one giant paragraph — fall back to sentences
            if current:
                pieces.append(current)
                current = ""
            sentences = re.split(r"(?<=[.!?])\s+", unit)
            for sentence in sentences:
                if current and len(current) + len(sentence) + 1 > limit:
                    pieces.append(current)
                    current = sentence
                else:
                    current = f"{current} {sentence}".strip()
            continue

        if current and len(current) + len(unit) + 2 > limit:
            pieces.append(current)
            current = unit
        else:
            current = f"{current}\n\n{unit}".strip()

    if current:
        pieces.append(current)
    return pieces


def split_documents(documents: list[Document]) -> list[Chunk]:
    """
    Section-aware chunking for the city_guides corpus.

    Why this and not fixed windows. These documents are long guides carved into
    labelled `##` sections — "Getting there", "Eat and drink" — and each section
    is already one coherent thought. Measured across the corpus there are 98 of
    them: median 284 characters, 90th percentile 440, longest 711. Every section
    already fits inside the starter's 800-character window, so the old chunker
    was never splitting because pieces were too big. It was splitting blindly,
    and cutting straight through boundaries that were already there. It left 35
    of 51 chunks starting mid-sentence and 42 of 51 holding parts of two or more
    unrelated sections.

    So the split happens at the headings, and `config.CHUNK_SIZE` stops being a
    window and becomes a ceiling that a well-formed section almost never hits.

    The second move matters more than the first. A section body almost never
    names its own town: six of the seven sections in `guide_kestrelford.md`
    never contain the word "Kestrelford", so the chunk holding the bakery fact
    had nothing in it for the question "when does the Kestrelford bakery sell
    out?" to match. Every chunk is therefore prefixed with its document title
    and heading, which puts the town name and the topic into the embedded text.

    `config.CHUNK_OVERLAP` is not used here. Overlap exists to stop a fixed
    window from severing a thought at an arbitrary point; splitting on real
    boundaries removes the problem instead of padding around it. `fallback_split`
    still honours it.
    """
    limit = config.CHUNK_SIZE
    chunks: list[Chunk] = []

    for doc in documents:
        title, sections = _parse_sections(doc.text)

        if not sections:  # a document with no headings at all
            sections = [("", doc.text)]

        index = 0
        for heading, body in _merge_small(sections):
            for piece in _cap(body, limit):
                prefix = CONTEXT_SEP.join(p for p in (title, heading) if p)
                text = f"{prefix}\n\n{piece}" if prefix else piece
                chunks.append(
                    Chunk(
                        text=text,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::split_documents",
                    )
                )
                index += 1

    return chunks


def describe(chunks: list[Chunk]) -> str:
    """A one-line summary, printed after indexing."""
    if not chunks:
        return "0 chunks"
    lengths = [len(c.text) for c in chunks]
    return (
        f"{len(chunks)} chunks, "
        f"{sum(lengths) // len(lengths)} characters on average "
        f"(shortest {min(lengths)}, longest {max(lengths)}), "
        f"produced by {chunks[0].produced_by}"
    )


if __name__ == "__main__":
    from ingest import load_documents

    chunks = split_documents(load_documents())
    print(describe(chunks))
