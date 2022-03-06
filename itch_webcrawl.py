import argparse
import csv
import logging
import requests
import time

from bs4 import BeautifulSoup
from pathlib import Path

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s')
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)
# Remove requests logging
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_source(source):
    try:
        r = requests.get(source)
        content = r.content
    except requests.exceptions.MissingSchema:
        filepath = Path(source)
        if not filepath.is_file():
            return False
        content = openfile(filepath)
    return content


def openfile(filepath):
    with open(str(filepath), 'r') as htmlsource:
        content = htmlsource.read()
    return content


def process_links(links):
    games = []
    llinks = len(links)
    for i, link in enumerate(links):
        logger.info(f'{i+1} / {llinks} - {link.get("title")}')
        link_content = get_source(link.get('link'))
        soup = BeautifulSoup(link_content, 'html.parser')
        try:
            rating_count_soup = soup.find('span', class_='rating_count')
            rating_count = int(rating_count_soup.attrs['content'])
        except AttributeError:
            rating_count = ''
        try:
            rating_soup = soup.find('div', class_='aggregate_rating')
            rating = float(rating_soup.attrs['title'])
        except AttributeError:
            rating = ''
        games.append(
            {
                'index': i,
                'title': link.get('title'),
                'author': link.get('author'),
                'rating_count': rating_count,
                'rating': rating,
                'desc': link.get('desc'),
                'link': link.get('link'),
            }
        )
        time.sleep(1)
    return games


def export_csv(content, filename='games.csv'):
    headers = list(content[0].keys())
    with open(filename, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, delimiter="←", fieldnames=headers)
        writer.writeheader()
        writer.writerows(content)


def parse_game_cells(gamecells):
    links = []
    for cell in gamecells:
        title = cell.find('a', class_='title')
        title = title.contents[0] if title else ''
        author = cell.find('a', class_='user_link')
        author = author.contents[0]
        desc = cell.find('div', class_='short_text')
        desc = desc.contents[0] if desc else ''
        link = cell.a.attrs['href']
        links.append(
            {
                'title': title,
                'author': author,
                'desc': desc,
                'link': link,
            }
        )
    return links


def process(**kwargs):
    content = kwargs.get('content')
    if not content:
        logger.error('No content detected')
        return None

    soup = BeautifulSoup(content, 'html.parser')
    gamecells = soup.find_all('div', class_='game_cell')
    links = parse_game_cells(gamecells)
    logger.info(f'Found {len(links)} links')
    games = process_links(links)
    return games


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('data_source', metavar='DATASOURCE', type=str, help='Data source')
    known_args, other_args = parser.parse_known_args()

    argsource = known_args.data_source

    content = get_source(argsource)

    dargs = {'content': content}

    games = process(**dargs)

    export_csv(games)
