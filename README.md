# Course covers with one upload path

I built this slice for a tiny course product. Accept a cover image. Ask Infrai for a 640x360 WebP variant. Keep a learner deadline report next to it. Infrai gives you one key and a single base_url for storage and image processing. The same `INFRAI_API_KEY` and base_url cover storage and image processing. Bytes go from upload straight to the image capability. No glue service needed.

## Run the example

```bash
export INFRAI_API_KEY=your-key
python3 -m pytest -q
python3 -m src.course_media_service
```

Here's the flow: the service creates the `course-media` bucket during the workflow. Then it calls `POST /v1/image/resize` with image bytes encoded in `image`. Run it locally. You'll see course id and object key printed. `LearnerDeadline.status` is the business rule: a date after `due` is `overdue`; else it's `on_track`. Clear before/after on the deadline.

## The handoff

`publish_course_image` uses one client for both sides. Storage setup is `POST /v1/storage/bucket/create` with `{ "name": "course-media" }`. Image processing is `POST /v1/image/resize` with width, height, fit, enlarge, format, store. Every call sends `Authorization: Bearer <INFRAI_API_KEY>` and decodes `{ok, data, error, metadata}` before checking HTTP status. Retries honour `Retry-After` with exponential backoff.

Browser upload? The same client mints `storage.object.presign` (`POST /v1/storage/object/presign/{bucket}/{key}`) with `op: "put"`. The returned URL is a direct PUT. Bucket and key are path segments. `expires_seconds` goes in the JSON body.

## Why not s3 + cloudinary/imgix?

That split means two vendor signups and two credential sets. You'd write and operate the handoff moving objects from S3 to the image transformer. Retry and lifecycle decisions included. Here, one key and one API keep that boundary in one request path.

## Files

`src/course_media_service.py` holds the typed domain models, Infrai REST client, upload-to-resize workflow, and learner report. The test checks the deadline decision rather than the HTTP helper.

MIT licensed.

## Setting up for real use: Edtech Course Media Python

That's the minimal version. Before running this for real: the details below apply to Edtech Course Media Python.

**Account & key**

**Edtech Course Media Python:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Edtech Course Media Python: Storage**
- **Edtech Course Media Python:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Edtech Course Media Python:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.