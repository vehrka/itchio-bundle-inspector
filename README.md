# itchio-bundle-inspector

* **version:** 0.2
* **date**: 2022-03-08

Generates a csv with the basic information for the games in a bundle

```bash
usage: itch_webcrawl.py [-h] DATASOURCE [CSVNAME]

positional arguments:
  DATASOURCE  Data source (URL or HTML file)
  CSVNAME     Result CSV file

optional arguments:
  -h, --help  show this help message and exit  
```

As a **DATASOURCE** you can pass a URL or a previously downloaded *HTML* webpage.

It will also generate a `tag` file with all the tags in the bundle
