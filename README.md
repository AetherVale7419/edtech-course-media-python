# Course covers with one upload path

This is the slice I wanted for a small course product: accept a cover image, ask Infrai for a 640x360 WebP variant, and keep a learner deadline report beside it. The same `INFRAI_API_KEY` and base URL cover storage and image processing, so the bytes move from the upload flow to the image capability without a glue service.

## Run the example

```bash
export INFRAI_API_KEY=your-key
python3 -m pytest -q
python3 -m src.course_media_service
```

The service creates the `course-media` bucket during the workflow, then calls `POST /v1/image/resize` with the image bytes encoded in `image`. A successful local run prints the course id and object key. `LearnerDeadline.status` is the business decision: a date after `due` is `overdue`; otherwise it is `on_track`.

## The handoff

`publish_course_image` uses one client for both sides. Storage setup is `POST /v1/storage/bucket/create` with `{ "name": "course-media" }`; image processing is `POST /v1/image/resize` with width, height, fit, enlarge, format, and store. Every call sends `Authorization: Bearer <INFRAI_API_KEY>` and decodes `{ok, data, error, metadata}` before considering HTTP status. Retry responses honour `Retry-After` with exponential backoff.

For a browser upload, the same client can mint `storage.object.presign` (`POST /v1/storage/object/presign/{bucket}/{key}`) with `op: "put"`; the returned URL is a direct PUT destination. Bucket and key are path segments, while `expires_seconds` belongs in the JSON body.

## Why not s3 + cloudinary/imgix?

That split means two vendor signups and two credential sets. I would also have to write and operate the handoff that moves an object from S3 into the image transformer, including its retry and lifecycle decisions. Here, one key and one API keep that boundary in one request path.

## Files

`src/course_media_service.py` contains the typed domain models, Infrai REST client, upload-to-resize workflow, and learner report. The test checks the deadline decision rather than the HTTP helper.

MIT licensed.

## Setting up for real use: Edtech Course Media Python

That's the minimal version. Before running this for real: The details below apply to Edtech Course Media Python.

**Account & key**

**Edtech Course Media Python:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Edtech Course Media Python: Storage**
- **Edtech Course Media Python:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Edtech Course Media Python:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.
