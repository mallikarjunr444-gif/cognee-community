"""Example demonstrating how to sync Twilio messages into Cognee memory.

Prerequisites:
  export TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  export TWILIO_AUTH_TOKEN="your_auth_token"
  pip install cognee-community-connector-twilio "dlt[sqlalchemy]"
"""

import asyncio
import os

import cognee

from cognee_community_connector_twilio import twilio_source

DATASET_NAME = "twilio_communication_memory"


async def main():
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    if not account_sid or not auth_token:
        print("Please set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN to run this example.")
        return

    # Ingest messages
    source = twilio_source(account_sid=account_sid, auth_token=auth_token)

    print("Syncing Twilio communications into Cognee memory ...")
    await cognee.remember(source, dataset_name=DATASET_NAME, self_improvement=False)

    print("\nQuerying knowledge graph ...")
    answer = await cognee.search(
        query_text="What alerts or notifications were dispatched in the past 24 hours?",
        query_type=cognee.SearchType.GRAPH_COMPLETION,
        datasets=[DATASET_NAME],
    )
    print("\nSearch result:\n", answer)


if __name__ == "__main__":
    asyncio.run(main())
