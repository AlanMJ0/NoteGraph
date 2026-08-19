# Document chunking logic
# This file splits a document into smaller pieces ("chunks") that we can
# store and search individually. We try to split on section headers first
# (lines starting with #), and keep code blocks (```...```) from being cut
# in half.

import uuid
from src import config


# A plain class to hold information about one chunk. Unlike a dictionary,
# a class lets us write chunk.text instead of chunk["text"], and groups
# related data together with a name.
import hashlib

class Chunk:
    def __init__(self, text, source_file, position, section_heading=""):
        # Deterministic ID based on file and position prevents duplication on re-ingest
        hash_input = f"{source_file}_{position}".encode("utf-8")
        self.chunk_id = hashlib.md5(hash_input).hexdigest()[:8]
        self.text = text
        self.source_file = source_file
        self.position = position
        self.section_heading = section_heading
        self.character_count = len(text)

    def to_metadata(self):
        # Returns a plain dictionary version of this chunk's info,
        # which is what ChromaDB will want later.
        return {
            "chunk_id": self.chunk_id,
            "source_file": self.source_file,
            "position": self.position,
            "character_count": self.character_count,
            "section_heading": self.section_heading,
        }


def split_into_sections(text):
    """
    Splits text into a list of (heading, section_text) pairs, wherever a
    line starts with '#'. If there are no headers at all, returns the
    whole text as one section with an empty heading.
    """
    lines = text.split("\n")
    sections = []
    current_heading = ""
    current_lines = []

    for line in lines:
        if line.strip().startswith("#"):
            # We hit a new header. Save whatever section we were building,
            # then start a new one.
            if current_lines:
                sections.append((current_heading, "\n".join(current_lines)))
            current_heading = line.strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    # Don't forget to save the last section after the loop ends.
    if current_lines:
        sections.append((current_heading, "\n".join(current_lines)))

    return sections


def protect_code_blocks(text):
    """
    Finds fenced code blocks (```...```) and replaces each one with a
    placeholder like __CODE_BLOCK_0__, so that later splitting logic
    doesn't cut a function in half. Returns the modified text, plus a
    dictionary mapping each placeholder back to its real code block.
    """
    parts = text.split("```")
    protected_text = ""
    code_blocks = {}
    block_number = 0

    # When you split on "```", the pieces alternate: normal text, code,
    # normal text, code, and so on. Even positions (0, 2, 4...) are
    # normal text; odd positions (1, 3, 5...) are code blocks.
    for i in range(len(parts)):
        if i % 2 == 1:
            placeholder = "__CODE_BLOCK_" + str(block_number) + "__"
            code_blocks[placeholder] = "```" + parts[i] + "```"
            protected_text = protected_text + placeholder
            block_number = block_number + 1
        else:
            protected_text = protected_text + parts[i]

    return protected_text, code_blocks


def restore_code_blocks(text, code_blocks):
    for placeholder in code_blocks:
        text = text.replace(placeholder, code_blocks[placeholder])
    return text


def split_by_paragraphs(text, max_chars, overlap_chars):
    """
    Fallback for sections that are still too long: splits on blank lines
    (paragraph breaks), packing paragraphs together until we hit max_chars,
    then starting a new chunk. Each new chunk starts with a little overlap
    from the end of the previous one, so context isn't lost at the boundary.
    """
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        if paragraph.strip() == "":
            continue

        if len(current_chunk) + len(paragraph) < max_chars:
            if current_chunk == "":
                current_chunk = paragraph
            else:
                current_chunk = current_chunk + "\n\n" + paragraph
        else:
            if current_chunk != "":
                chunks.append(current_chunk)
            # Carry a small overlap from the end of the last chunk forward,
            # so the next chunk has a bit of shared context.
            overlap_text = current_chunk[-overlap_chars:]
            current_chunk = overlap_text + "\n\n" + paragraph

    if current_chunk != "":
        chunks.append(current_chunk)

    return chunks


def chunk_document(text, source_file):
    """
    The main function other files will call. Takes raw document text and
    returns a list of Chunk objects, ready to be stored.
    """
    sections = split_into_sections(text)
    all_chunks = []
    position = 0

    for heading, section_text in sections:
        protected_text, code_blocks = protect_code_blocks(section_text)

        if len(protected_text) <= config.MAX_CHUNK_CHARS:
            pieces = [protected_text]
        else:
            pieces = split_by_paragraphs(protected_text, config.MAX_CHUNK_CHARS, config.CHUNK_OVERLAP_CHARS)

        for piece in pieces:
            restored_text = restore_code_blocks(piece, code_blocks).strip()
            if restored_text == "":
                continue

            new_chunk = Chunk(
                text=restored_text,
                source_file=source_file,
                position=position,
                section_heading=heading,
            )
            all_chunks.append(new_chunk)
            position = position + 1

    return all_chunks


# Quick manual test -- run with: python -m src.chunker
if __name__ == "__main__":
    sample_text = """# Sorting Algorithms

## QuickSort
QuickSort has average time complexity O(n log n).

```python
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    return arr
```

It performs poorly on already-sorted input without randomization.
"""

    chunks = chunk_document(sample_text, "sample.md")
    for chunk in chunks:
        print("--- chunk", chunk.position, "(section:", chunk.section_heading, ") ---")
        print(chunk.text)
        print("")