from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from dependency_injector.wiring import Provide, inject
import ijson  # type: ignore
from src.container import Container
from src.database.manager import DatabaseManager
from src.database.models import Videos, VideoSnapshots

VideoItemType = dict[str, Any]
SnapshotsItemType = dict[str, Any]

VideoBatchType = list[VideoItemType]
SnapshotsBatchType = list[SnapshotsItemType]


class JsonToDatabaseUploader:  # noqa: D101
    @inject
    def __init__(  # noqa: D107
        self,
        path_to_json: Path,
        bulk_size: int = 50,
        database_manager: DatabaseManager = Provide[
            Container.database_manager_rw
        ],
    ) -> None:
        if not path_to_json.exists():
            raise FileNotFoundError(f"json file not found: {path_to_json}")

        self.path_to_json = path_to_json
        self.bulk_size = bulk_size
        self.database_manager = database_manager

    def _convert_video_data(  # noqa: D102
        self, video_item: VideoItemType
    ) -> VideoItemType:
        return {
            "id": UUID(video_item["id"]),
            "creator_id": UUID(video_item["creator_id"]),
            "video_created_at": datetime.fromisoformat(
                video_item["video_created_at"]
            ),
            "views_count": video_item["views_count"],
            "likes_count": video_item["likes_count"],
            "comments_count": video_item["comments_count"],
            "reports_count": video_item["reports_count"],
            "created_at": datetime.fromisoformat(video_item["created_at"]),
            "updated_at": datetime.fromisoformat(video_item["updated_at"]),
        }

    def _convert_snapshot_data(  # noqa: D102
        self, snapshot_item: SnapshotsItemType
    ) -> SnapshotsItemType:
        return {
            "id": UUID(snapshot_item["id"]),
            "video_id": UUID(snapshot_item["video_id"]),
            "views_count": snapshot_item["views_count"],
            "likes_count": snapshot_item["likes_count"],
            "comments_count": snapshot_item["comments_count"],
            "reports_count": snapshot_item["reports_count"],
            "delta_views_count": snapshot_item["delta_views_count"],
            "delta_likes_count": snapshot_item["delta_likes_count"],
            "delta_comments_count": snapshot_item["delta_comments_count"],
            "delta_reports_count": snapshot_item["delta_reports_count"],
            "created_at": datetime.fromisoformat(snapshot_item["created_at"]),
            "updated_at": datetime.fromisoformat(snapshot_item["updated_at"]),
        }

    async def upload_bulk_to_database(  # noqa: D102
        self,
        videos_batch: VideoBatchType,
        snapshots_batch: SnapshotsBatchType,
    ) -> None:
        async with self.database_manager.session(commit=True) as session:
            if videos_batch:
                session.add_all(
                    [Videos(**video_data) for video_data in videos_batch]
                )

            if snapshots_batch:
                session.add_all(
                    [
                        VideoSnapshots(**snapshot_data)
                        for snapshot_data in snapshots_batch
                    ]
                )

    def load_bulk_from_json(  # noqa: D102
        self,
    ) -> Generator[tuple[VideoBatchType, SnapshotsBatchType]]:
        videos_batch: VideoBatchType = []
        snapshots_batch: SnapshotsBatchType = []

        with open(self.path_to_json, "rb") as file:
            videos_items = ijson.items(file, "videos.item")

            for video_item in videos_items:
                snapshots_items = video_item.pop("snapshots", [])

                video_data = self._convert_video_data(video_item)
                videos_batch.append(video_data)

                for snapshot_item in snapshots_items:
                    snapshot_data = self._convert_snapshot_data(snapshot_item)
                    snapshots_batch.append(snapshot_data)

                if len(videos_batch) == self.bulk_size:
                    yield videos_batch, snapshots_batch

                    videos_batch.clear()
                    snapshots_batch.clear()

        if videos_batch or snapshots_batch:
            yield videos_batch, snapshots_batch
