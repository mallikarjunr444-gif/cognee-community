from cognee_community_connector_hackernews import HackerNewsConnector


def main():
    connector = HackerNewsConnector()
    print("--- Top Hacker News Stories ---")
    for story in connector.get_top_stories(limit=5):
        print(f"[{story['score']} pts] {story['title']} (by {story['by']})")


if __name__ == "__main__":
    main()
