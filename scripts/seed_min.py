"""
Minimal seed / fixtures for Amazon Second Life AI.

Owner: B (P0-B2)

Creates a reproducible baseline dataset that every service and the frontend
can build against immediately. Idempotent — safe to re-run at any time.

What gets created
-----------------
Users (6):
  - 1 demo returner   : the primary customer for the judge happy-path
  - 4 nearby buyers   : spread around the returner, various interests
  - 1 admin           : operational/observer persona

Products (4):
  - 1 golden-path product : headphones, Electronics, used by the demo flow
  - 3 supporting products : different categories for matching variety

Returns (2):
  - 1 golden-path return  : pre-wired to GOLDEN_PATH_MEDIA_KEY, status SUBMITTED
  - 1 supporting return   : different category, for testing edge cases

MinIO:
  - Uploads the golden-path media placeholder so grading service can reference it

Usage
-----
    # From repo root (services must be up):
    python scripts/seed_min.py

    # Reset and re-seed:
    python scripts/seed_min.py --reset

Environment
-----------
Reads from .env (or env vars). Services must be reachable.
"""

import argparse
import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Bootstrap: add packages/shared-py to path so shared_py is importable
# without requiring an editable install in every context
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "packages" / "shared-py"))

try:
    import asyncpg
    import boto3
    from botocore.exceptions import ClientError
except ImportError as e:
    print(f"[seed_min] Missing dependency: {e}")
    print("Run: pip install asyncpg boto3")
    sys.exit(1)

try:
    import asyncio
except ImportError:
    print("[seed_min] Python 3.10+ required (asyncio)")
    sys.exit(1)

from shared_py.ai.client import (
    GOLDEN_PATH_MEDIA_KEY,
    GOLDEN_PATH_CATEGORY,
    GOLDEN_PATH_REASON,
    GOLDEN_PATH_VALUE_ESTIMATE,
)
from shared_py.schemas.enums import ReturnStatus

# ---------------------------------------------------------------------------
# Config from environment
# ---------------------------------------------------------------------------

DB_URLS: dict[str, str] = {
    "user": os.getenv(
        "DATABASE_URL_USER",
        "postgresql://slmai:slmai_password@localhost:5432/slmai_user",
    ),
    "grading": os.getenv(
        "DATABASE_URL_GRADING",
        "postgresql://slmai:slmai_password@localhost:5432/slmai_grading",
    ),
    "lifecycle": os.getenv(
        "DATABASE_URL_LIFECYCLE",
        "postgresql://slmai:slmai_password@localhost:5432/slmai_lifecycle",
    ),
    "passport": os.getenv(
        "DATABASE_URL_PASSPORT",
        "postgresql://slmai:slmai_password@localhost:5432/slmai_passport",
    ),
    "matching": os.getenv(
        "DATABASE_URL_MATCHING",
        "postgresql://slmai:slmai_password@localhost:5432/slmai_matching",
    ),
    "sustainability": os.getenv(
        "DATABASE_URL_SUSTAINABILITY",
        "postgresql://slmai:slmai_password@localhost:5432/slmai_sustainability",
    ),
}

# Convert asyncpg+postgresql style to plain postgresql for asyncpg
for _k, _v in DB_URLS.items():
    DB_URLS[_k] = _v.replace("postgresql+asyncpg://", "postgresql://")

S3_ENDPOINT = os.getenv("S3_ENDPOINT_URL", "http://localhost:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")
S3_BUCKET = os.getenv("S3_BUCKET", "slmai-media")

# ---------------------------------------------------------------------------
# Deterministic UUIDs — same every run for idempotency
# ---------------------------------------------------------------------------

def _det_uuid(name: str) -> str:
    """Deterministic UUID v5 from a name. Same name → same UUID every run."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"slmai.seed.{name}"))


# ── Users ──────────────────────────────────────────────────────────────────

USER_RETURNER_ID     = _det_uuid("user.returner")
USER_BUYER_ALICE_ID  = _det_uuid("user.buyer.alice")
USER_BUYER_BOB_ID    = _det_uuid("user.buyer.bob")
USER_BUYER_CAROL_ID  = _det_uuid("user.buyer.carol")
USER_BUYER_DAN_ID    = _det_uuid("user.buyer.dan")
USER_ADMIN_ID        = _det_uuid("user.admin")

# ── Products ───────────────────────────────────────────────────────────────

PRODUCT_HEADPHONES_ID  = _det_uuid("product.headphones")   # golden-path
PRODUCT_LAPTOP_ID      = _det_uuid("product.laptop")
PRODUCT_JACKET_ID      = _det_uuid("product.jacket")
PRODUCT_CHAIR_ID       = _det_uuid("product.chair")

# ── Returns ────────────────────────────────────────────────────────────────

RETURN_GOLDEN_ID  = _det_uuid("return.golden")   # golden-path demo return
RETURN_LAPTOP_ID  = _det_uuid("return.laptop")   # supporting return

# ---------------------------------------------------------------------------
# Seed data definitions
# ---------------------------------------------------------------------------

USERS: list[dict[str, Any]] = [
    {
        "id": USER_RETURNER_ID,
        "email": "demo.returner@slmai.dev",
        "display_name": "Demo Customer",
        # bcrypt hash of "demo1234" — pre-computed, no runtime crypto needed
        "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQyCMRasHz3HNBj.YGX6VHq6u",
        "lat": 12.9716,
        "lng": 77.5946,
        "city": "Bengaluru",
        "interests": ["electronics", "gaming", "wearables"],
        "green_credits": 0,
        "role": "customer",
    },
    {
        "id": USER_BUYER_ALICE_ID,
        "email": "alice.nearby@slmai.dev",
        "display_name": "Alice (Nearby)",
        "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQyCMRasHz3HNBj.YGX6VHq6u",
        "lat": 12.9750,   # ~0.4 km from returner
        "lng": 77.5965,
        "city": "Bengaluru",
        "interests": ["electronics", "gaming", "headphones"],
        "green_credits": 120,
        "role": "customer",
    },
    {
        "id": USER_BUYER_BOB_ID,
        "email": "bob.local@slmai.dev",
        "display_name": "Bob (Local)",
        "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQyCMRasHz3HNBj.YGX6VHq6u",
        "lat": 12.9800,   # ~0.9 km from returner
        "lng": 77.5900,
        "city": "Bengaluru",
        "interests": ["electronics", "laptops", "accessories"],
        "green_credits": 80,
        "role": "customer",
    },
    {
        "id": USER_BUYER_CAROL_ID,
        "email": "carol.fashion@slmai.dev",
        "display_name": "Carol (Fashion)",
        "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQyCMRasHz3HNBj.YGX6VHq6u",
        "lat": 12.9680,   # ~0.4 km from returner
        "lng": 77.5920,
        "city": "Bengaluru",
        "interests": ["clothing", "fashion", "accessories"],
        "green_credits": 45,
        "role": "customer",
    },
    {
        "id": USER_BUYER_DAN_ID,
        "email": "dan.remote@slmai.dev",
        "display_name": "Dan (Regional)",
        "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQyCMRasHz3HNBj.YGX6VHq6u",
        "lat": 13.0300,   # ~6.5 km from returner
        "lng": 77.5800,
        "city": "Bengaluru North",
        "interests": ["furniture", "home", "electronics"],
        "green_credits": 200,
        "role": "customer",
    },
    {
        "id": USER_ADMIN_ID,
        "email": "admin@slmai.dev",
        "display_name": "Platform Admin",
        "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQyCMRasHz3HNBj.YGX6VHq6u",
        "lat": 12.9716,
        "lng": 77.5946,
        "city": "Bengaluru",
        "interests": [],
        "green_credits": 0,
        "role": "admin",
    },
]

PRODUCTS: list[dict[str, Any]] = [
    {
        "id": PRODUCT_HEADPHONES_ID,
        "owner_user_id": USER_RETURNER_ID,
        "category": GOLDEN_PATH_CATEGORY,
        "title": "Zebronics Jet PRO Premium Wired Gaming Headphones",
        "brand": "Zebronics",
        "attributes": {
            "color": "Black/Blue",
            "connectivity": "Wired",
            "driver_size": "40mm",
            "weight_grams": 320,
            "original_price_usd": GOLDEN_PATH_VALUE_ESTIMATE,
        },
        # This media key is the golden-path constant — grading service will hash it
        # to produce the reproducible Grade B result for the demo
        "demo_media_key": GOLDEN_PATH_MEDIA_KEY,
    },
    {
        "id": PRODUCT_LAPTOP_ID,
        "owner_user_id": USER_RETURNER_ID,
        "category": "electronics",
        "title": "Lenovo IdeaPad 3 15.6-inch Laptop",
        "brand": "Lenovo",
        "attributes": {
            "ram_gb": 8,
            "storage_gb": 512,
            "original_price_usd": 420.00,
        },
        "demo_media_key": "products/laptop/lenovo-ideapad-001.jpg",
    },
    {
        "id": PRODUCT_JACKET_ID,
        "owner_user_id": USER_BUYER_CAROL_ID,
        "category": "clothing",
        "title": "Columbia Men's Watertight II Rain Jacket",
        "brand": "Columbia",
        "attributes": {
            "size": "M",
            "color": "Navy",
            "original_price_usd": 65.00,
        },
        "demo_media_key": "products/clothing/columbia-jacket-001.jpg",
    },
    {
        "id": PRODUCT_CHAIR_ID,
        "owner_user_id": USER_BUYER_DAN_ID,
        "category": "furniture",
        "title": "Ergonomic Mesh Office Chair",
        "brand": "Furmax",
        "attributes": {
            "adjustable_height": True,
            "original_price_usd": 89.00,
        },
        "demo_media_key": "products/furniture/ergonomic-chair-001.jpg",
    },
]

RETURNS: list[dict[str, Any]] = [
    {
        # ── GOLDEN PATH RETURN ──
        # This is the return used in the judge demo walkthrough.
        # It flows through the full 10-event saga.
        "id": RETURN_GOLDEN_ID,
        "product_id": PRODUCT_HEADPHONES_ID,
        "user_id": USER_RETURNER_ID,
        "reason": GOLDEN_PATH_REASON,
        "media": [GOLDEN_PATH_MEDIA_KEY],
        "status": ReturnStatus.SUBMITTED.value,
        "is_golden_path": True,
    },
    {
        # ── SUPPORTING RETURN ──
        # Used to test a second saga flow (laptop, higher value product).
        "id": RETURN_LAPTOP_ID,
        "product_id": PRODUCT_LAPTOP_ID,
        "user_id": USER_RETURNER_ID,
        "reason": "Screen has dead pixels",
        "media": ["products/laptop/lenovo-ideapad-001.jpg"],
        "status": ReturnStatus.SUBMITTED.value,
        "is_golden_path": False,
    },
]

# ---------------------------------------------------------------------------
# MinIO helpers
# ---------------------------------------------------------------------------

def _ensure_bucket(s3_client: Any) -> None:
    """Create the media bucket if it doesn't exist."""
    try:
        s3_client.head_bucket(Bucket=S3_BUCKET)
        print(f"  [minio] Bucket '{S3_BUCKET}' already exists")
    except ClientError:
        s3_client.create_bucket(Bucket=S3_BUCKET)
        print(f"  [minio] Created bucket '{S3_BUCKET}'")


def _upload_placeholder(s3_client: Any, key: str) -> None:
    """Upload a 1-pixel PNG placeholder so grading can reference the media key."""
    # Minimal valid PNG (1×1 transparent pixel)
    PNG_1PX = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
        b"\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    try:
        s3_client.head_object(Bucket=S3_BUCKET, Key=key)
        print(f"  [minio] {key} already exists — skipping")
    except ClientError:
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=PNG_1PX,
            ContentType="image/png",
            Metadata={"seed": "placeholder", "product": key.split("/")[-1]},
        )
        print(f"  [minio] Uploaded placeholder: {key}")


def seed_minio() -> None:
    """Upload media placeholders for all seeded products."""
    print("\n[minio] Seeding media placeholders...")
    s3 = boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        region_name="us-east-1",
    )
    _ensure_bucket(s3)

    for product in PRODUCTS:
        _upload_placeholder(s3, product["demo_media_key"])

    print("[minio] Done.")


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

NOW = datetime.now(timezone.utc).isoformat()


async def _upsert(conn: Any, table: str, record: dict[str, Any], pk: str = "id") -> None:
    """Insert or update a record. Uses ON CONFLICT DO UPDATE for idempotency."""
    cols = list(record.keys())
    values = list(record.values())
    placeholders = ", ".join(f"${i + 1}" for i in range(len(cols)))
    col_names = ", ".join(cols)
    updates = ", ".join(
        f"{col} = EXCLUDED.{col}" for col in cols if col != pk
    )
    query = (
        f"INSERT INTO {table} ({col_names}) VALUES ({placeholders}) "
        f"ON CONFLICT ({pk}) DO UPDATE SET {updates}"
    )
    await conn.execute(query, *values)


async def seed_users() -> None:
    """Seed users into slmai_user database."""
    print("\n[user-db] Seeding users...")
    conn = await asyncpg.connect(DB_URLS["user"])
    try:
        for u in USERS:
            record = {
                "id": u["id"],
                "email": u["email"],
                "display_name": u["display_name"],
                "password_hash": u["password_hash"],
                "lat": u["lat"],
                "lng": u["lng"],
                "city": u["city"],
                "interests": json.dumps(u["interests"]),
                "green_credits": u["green_credits"],
                "created_at": NOW,
                "updated_at": NOW,
            }
            await _upsert(conn, "users", record)
            print(f"  [user-db] Upserted: {u['email']}")
    finally:
        await conn.close()
    print("[user-db] Done.")


async def seed_products() -> None:
    """Seed products into slmai_passport database (Passport owns canonical Product)."""
    print("\n[passport-db] Seeding products...")
    conn = await asyncpg.connect(DB_URLS["passport"])
    try:
        for p in PRODUCTS:
            record = {
                "id": p["id"],
                "owner_user_id": p["owner_user_id"],
                "category": p["category"],
                "title": p["title"],
                "brand": p.get("brand"),
                "attributes": json.dumps(p.get("attributes", {})),
                "created_at": NOW,
                "updated_at": NOW,
            }
            await _upsert(conn, "products", record)
            print(f"  [passport-db] Upserted: {p['title'][:50]}")
    finally:
        await conn.close()
    print("[passport-db] Done.")


async def seed_returns() -> None:
    """Seed returns into gateway database (Gateway owns Return entity)."""
    print("\n[gateway-db] Seeding returns...")
    # Gateway uses the default postgres DB since it has no dedicated DB
    # (it uses slmai_user or a gateway-specific table — adjust if Member A chose differently)
    # For now seed into slmai_user with a returns table (or skip if not yet migrated)
    try:
        conn = await asyncpg.connect(DB_URLS["user"])
        try:
            # Check if returns table exists yet (may not until P1-A2)
            exists = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'returns')"
            )
            if not exists:
                print("  [gateway-db] 'returns' table not yet migrated — skipping DB insert.")
                print("  [gateway-db] Returns data is defined in SEED_RETURNS constant for later use.")
                return

            for r in RETURNS:
                record = {
                    "id": r["id"],
                    "product_id": r["product_id"],
                    "user_id": r["user_id"],
                    "reason": r["reason"],
                    "media": json.dumps(r["media"]),
                    "status": r["status"],
                    "created_at": NOW,
                    "updated_at": NOW,
                }
                await _upsert(conn, "returns", record)
                label = "GOLDEN PATH" if r.get("is_golden_path") else "supporting"
                print(f"  [gateway-db] Upserted return ({label}): {r['id']}")
        finally:
            await conn.close()
    except Exception as e:
        print(f"  [gateway-db] Skipped returns (not yet available): {e}")
    print("[gateway-db] Done.")


async def reset_seed_data() -> None:
    """Remove seeded records for a clean re-seed."""
    print("\n[reset] Removing seed data...")

    # Users
    try:
        conn = await asyncpg.connect(DB_URLS["user"])
        ids = [u["id"] for u in USERS]
        await conn.execute("DELETE FROM users WHERE id = ANY($1::uuid[])", ids)
        await conn.close()
        print(f"  [reset] Deleted {len(ids)} users")
    except Exception as e:
        print(f"  [reset] Users: {e}")

    # Products
    try:
        conn = await asyncpg.connect(DB_URLS["passport"])
        ids = [p["id"] for p in PRODUCTS]
        await conn.execute("DELETE FROM products WHERE id = ANY($1::uuid[])", ids)
        await conn.close()
        print(f"  [reset] Deleted {len(ids)} products")
    except Exception as e:
        print(f"  [reset] Products: {e}")

    print("[reset] Done.")


# ---------------------------------------------------------------------------
# Seed manifest
# ---------------------------------------------------------------------------

def print_manifest() -> None:
    """Print a summary of what was seeded, useful for other team members."""
    print("\n" + "=" * 60)
    print("SEED MANIFEST — Amazon Second Life AI (Minimal)")
    print("=" * 60)

    print("\nUSERS")
    for u in USERS:
        credits = f"  ({u['green_credits']} credits)" if u["green_credits"] else ""
        print(f"  {u['email']:<35} id={u['id'][:8]}...{credits}")
    print(f"  Password for all accounts: demo1234")

    print("\nPRODUCTS")
    for p in PRODUCTS:
        golden = " ← GOLDEN PATH" if p["id"] == PRODUCT_HEADPHONES_ID else ""
        print(f"  {p['title'][:50]:<52} id={p['id'][:8]}...{golden}")

    print("\nRETURNS")
    for r in RETURNS:
        golden = " ← GOLDEN PATH (use this for demo)" if r.get("is_golden_path") else ""
        print(f"  return_id={r['id'][:8]}...  product={r['product_id'][:8]}...{golden}")

    print("\nGOLDEN PATH CONSTANTS (shared_py.ai.client)")
    print(f"  GOLDEN_PATH_MEDIA_KEY = {GOLDEN_PATH_MEDIA_KEY}")
    print(f"  GOLDEN_PATH_CATEGORY  = {GOLDEN_PATH_CATEGORY}")
    print(f"  GOLDEN_PATH_REASON    = {GOLDEN_PATH_REASON}")
    print(f"  GOLDEN_PATH_VALUE_ESTIMATE = {GOLDEN_PATH_VALUE_ESTIMATE}")

    print("\nMINIO BUCKET")
    print(f"  bucket : {S3_BUCKET}")
    print(f"  endpoint: {S3_ENDPOINT}")
    for p in PRODUCTS:
        print(f"  key    : {p['demo_media_key']}")

    print("=" * 60 + "\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main(reset: bool = False) -> None:
    if reset:
        await reset_seed_data()

    errors: list[str] = []

    # MinIO first (no DB dependency)
    try:
        seed_minio()
    except Exception as e:
        print(f"  [minio] WARNING: {e} — MinIO may not be running yet")
        errors.append(f"minio: {e}")

    # User DB
    try:
        await seed_users()
    except Exception as e:
        print(f"  [user-db] WARNING: {e} — User service DB may not be migrated yet")
        errors.append(f"user-db: {e}")

    # Passport DB (products)
    try:
        await seed_products()
    except Exception as e:
        print(f"  [passport-db] WARNING: {e} — Passport service DB may not be migrated yet")
        errors.append(f"passport-db: {e}")

    # Gateway DB (returns) — gracefully skips if tables not ready
    await seed_returns()

    print_manifest()

    if errors:
        print(f"[seed_min] Completed with {len(errors)} warning(s):")
        for err in errors:
            print(f"  - {err}")
        print("  Re-run after services/migrations are up to seed skipped tables.")
    else:
        print("[seed_min] All seed data applied successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed minimal fixtures for SLMAI")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing seed data before re-seeding (clean slate)",
    )
    args = parser.parse_args()
    asyncio.run(main(reset=args.reset))
