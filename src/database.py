import os
from elasticsearch import Elasticsearch


ELASTICSEARCH_URL = os.environ["ELASTICSEARCH_URL"]

def get_elasticsearch_connection(url: str):

    es = Elasticsearch(f"{url}")
    try:
        client_info = es.info()
        print("Connected to Elasticsearch")
    except ConnectionError as docker_not_spined_up:
        print(f"unable to connect to elasticsearch, please check if your docker container is running as port {port}")
        exit("Unable to connect to elasticsearch")
    return es

es = get_elasticsearch_connection(ELASTICSEARCH_URL)
