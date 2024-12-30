"""This script creates fake chinese article data using faker for the app. Loaded into elastic search, text fields will have simplified chinese version for easier searching."""
import argparse
from pprint import pp
from elasticsearch import Elasticsearch, ConnectionError
from faker import Faker
from tqdm import tqdm
import opencc

FAKE_INDEX_NAME = 'fake_chinese_articles_collection_data'
fake = Faker(["zh_TW", "zh_CN"])
text_converter = opencc.OpenCC("t2s.json")

INDEX_MAPPING = {
    "properties": {
        "id": {"type": "keyword"},
        "publisher": {
            "type": "text",
        },
        "publish_location": {
            "type": "text",
        },
        "publish_date": {"type": "date"},
        "author_name": {
            "type": "text",
        },
        "title": {
            "type": "text",
        },
        "full_text": {
            "type": "text",
        },
        "publisher_simplified": {
            "type": "text",
        },
        "publish_location_simplified": {
            "type": "text",
        },
        "author_name_simplified": {
            "type": "text",
        },
        "title_simplified": {
            "type": "text",
        },
        "full_text_simplified": {
            "type": "text",
        },
    }
}

def connect_elasticsearch(port: int):
    """Connect to local hosted elasticsearch"""
    es = Elasticsearch(f"http://localhost:{port}")
    try:
        client_info = es.info()
        print("Connected to Elasticsearch")
        pp(client_info.body)
    except ConnectionError as docker_not_spined_up:
        print(f"unable to connect to elasticsearch, please check if your docker container is running as port {port}")
        return None
    return es

def create_fake_data_index(es: Elasticsearch):
    """Create fake data index in elasticsearch"""
    if es.indices.exists(index=FAKE_INDEX_NAME).body:
        confirm_delete = input(f"Index {FAKE_INDEX_NAME} already exists, do you want to delete and rewrite it? (y/n): ")
        if confirm_delete.lower() != 'y':
            exit("Index not deleted")
    es.indices.delete(index=FAKE_INDEX_NAME, ignore_unavailable=True)
    es.indices.create(
        index=FAKE_INDEX_NAME,
        settings={
            "index": {
                "number_of_shards": 3,  # how many pieces the data is split into
                "number_of_replicas": 2  # how many copies of the data
            }
        },
    )
    es.indices.put_mapping(index=FAKE_INDEX_NAME, body=INDEX_MAPPING)

def create_fake_article_entry(es: Elasticsearch, full_text_len: int):
    """Create fake article entry in elasticsearch with the following entries:
    - id
    - publisher
    - publish location
    - publish date
    - author name
    - title
    - full text
    """
    fake_data = {
        "id": fake.uuid4(),
        "publisher": fake.company(),
        "publish_location": fake.city(),
        "publish_date": fake.date(),
        "author_name": fake.name(),
        "title": fake.sentence(),
        "full_text": fake.text(full_text_len),
    }
    for field_name in ["publisher", "publish_location", "author_name", "title", "full_text"]:
        fake_data[f"{field_name}_simplified"] = text_converter.convert(fake_data[field_name])
    es.index(index=FAKE_INDEX_NAME, body=fake_data)

def create_fake_data(es: Elasticsearch, num_entries: int, full_text_len: int):
    """Create fake data in elasticsearch"""
    for i in tqdm(range(num_entries), desc="Creating fake article data"):
        create_fake_article_entry(es, full_text_len)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create fake data in elasticsearch')
    parser.add_argument('--port', type=int, default=9200)
    parser.add_argument('--num_entries', type=int, default=1000)
    parser.add_argument('--full_text_len', type=int, default=1000)
    args = parser.parse_args()
    es = connect_elasticsearch(args.port)
    if es is None:
        exit()
    create_fake_data_index(es)
    create_fake_data(es, args.num_entries, args.full_text_len)
    print("Done!")
