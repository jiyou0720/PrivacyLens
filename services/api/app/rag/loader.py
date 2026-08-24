from pathlib import Path


def load_documents(
    directory: str,
) -> list[dict[str, str]]:

    documents = []

    path = Path(directory)

    for file in path.glob("*.txt"):

        content = file.read_text(
            encoding="utf-8"
        )

        documents.append(
            {
                "source": file.name,
                "content": content,
            }
        )

    return documents