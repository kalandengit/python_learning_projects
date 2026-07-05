"""Camera / edge-gateway simulator.

Posts synthetic detection events to a running PIDS API so you can watch the
detection -> rule -> alert -> notification pipeline end-to-end without physical cameras.

Usage:
    python simulator/camera_sim.py --api http://localhost:8000 --camera <CAMERA_ID> --count 20

Get a camera id from the seeded data (login as admin@demo.pids / changeme123 and
GET /api/v1/cameras), or pass --discover to have the simulator log in and pick the first camera.
"""
from __future__ import annotations

import argparse
import random
import time
from datetime import datetime, timezone

import httpx

CLASSES = ["human", "vehicle", "car", "truck", "dog", "cat", "bike", "motorcycle"]
# Weight towards nuisance classes to show NAR filtering in action.
WEIGHTS = [3, 2, 1, 1, 4, 4, 2, 1]


def discover_camera(client: httpx.Client, api: str) -> str:
    tok = client.post(
        f"{api}/api/v1/auth/token",
        data={"username": "admin@demo.pids", "password": "changeme123"},
    ).json()["access_token"]
    cams = client.get(f"{api}/api/v1/cameras", headers={"Authorization": f"Bearer {tok}"}).json()
    if not cams:
        raise SystemExit("no cameras found — seed the DB first")
    return cams[0]["id"]


def main() -> None:
    p = argparse.ArgumentParser(description="PIDS camera simulator")
    p.add_argument("--api", default="http://localhost:8000")
    p.add_argument("--camera", help="camera id; omit with --discover to auto-pick")
    p.add_argument("--discover", action="store_true", help="log in as demo admin and pick first camera")
    p.add_argument("--count", type=int, default=20)
    p.add_argument("--interval", type=float, default=0.5, help="seconds between events")
    p.add_argument("--night", action="store_true", help="stamp events at 23:00 to trigger high-crit rules")
    args = p.parse_args()

    with httpx.Client(timeout=10.0) as client:
        camera_id = args.camera or (discover_camera(client, args.api) if args.discover else None)
        if not camera_id:
            raise SystemExit("provide --camera <id> or --discover")

        stats: dict[str, int] = {}
        for i in range(args.count):
            cls = random.choices(CLASSES, weights=WEIGHTS, k=1)[0]
            hour = 23 if args.night else random.randint(0, 23)
            ts = datetime.now(timezone.utc).replace(hour=hour)
            payload = {
                "camera_id": camera_id,
                "object_class": cls,
                "confidence": round(random.uniform(0.3, 0.99), 2),
                "ts": ts.isoformat(),
                "track_id": f"t-{i}",
                "bbox": {"x": 10, "y": 20, "w": 50, "h": 80},
            }
            r = client.post(f"{args.api}/api/v1/events", json=payload)
            outcome = r.json().get("status", f"http-{r.status_code}")
            stats[outcome] = stats.get(outcome, 0) + 1
            print(f"[{i:03d}] {cls:11s} conf={payload['confidence']:.2f} -> {outcome}")
            time.sleep(args.interval)

        print("\nSummary:", stats)


if __name__ == "__main__":
    main()
