# Chinese doc search

This is a Chinese article text search Engine developed using FastHTML and ElasticSearch

## Loading data to ElasticSearch form excel file

If you have enough memory to load the entire excel file at once, then it is strict forward by using
```python
   for i, row in df.iterrows():
      ... # reference to create_fake_data.py
```

Otherwise, please either:

1. Save the file as csv and refer to [How do I read a large csv file with pandas?](https://stackoverflow.com/questions/25962114/how-do-i-read-a-large-csv-file-with-pandas)
2. Know the number of rows in your file in advance and refer to [read a full excel file chunk by chunk using pandas](https://stackoverflow.com/questions/70681153/read-a-full-excel-file-chunk-by-chunk-using-pandas)

## How to run

1. Setup ElasticSearch in docker and start the container, My version is 8.15.0. [Reference](https://www.elastic.co/search-labs/tutorials/install-elasticsearch)
2. create a `.env` file and define these variables in it
   -  `DEBUG`
   -  `ELASTICSEARCH_PORT`
   -  `ELASTICSEARCH_INDEX`
3. `pip install -r requirements.txt`
4. `python src/main.py`

## Previews

The tests are done on 10,000 entries, each entries' full_text section is 10,000 characters long

Please click on the links to watch the preview videos

### [Basic query](https://www.awesomescreenshot.com/video/35106527?key=6a3a64a98bb46dd852c4f2df7fb58aff)

### [Complex query](https://www.awesomescreenshot.com/video/35106750?key=bda05fd7d0c42b6a7eff989d68269240)

### [Form error handling](https://www.awesomescreenshot.com/video/35106784?key=d495981c2384b162634235b4440b83a3)
