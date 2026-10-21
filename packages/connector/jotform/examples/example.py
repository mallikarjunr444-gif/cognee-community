"""Example demonstrating Jotform connector usage with Cognee."""

import asyncio
import os

from cognee_community_connector_jotform import jotform


async def main():
    api_key = os.environ.get("JOTFORM_API_KEY", "demo_api_key")
    print(f"Connecting to Jotform with API key: {api_key[:4]}...")

    # Fetch and display documents from Jotform connector
    resource = jotform(api_key=api_key, limit_per_form=10)
    count = 0
    for doc in resource:
        count += 1
        print(f"[{count}] Ingested doc: {doc['name']}")
        print(f"Metadata: {doc['external_metadata']}")
        print("---")


if __name__ == "__main__":
    asyncio.run(main())
