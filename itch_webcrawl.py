import argparse
import csv
import logging
import re
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


def process_game_cell_links(links):
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
        try:
            tag_list = [otag.contents[0].lower() for otag in soup.find_all('a', href=re.compile(r'tag'))]
        except (TypeError, AttributeError):
            tag_list = []
        games.append(
            {
                'index': i,
                'title': link.get('title'),
                'author': link.get('author'),
                'rating_count': rating_count,
                'rating': rating,
                'desc': link.get('desc'),
                'link': link.get('link'),
                'tags': tag_list,
            }
        )
        time.sleep(1)
    return games


def unpack_tags(games):
    settags = {tag for game in games for tag in game.get('tags', [])}
    for game in games:
        #  game.update(dtags)
        for tag in game.get('tags'):
            game[tag] = 'x'
        game.pop('tags', None)
    lst = list(settags)
    lst.sort()
    with open('tags', 'w') as tagfile:
        for tag in lst:
            tagfile.writelines(f'{tag}\n')
    return games, lst


def export_csv(games_content, filename='games.csv'):
    filepath = Path(filename)
    if filepath.is_file():
        filepath.unlink()
    headers_o = list(games_content[0].keys())
    upcontent, headers_t = unpack_tags(games_content)
    headers_o.remove('tags')
    headers = headers_o + headers_t
    with open(filename, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, delimiter="←", fieldnames=headers)
        writer.writeheader()
        writer.writerows(upcontent)


def parse_game_cells(gamecells):
    links = []
    for i, cell in enumerate(gamecells):
        title = cell.find('a', class_='title')
        title = title.contents[0] if title else ''
        author = cell.find('a', class_='user_link')
        author = author.contents[0] if author else ''
        desc = cell.find('div', class_='short_text')
        desc = desc.contents[0] if desc else ''
        link = cell.a.attrs['href']
        links.append(
            {
                'index': i,
                'title': title,
                'author': author,
                'desc': desc,
                'link': link,
            }
        )
    return links


def process_content(content):
    soup = BeautifulSoup(content, 'html.parser')
    gamecells = soup.find_all('div', class_='game_cell')
    links = parse_game_cells(gamecells)
    logger.info(f'Found {len(links)} links')
    games = process_game_cell_links(links)
    return games


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('data_source', metavar='DATASOURCE', type=str, help='Data source (URL or HTML file)')
    parser.add_argument(
        'export_csv', metavar='CSVNAME', nargs='?', type=str, help='Result CSV file', default='games.csv'
    )
    known_args, other_args = parser.parse_known_args()

    argsource = known_args.data_source
    csvfile = known_args.export_csv

    content = get_source(argsource)

    games = process_content(content)

    export_csv(games, filename=csvfile)
