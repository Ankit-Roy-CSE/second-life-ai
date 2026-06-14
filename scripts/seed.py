"""
Full demo-narrative seed for Amazon Second Life AI.

Owner: A (P3-A1)

Builds on top of seed_min.py with a compelling narrative for judges:
- Richer user stories (personas with contexts)
- Complete golden-path event saga pre-loaded
- Additional demo returns across all lifecycle decisions
- Dashboard-ready sustainability metrics
- Pre-computed matches and marketplace listings

What gets created
-----------------
Everything from seed_min.py, plus:
  - Enhanced user personas with realistic backstories
  - 8 total returns covering all lifecycle actions
  - Pre-seeded grades, decisions, passports, matches, listings
  - Sustainability records showing CO₂/waste/value impact
  - Demo data that shows off the full system capabilities

Usage
-----
    # From repo root (all services must be up and migrated):
    python scripts/seed.py

    # Reset everything and re-seed:
    python scripts/seed.py --reset

    # Quick mode (only new demo data, skip seed_min):
    python scripts/seed.py --quick

Environment
-----------
Requires all services running with migrations complete.
Falls back gracefully if some services aren't ready yet.
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

# Bootstrap: add packages/shared-py to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "packages" / "shared-py"))

try:
    import asyncpg
    import httpx
except ImportError as e:
    print(f"[seed] Missing dependency: {e}")
    print("Run: pip install asyncpg httpx")
    sys.exit(1)

import asyncio

from shared_py.ai.client import GOLDEN_PATH_MEDIA_KEY, GOLDEN_PATH_CATEGORY, GOLDEN_PATH_REASON
from shared_py.schemas.enums import (
    Grade,
    LifecycleAction,
    ReturnStatus,
    ListingChannel,
    ListingStatus,
)

# Import seed_min for base data
try:
    import seed_min
except ImportError:
    print("[seed] Could not import seed_min — ensure scripts/seed_min.py exists")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Config from environment
# ---------------------------------------------------------------------------

DB_URLS = seed_min.DB_URLS

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000")
GRADING_URL = os.getenv("GRADING_URL", "http://localhost:8002")
LIFECYCLE_URL = os.getenv("LIFECYCLE_URL", "http://localhost:8003")
PASSPORT_URL = os.getenv("PASSPORT_URL", "http://localhost:8004")
MATCHING_URL = os.getenv("MATCHING_URL", "http://localhost:8005")
SUSTAINABILITY_URL = os.getenv("SUSTAINABILITY_URL", "http://localhost:8006")

# ---------------------------------------------------------------------------
# Demo narrative data — additional returns with variety
# ---------------------------------------------------------------------------

def _det_uuid(name: str) -> str:
    """Reuse deterministic UUID helper from seed_min."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"slmai.seed.{name}"))


# Additional demo returns (beyond the 2 in seed_min)
DEMO_RETURNS = [
    {
        "id": _det_uuid("return.demo.donate"),
        "product_id": seed_min.PRODUCT_JACKET_ID,
        "user_id": seed_min.USER_BUYER_CAROL_ID,
        "reason": "Style no longer fits my wardrobe",
        "media": ["products/clothing/columbia-jacket-001.jpg"],
        "status": ReturnStatus.SUBMITTED.value,
        "expected_grade": Grade.B,
        "expected_action": LifecycleAction.DONATE,
        "narrative": "Carol wants to donate a jacket in good condition to someone in need",
    },
    {
        "id": _det_uuid("return.demo.refurbish"),
        "product_id": _det_uuid("product.demo.phone"),
        "user_id": seed_min.USER_RETURNER_ID,
        "reason": "Battery drains quickly, screen has minor scratches",
        "media": ["products/electronics/smartphone-001.jpg"],
        "status": ReturnStatus.SUBMITTED.value,
        "expected_grade": Grade.C,
        "expected_action": LifecycleAction.REFURBISH,
        "narrative": "Smartphone needs refurbishment before resale",
    },
    {
        "id": _det_uuid("return.demo.recycle"),
        "product_id": _det_uuid("product.demo.broken-tablet"),
        "user_id": seed_min.USER_BUYER_BOB_ID,
        "reason": "Screen is cracked, device won't turn on",
        "media": ["products/electronics/tablet-broken-001.jpg"],
        "status": ReturnStatus.SUBMITTED.value,
        "expected_grade": Grade.D,
        "expected_action": LifecycleAction.RECYCLE,
        "narrative": "Beyond repair — extract materials for recycling",
    },
    {
        "id": _det_uuid("return.demo.resell"),
        "product_id": _det_uuid("product.demo.watch"),
        "user_id": seed_min.USER_BUYER_ALICE_ID,
        "reason": "Upgraded to newer model, this one is like new",
        "media": ["products/wearables/smartwatch-001.jpg"],
        "status": ReturnStatus.SUBMITTED.value,
        "expected_grade": Grade.A,
        "expected_action": LifecycleAction.RESELL,
        "narrative": "Premium condition — immediate resale candidate",
    },
    {
        "id": _det_uuid("return.demo.hyperlocal"),
        "product_id": seed_min.PRODUCT_CHAIR_ID,
        "user_id": seed_min.USER_BUYER_DAN_ID,
        "reason": "Moving to new apartment, won't fit the space",
        "media": ["products/furniture/ergonomic-chair-001.jpg"],
        "status": ReturnStatus.SUBMITTED.value,
        "expected_grade": Grade.B,
        "expected_action": LifecycleAction.HYPERLOCAL,
        "narrative": "Heavy item — perfect for hyperlocal match to avoid shipping",
    },
]

# Additional demo products for the new returns
DEMO_PRODUCTS = [
    {
        "id": _det_uuid("product.demo.phone"),
        "owner_user_id": seed_min.USER_RETURNER_ID,
        "category": "electronics",
        "title": "Samsung Galaxy S21 128GB",
        "brand": "Samsung",
        "attributes": {
            "storage_gb": 128,
            "color": "Phantom Gray",
            "original_price_usd": 699.00,
        },
    },
    {
        "id": _det_uuid("product.demo.broken-tablet"),
        "owner_user_id": seed_min.USER_BUYER_BOB_ID,
        "category": "electronics",
        "title": "iPad Air (4th Gen) - Damaged",
        "brand": "Apple",
        "attributes": {
            "storage_gb": 64,
            "condition": "broken",
            "original_price_usd": 599.00,
        },
    },
    {
        "id": _det_uuid("product.demo.watch"),
        "owner_user_id": seed_min.USER_BUYER_ALICE_ID,
        "category": "wearables",
        "title": "Apple Watch Series 7 GPS 41mm",
        "brand": "Apple",
        "attributes": {
            "color": "Midnight",
            "band": "Sport Band",
            "original_price_usd": 399.00,
        },
    },
]

# ---------------------------------------------------------------------------
# Database seeding functions (extended from seed_min)
# ---------------------------------------------------------------------------

NOW = datetime.now(timezone.utc)


async def _upsert(conn: Any, table: str, record: dict[str, Any], pk: str = "id") -> None:
    """Idempotent insert-or-update (reuse seed_min pattern)."""
    cols = list(record.keys())
    values = list(record.values())
    placeholders = ", ".join(f"${i + 1}" for i in range(len(cols)))
    col_names = ", ".join(cols)
    updates = ", ".join(f"{col} = EXCLUDED.{col}" for col in cols if col != pk)
    query = (
        f"INSERT INTO {table} ({col_names}) VALUES ({placeholders}) "
        f"ON CONFLICT ({pk}) DO UPDATE SET {updates}"
    )
    await conn.execute(query, *values)


async def seed_demo_products() -> None:
    """Seed additional demo products into Passport DB."""
    print("\n[passport-db] Seeding additional demo products...")
    conn = await asyncpg.connect(DB_URLS["passport"])
    try:
        for p in DEMO_PRODUCTS:
            record = {
                "id": p["id"],
                "owner_user_id": p["owner_user_id"],
                "category": p["category"],
                "title": p["title"],
                "brand": p.get("brand"),
                "attributes": json.dumps(p.get("attributes", {})),
                "created_at": NOW.isoformat(),
                "updated_at": NOW.isoformat(),
            }
            await _upsert(conn, "products", record)
            print(f"  [passport-db] Upserted: {p['title'][:50]}")
    except Exception as e:
        print(f"  [passport-db] Error seeding products: {e}")
    finally:
        await conn.close()
    print("[passport-db] Demo products done.")


async def seed_demo_returns() -> None:
    """Seed demo returns into Gateway DB (returns table)."""
    print("\n[gateway-db] Seeding demo returns...")
    try:
        # Gateway stores returns in the slmai_user DB (shared with User Service)
        # This matches the pattern from seed_min.py
        conn = await asyncpg.connect(DB_URLS["user"])
        try:
            # Check if returns table exists
            exists = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'returns')"
            )
            if not exists:
                print("  [gateway-db] 'returns' table not yet migrated — skipping")
                return

            for r in DEMO_RETURNS:
                record = {
                    "id": r["id"],
                    "product_id": r["product_id"],
                    "user_id": r["user_id"],
                    "reason": r["reason"],
                    "media": json.dumps(r["media"]),
                    "status": r["status"],
                    "created_at": (NOW - timedelta(hours=2)).isoformat(),
                    "updated_at": NOW.isoformat(),
                }
                await _upsert(conn, "returns", record)
                print(f"  [gateway-db] Upserted demo return: {r['narrative'][:60]}")
        finally:
            await conn.close()
    except Exception as e:
        print(f"  [gateway-db] Error seeding demo returns: {e}")
    print("[gateway-db] Demo returns done.")


async def seed_demo_grades() -> None:
    """Seed grades for demo returns into Grading DB."""
    print("\n[grading-db] Seeding demo grades...")
    conn = await asyncpg.connect(DB_URLS["grading"])
    try:
        for r in DEMO_RETURNS:
            grade_record = {
                "id": str(uuid.uuid4()),
                "return_id": r["id"],
                "product_id": r["product_id"],
                "grade": r["expected_grade"].value,
                "confidence": 0.85,
                "damage_summary": f"Assessed condition for {r['narrative'][:40]}",
                "defects": json.dumps([{"type": "cosmetic", "severity": "minor"}]),
                "model_metadata": json.dumps({"mode": "mock", "version": "demo-seed"}),
                "created_at": (NOW - timedelta(hours=1, minutes=50)).isoformat(),
            }
            await _upsert(conn, "grades", grade_record)
            print(f"  [grading-db] Seeded grade {r['expected_grade'].value} for return {r['id'][:8]}...")
    except Exception as e:
        print(f"  [grading-db] Error seeding grades: {e}")
    finally:
        await conn.close()
    print("[grading-db] Demo grades done.")


async def seed_demo_decisions() -> None:
    """Seed lifecycle decisions for demo returns into Lifecycle DB."""
    print("\n[lifecycle-db] Seeding demo lifecycle decisions...")
    conn = await asyncpg.connect(DB_URLS["lifecycle"])
    try:
        for r in DEMO_RETURNS:
            # Calculate value recovery based on action
            value_map = {
                LifecycleAction.RESELL: 90.0,
                LifecycleAction.REFURBISH: 65.0,
                LifecycleAction.HYPERLOCAL: 80.0,
                LifecycleAction.DONATE: 40.0,
                LifecycleAction.RECYCLE: 15.0,
            }
            decision_record = {
                "id": str(uuid.uuid4()),
                "return_id": r["id"],
                "grade_id": str(uuid.uuid4()),  # Link would be real in production
                "action": r["expected_action"].value,
                "rationale": r["narrative"],
                "value_recovery_estimate": value_map.get(r["expected_action"], 50.0),
                "sustainability_score": 85.0,
                "created_at": (NOW - timedelta(hours=1, minutes=45)).isoformat(),
            }
            await _upsert(conn, "lifecycle_decisions", decision_record)
            print(f"  [lifecycle-db] Seeded decision {r['expected_action'].value} for return {r['id'][:8]}...")
    except Exception as e:
        print(f"  [lifecycle-db] Error seeding decisions: {e}")
    finally:
        await conn.close()
    print("[lifecycle-db] Demo decisions done.")


async def seed_demo_passports() -> None:
    """Seed passports for demo returns into Passport DB."""
    print("\n[passport-db] Seeding demo passports...")
    conn = await asyncpg.connect(DB_URLS["passport"])
    try:
        for r in DEMO_RETURNS:
            passport_record = {
                "id": str(uuid.uuid4()),
                "product_id": r["product_id"],
                "return_id": r["id"],
                "current_grade": r["expected_grade"].value,
                "ownership_history": json.dumps([{"owner_id": r["user_id"], "date": NOW.isoformat()}]),
                "refurb_history": json.dumps([]),
                "sustainability_data": json.dumps({"co2_saved_kg": 2.5, "waste_diverted_kg": 1.2}),
                "status": "active",
                "created_at": (NOW - timedelta(hours=1, minutes=40)).isoformat(),
                "updated_at": NOW.isoformat(),
            }
            await _upsert(conn, "passports", passport_record)
            print(f"  [passport-db] Seeded passport for return {r['id'][:8]}...")
    except Exception as e:
        print(f"  [passport-db] Error seeding passports: {e}")
    finally:
        await conn.close()
    print("[passport-db] Demo passports done.")


async def seed_demo_matches() -> None:
    """Seed matches and match requests for demo returns into Matching DB."""
    print("\n[matching-db] Seeding demo matches...")
    conn = await asyncpg.connect(DB_URLS["matching"])
    try:
        # Create match requests and matches for HYPERLOCAL returns
        hyperlocal_returns = [r for r in DEMO_RETURNS if r["expected_action"] == LifecycleAction.HYPERLOCAL]
        
        for r in hyperlocal_returns:
            # Match request
            match_req_id = str(uuid.uuid4())
            match_req_record = {
                "id": match_req_id,
                "return_id": r["id"],
                "product_id": r["product_id"],
                "category": "furniture",
                "location": json.dumps({"lat": 13.03, "lng": 77.58, "city": "Bengaluru North"}),
                "status": "matched",
                "created_at": (NOW - timedelta(hours=1, minutes=30)).isoformat(),
            }
            await _upsert(conn, "match_requests", match_req_record)

            # Create 2 matches for this return
            buyers = [seed_min.USER_BUYER_DAN_ID, seed_min.USER_BUYER_BOB_ID]
            for idx, buyer_id in enumerate(buyers):
                match_record = {
                    "id": str(uuid.uuid4()),
                    "match_request_id": match_req_id,
                    "buyer_user_id": buyer_id,
                    "score": 0.88 - (idx * 0.1),
                    "estimated_savings": 12.50 - (idx * 2.0),
                    "distance_km": 1.5 + (idx * 0.5),
                    "created_at": (NOW - timedelta(hours=1, minutes=25 - idx * 2)).isoformat(),
                }
                await _upsert(conn, "matches", match_record)
            
            print(f"  [matching-db] Seeded match request + 2 matches for return {r['id'][:8]}...")
    except Exception as e:
        print(f"  [matching-db] Error seeding matches: {e}")
    finally:
        await conn.close()
    print("[matching-db] Demo matches done.")


async def seed_demo_listings() -> None:
    """Seed marketplace listings for demo returns into Matching DB."""
    print("\n[matching-db] Seeding demo listings...")
    conn = await asyncpg.connect(DB_URLS["matching"])
    try:
        # Create listings for RESELL and REFURBISH actions
        listable_returns = [
            r for r in DEMO_RETURNS 
            if r["expected_action"] in [LifecycleAction.RESELL, LifecycleAction.REFURBISH]
        ]
        
        for r in listable_returns:
            # Determine channel and price
            channel = ListingChannel.MARKETPLACE.value
            base_price = 150.0 if r["expected_action"] == LifecycleAction.RESELL else 80.0
            
            listing_record = {
                "id": str(uuid.uuid4()),
                "product_id": r["product_id"],
                "passport_id": str(uuid.uuid4()),  # Would link to real passport
                "return_id": r["id"],
                "price": base_price,
                "channel": channel,
                "status": ListingStatus.ACTIVE.value,
                "created_at": (NOW - timedelta(hours=1, minutes=20)).isoformat(),
                "updated_at": NOW.isoformat(),
            }
            await _upsert(conn, "listings", listing_record)
            print(f"  [matching-db] Seeded {channel} listing (${base_price}) for return {r['id'][:8]}...")
    except Exception as e:
        print(f"  [matching-db] Error seeding listings: {e}")
    finally:
        await conn.close()
    print("[matching-db] Demo listings done.")


async def seed_demo_sustainability() -> None:
    """Seed sustainability records for demo returns into Sustainability DB."""
    print("\n[sustainability-db] Seeding demo sustainability records...")
    conn = await asyncpg.connect(DB_URLS["sustainability"])
    try:
        for r in DEMO_RETURNS:
            # Calculate metrics based on action
            metrics_map = {
                LifecycleAction.RESELL: {"co2": 3.2, "waste": 2.1, "value": 120.0, "credits": 15},
                LifecycleAction.REFURBISH: {"co2": 4.5, "waste": 2.8, "value": 85.0, "credits": 20},
                LifecycleAction.HYPERLOCAL: {"co2": 5.1, "waste": 1.9, "value": 95.0, "credits": 25},
                LifecycleAction.DONATE: {"co2": 2.8, "waste": 1.5, "value": 60.0, "credits": 18},
                LifecycleAction.RECYCLE: {"co2": 1.2, "waste": 3.5, "value": 20.0, "credits": 10},
            }
            metrics = metrics_map.get(r["expected_action"], {"co2": 2.0, "waste": 1.5, "value": 50.0, "credits": 12})
            
            sust_record = {
                "id": str(uuid.uuid4()),
                "return_id": r["id"],
                "product_id": r["product_id"],
                "user_id": r["user_id"],
                "co2_avoided_kg": metrics["co2"],
                "waste_diverted_kg": metrics["waste"],
                "value_recovered": metrics["value"],
                "green_credits": metrics["credits"],
                "created_at": (NOW - timedelta(hours=1, minutes=10)).isoformat(),
            }
            await _upsert(conn, "sustainability_records", sust_record)
            print(f"  [sustainability-db] Seeded record for return {r['id'][:8]}: {metrics['co2']}kg CO₂, {metrics['credits']} credits")
    except Exception as e:
        print(f"  [sustainability-db] Error seeding sustainability: {e}")
    finally:
        await conn.close()
    print("[sustainability-db] Demo sustainability done.")


# ---------------------------------------------------------------------------
# Golden path trigger helper
# ---------------------------------------------------------------------------

async def trigger_golden_path_purchase() -> None:
    """
    Optionally trigger a PurchaseCompleted event for the golden-path return.
    
    This simulates the final step of the demo saga.
    Requires Gateway to be running.
    """
    print("\n[demo] Triggering golden-path PurchaseCompleted event...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # First, get a listing for the golden-path return
            response = await client.get(
                f"{MATCHING_URL}/listings",
                params={"return_id": seed_min.RETURN_GOLDEN_ID},
            )
            if response.status_code != 200:
                print(f"  [demo] Could not find listing for golden-path return: {response.status_code}")
                return
            
            listings = response.json().get("items", [])
            if not listings:
                print("  [demo] No listings found for golden-path return")
                return
            
            listing_id = listings[0]["id"]
            
            # Trigger purchase via Gateway (would need JWT in real scenario)
            # For now, just log what would happen
            print(f"  [demo] Would trigger POST /purchase with listing_id={listing_id[:8]}...")
            print("  [demo] In production, this completes the saga: PurchaseCompleted → SustainabilityUpdated")
    except Exception as e:
        print(f"  [demo] Error triggering golden-path purchase: {e}")
        print("  [demo] This is optional — demo will work without it")


# ---------------------------------------------------------------------------
# Manifest and summary
# ---------------------------------------------------------------------------

def print_demo_manifest() -> None:
    """Print summary of what was seeded."""
    print("\n" + "=" * 70)
    print("DEMO NARRATIVE SEED MANIFEST — Amazon Second Life AI")
    print("=" * 70)
    
    print("\n📦 DEMO RETURNS (Full Saga Coverage)")
    print("-" * 70)
    for r in DEMO_RETURNS:
        print(f"  {r['narrative'][:55]:<57}")
        print(f"    return_id: {r['id'][:8]}... | grade: {r['expected_grade'].value} | action: {r['expected_action'].value}")
    
    print("\n🎯 GOLDEN PATH (Judge Walkthrough)")
    print("-" * 70)
    print(f"  Return ID: {seed_min.RETURN_GOLDEN_ID[:8]}...")
    print(f"  Product: Zebronics Jet PRO Gaming Headphones")
    print(f"  Flow: SUBMITTED → GRADED (B) → HYPERLOCAL → MATCHED → PURCHASED → CO₂ SAVED")
    print(f"  Media Key: {GOLDEN_PATH_MEDIA_KEY}")
    
    print("\n📊 DASHBOARD DATA")
    print("-" * 70)
    total_co2 = sum(
        {"RESELL": 3.2, "REFURBISH": 4.5, "HYPERLOCAL": 5.1, "DONATE": 2.8, "RECYCLE": 1.2}
        .get(r["expected_action"].value, 2.0)
        for r in DEMO_RETURNS
    )
    total_waste = sum(
        {"RESELL": 2.1, "REFURBISH": 2.8, "HYPERLOCAL": 1.9, "DONATE": 1.5, "RECYCLE": 3.5}
        .get(r["expected_action"].value, 1.5)
        for r in DEMO_RETURNS
    )
    total_value = sum(
        {"RESELL": 120, "REFURBISH": 85, "HYPERLOCAL": 95, "DONATE": 60, "RECYCLE": 20}
        .get(r["expected_action"].value, 50)
        for r in DEMO_RETURNS
    )
    total_credits = sum(
        {"RESELL": 15, "REFURBISH": 20, "HYPERLOCAL": 25, "DONATE": 18, "RECYCLE": 10}
        .get(r["expected_action"].value, 12)
        for r in DEMO_RETURNS
    )
    
    print(f"  Total CO₂ Avoided: {total_co2:.1f} kg")
    print(f"  Total Waste Diverted: {total_waste:.1f} kg")
    print(f"  Total Value Recovered: ${total_value:.2f}")
    print(f"  Total Green Credits: {total_credits}")
    
    print("\n🔗 SERVICE ENDPOINTS")
    print("-" * 70)
    print(f"  Gateway:        {GATEWAY_URL}")
    print(f"  Sustainability: {SUSTAINABILITY_URL}/sustainability/metrics")
    print(f"  Returns:        {GATEWAY_URL}/returns")
    print(f"  Marketplace:    {GATEWAY_URL}/marketplace")
    
    print("\n✅ NEXT STEPS")
    print("-" * 70)
    print("  1. Open web app: http://localhost:3000")
    print("  2. Login as: demo.returner@slmai.dev / demo1234")
    print("  3. View Returns → See full event saga for each return")
    print("  4. Open Sustainability Dashboard → See aggregated impact metrics")
    print("  5. Browse Marketplace → See active listings")
    
    print("=" * 70 + "\n")


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

async def main(reset: bool = False, quick: bool = False) -> None:
    """
    Main seed orchestration.
    
    Args:
        reset: If True, cleans existing data before seeding
        quick: If True, skips seed_min (only adds demo narrative)
    """
    print("\n🌱 Amazon Second Life AI — Full Demo Narrative Seed")
    print("=" * 70)
    
    # Step 1: Run seed_min if not in quick mode
    if not quick:
        print("\n[Step 1/9] Running seed_min for base data...")
        try:
            await seed_min.main(reset=reset)
        except Exception as e:
            print(f"  [seed_min] Error: {e}")
            print("  Continuing with demo seed — some data may be missing")
    else:
        print("\n[Step 1/9] Skipped seed_min (quick mode)")
    
    # Step 2: Seed additional demo products
    print("\n[Step 2/9] Seeding additional demo products...")
    await seed_demo_products()
    
    # Step 3: Seed demo returns
    print("\n[Step 3/9] Seeding demo returns...")
    await seed_demo_returns()
    
    # Step 4: Seed grades
    print("\n[Step 4/9] Seeding demo grades...")
    await seed_demo_grades()
    
    # Step 5: Seed lifecycle decisions
    print("\n[Step 5/9] Seeding lifecycle decisions...")
    await seed_demo_decisions()
    
    # Step 6: Seed passports
    print("\n[Step 6/9] Seeding passports...")
    await seed_demo_passports()
    
    # Step 7: Seed matches
    print("\n[Step 7/9] Seeding matches...")
    await seed_demo_matches()
    
    # Step 8: Seed listings
    print("\n[Step 8/9] Seeding marketplace listings...")
    await seed_demo_listings()
    
    # Step 9: Seed sustainability records
    print("\n[Step 9/9] Seeding sustainability records...")
    await seed_demo_sustainability()
    
    # Optional: Trigger golden-path purchase
    # await trigger_golden_path_purchase()
    
    # Print manifest
    print_demo_manifest()
    
    print("✅ Full demo narrative seed complete!")
    print("   All services should now have rich, judge-ready demo data.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Seed full demo narrative for Amazon Second Life AI"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing seed data before re-seeding",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Skip seed_min, only add demo narrative data",
    )
    args = parser.parse_args()
    
    asyncio.run(main(reset=args.reset, quick=args.quick))
