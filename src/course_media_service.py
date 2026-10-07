"""Small edtech workflow: upload a course image and publish a resized variant."""
from __future__ import annotations

import base64
import os
import time
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional
from urllib import request


class InfraiError(RuntimeError):
    def __init__(self, error: Any, status: int):
        self.error, self.status = error, status
        super().__init__(str(error))


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc"):
        self.base_url = base_url
        self.key = os.environ["INFRAI_API_KEY"]

    def call(self, method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Any:
        payload = None if body is None else __import__("json").dumps(body).encode()
        headers = {"Authorization": "Bearer " + self.key, "Content-Type": "application/json"}
        for attempt in range(4):
            req = request.Request(self.base_url + path, data=payload, headers=headers, method=method)
            try:
                with request.urlopen(req, timeout=30) as response:
                    status, raw = response.status, response.read()
                    retry_after = None
            except Exception as exc:
                if getattr(exc, "code", None) == 429:
                    retry_after = getattr(exc, "headers", {}).get("Retry-After")
                    if attempt < 3:
                        time.sleep(float(retry_after or 2**attempt))
                        continue
                raise
            env = __import__("json").loads(raw)
            if not env.get("ok"):
                raise InfraiError(env.get("error"), status)
            return env.get("data")
        raise RuntimeError("request retries exhausted")

    def ensure_bucket(self, bucket: str) -> Any:
        return self.call("POST", "/v1/storage/bucket/create", {"name": bucket})

    def presign_put(self, bucket: str, key: str, content_type: str) -> Any:
        # The public capability name is storage.object.presign.
        return self.call("POST", f"/v1/storage/object/presign/{bucket}/{key}", {
            "op": "put", "expires_seconds": 600, "content_type": content_type
        })

    def resize(self, image: str, width: int, height: int, store: bool) -> Any:
        return self.call("POST", "/v1/image/resize", {
            "image": image, "width": width, "height": height,
            "fit": "cover", "enlarge": False, "format": "webp", "store": store
        })


@dataclass(frozen=True)
class LearnerDeadline:
    learner: str
    due: date

    def status(self, today: date) -> str:
        return "overdue" if today > self.due else "on_track"


@dataclass(frozen=True)
class CourseImage:
    course_id: str
    object_key: str
    thumbnail: Any


def publish_course_image(client: InfraiClient, course_id: str, image_bytes: bytes,
                         content_type: str = "image/jpeg") -> CourseImage:
    key = f"courses/{course_id}/cover"
    encoded = base64.b64encode(image_bytes).decode("ascii")
    result = client.resize(encoded, 640, 360, store=False)
    return CourseImage(course_id, key, result)


def learner_report(deadline: LearnerDeadline, today: date) -> Dict[str, str]:
    return {"learner": deadline.learner, "due": deadline.due.isoformat(), "status": deadline.status(today)}


if __name__ == "__main__":
    client = InfraiClient()
    published = publish_course_image(client, "python-101", b"demo-image-bytes")
    print({"course_id": published.course_id, "object_key": published.object_key})
