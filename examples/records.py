"""
Records SDK Example
Demonstrates schema definition, CRUD, query, and semantic search
"""

import os
from mnexium import Mnexium

def main():
    mnx_key = os.environ.get("MNX_KEY")
    if not mnx_key:
        print("⏭️  Skipping: MNX_KEY not set")
        return

    mnx = Mnexium(
        api_key=mnx_key,
        base_url=os.environ.get("MNX_BASE_URL", "https://mnexium.com/api/v1"),
    )

    # 1. Define schemas
    print("1. Define schemas")
    mnx.records.define_schema(
        "account",
        {
            "name": {"type": "string", "required": True},
            "industry": {"type": "string"},
            "arr": {"type": "number"},
            "status": {"type": "string"},
        },
        display_name="Account",
        description="Business accounts",
    )

    mnx.records.define_schema(
        "deal",
        {
            "title": {"type": "string", "required": True},
            "value": {"type": "number"},
            "stage": {"type": "string"},
            "account_id": {"type": "ref:account"},
        },
        display_name="Deal",
        description="Sales deals",
    )

    # 2. Insert records
    print("2. Insert records")
    account = mnx.records.insert("account", {
        "name": "TechCorp",
        "industry": "Technology",
        "arr": 5000000,
        "status": "active",
    })
    print(f"   Account: {account['record_id']}")

    deal = mnx.records.insert("deal", {
        "title": "TechCorp Enterprise",
        "value": 250000,
        "stage": "proposal",
        "account_id": account["record_id"],
    })
    print(f"   Deal: {deal['record_id']}")

    # 3. Get a record
    print("3. Get record")
    fetched = mnx.records.get("deal", deal["record_id"])
    print(f"   {fetched['data']['title']}: {fetched['data']['stage']}")

    # 4. Update a record
    print("4. Update record")
    updated = mnx.records.update("deal", deal["record_id"], {
        "stage": "closed_won",
        "value": 300000,
    })
    print(f"   Stage: {updated['data']['stage']}, Value: {updated['data']['value']}")

    # 5. Query records
    print("5. Query records")
    closed_deals = mnx.records.query("deal", where={"stage": "closed_won"}, order_by="-value", limit=10)
    print(f"   Found {len(closed_deals)} closed deals")

    # 6. Semantic search
    print("6. Semantic search")
    results = mnx.records.search("deal", "enterprise license")
    print(f"   Found {len(results)} results")
    for r in results:
        print(f"   - {r['data']['title']} (similarity: {r.get('similarity', 0):.3f})")

    # 7. List schemas
    print("7. List schemas")
    schemas = mnx.records.list_schemas()
    print(f"   {len(schemas)} schemas: {', '.join(s['type_name'] for s in schemas)}")

    # 8. Delete a record
    print("8. Delete record")
    mnx.records.delete("deal", deal["record_id"])
    deleted = mnx.records.get("deal", deal["record_id"])
    print(f"   Deleted: {'yes' if deleted is None else 'no'}")

    print("\nDone!")


if __name__ == "__main__":
    main()
