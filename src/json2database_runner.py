from asyncio import run
from pathlib import Path

from src.container import Container
from src.scripts.json_to_database import JsonToDatabaseUploader


async def load_json_to_database() -> None:  # noqa: D103
    uploader = JsonToDatabaseUploader(path_to_json=Path("demo/videos.json"))

    for videos_batch, snapshots_batch in uploader.load_bulk_from_json():
        await uploader.upload_bulk_to_database(videos_batch, snapshots_batch)


if __name__ == "__main__":

    container = Container()
    container.wire([__name__])

    run(load_json_to_database())
