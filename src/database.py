import os
from elasticsearch import Elasticsearch


ELASTICSEARCH_PORT = os.environ["ELASTICSEARCH_PORT"]

def get_elasticsearch_connection(port: str):

    es = Elasticsearch(f"http://localhost:{port}")
    try:
        client_info = es.info()
        print("Connected to Elasticsearch")
    except ConnectionError as docker_not_spined_up:
        print(f"unable to connect to elasticsearch, please check if your docker container is running as port {port}")
        exit("Unable to connect to elasticsearch")
    return es

es = get_elasticsearch_connection(ELASTICSEARCH_PORT)
