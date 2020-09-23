# Wikipedia-Search-Engine
A simple standalone search engine tool to search for relevant information in a locally downloaded Wikipedia corpus. Given a Wikipedia dump in XML format, this creates a local index of the data and search for any queried information in 1-4 seconds!

## Requirements
- Python 3
- [PyStemmer](https://pypi.org/project/PyStemmer/)
- xml.sax Parser - Included in the default Python package (see [here](https://docs.python.org/3/library/xml.sax.html#module-xml.sax))
- [nltk](https://pypi.org/project/nltk/)
- Download nltk stopwords via typing `python -m nltk.downloader stopwords` in the terminal.

## Instructions for Running the code
1. Clone this repository and `cd` into the directory.
2. The first step is to **download** a Wikipedia dump file ([this link](https://dumps.wikimedia.org/enwiki/latest/) contains the **latest Wikipedia dump**). A sample zipped dump file present in the repository can also be used for the purpose. Uncompress the dump file(s) if it was downloaded in compressed format and place it inside a folder named `uncompressed-dump` in the cloned directory.
3. To create inverted index run the following command (in the cloned directory): 
    ```
    python3 wiki_indexer.py
    ```
    This creates a folder named `data/` containing the index created.

4. The query must be written in a plain text file, and the ouput of query is also written into a file. Each query result contains the name of the corresponding Wikipedia page title. To run a query, run the following command inside the cloned directory:
    ```
    python3 wiki_query.py <path_to_file_containing_query> <path_to_query_output_file>
    ```

## Query Format
- All the queries are written in a plain text file.
- Each query should be present in a new line. The file ends after the last query. Query has a general format `<num_results>, "query"`, where num_results is an integer denoting the number of desired results for the provided query. 
- Two types of queries can be handled by the search engine:
  - Simple Query: Here we mention the phrase or keyword or sentence form query. eg. "3, Sachin tendulkar", "2, Cricket World Cup 2019", "10, India" etc.
  - Field Query: Wikipedia articles have several categories in the page and the user can specify to search in only those fields. The search engine handles the following categories: Title(t), Body(b), Links(l), References(r), Infobox(i), Category(c). Example of field queries 1) "3, t:World Cup i:2019 c:Cricket", 2) "2, t:the two towers i:1954" etc.


## How the search engine works?
- First the `indexer` creates an inverted index of the entire dump provided to it. It processes the whole data in small chunks, so dump of any size (even greater than the RAM size) can be processed. To do so, **Block-sort** based indexing has been used, which efficiently sorts the inverted index created (of any size) without the limitation of RAM size, so that the created index can be used by the `query` module for fast query processing.
  - Various intermediate steps like parsing, tokenization, stemming, stop words removal etc. have been done to create a quality index.
- **Tf-Idf** scoring mechanism has been used primarily along with some heuristic to rank the documents in the order of their relevance. So when a user types in a query, and they specify the number of results along with that, we can display the most relevant results to them. Even for the cases when a document that exactly matches the query does not exist, the ranking mechanism ensures that we still have the most relevant results that are available, ready for the user.

## Additional Remarks
- As the number of documents in the corpus increase, the quality of the search results will also enhance. Hence increasing the size of the dump, will create a better index, and hence produce results that are more relevant to the user.
- This approach is just built for Wikipedia articles, and it defines the core search part of any search engine. It can be combined with the web crawler part to move in the direction of building a complete search engine.
