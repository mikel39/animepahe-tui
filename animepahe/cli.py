import asyncio
import gc
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

import m3u8
from Cryptodome.Cipher import AES
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.prompt import Prompt
from rich.style import Style

from animepahe.theme import Mocha

from .anime_pahe import AnimePahe
from .client import USER_AGENT, clt
from .rich_menu import RichMenu

console = Console()

ani = AnimePahe()


def select_best_resolution_possible(data: list):
    possibles = [option for option in data if option['audio'] == 'jpn']
    possibles.sort(key=lambda x: int(x['resolution']), reverse=True)
    best = possibles[0]
    return best['src']


async def download_anime(anime_session: str, title: str):
    episodes = await ani.get_episodes_by_anime(anime_session)

    path = Path(title)

    if not path.exists():
        path.mkdir()

    for episode in episodes:
        res = await ani.get_episode_options(anime_session, episode['session'])
        name = res['title']
        resolution = select_best_resolution_possible(res['data'])
        file_name = path / f'{name}.mp4'

        m3u8 = await ani.get_m3u8_url(resolution)
        url = urlparse(resolution)
        referer = f'{url.scheme}://{url.hostname}'
        await download_video(m3u8, referer, file_name)


async def show_episodes(anime_session: str, title: str):
    episodes = await ani.get_episodes_by_anime(anime_session)
    options = {
        'rows': [],
        'columns': ['Episode', 'Duration'],
        'config': [('b', 'back')],
    }

    for episode in episodes:
        options['rows'].append((episode['episode'], episode['duration']))

    menu = RichMenu(options, title)
    while True:
        index = menu.run()
        console.clear()

        if index == 'back':
            return

        episode = episodes[index]
        await show_episode((anime_session, episode['session']))


async def search_anime():
    query = Prompt.ask(f'[{Mocha.green}]Enter your query')
    console.clear()

    result: list = await ani.search_serie(query)
    options = {
        'columns': ['Title', 'Episodes', 'Score'],
        'rows': [],
        'config': [('b', 'back')],
    }

    for anime in result:
        options['rows'].append((anime['title'], anime['episodes'], anime['score']))

    menu = RichMenu(options)
    while True:
        index = menu.run()
        console.clear()

        if index == 'back':
            return

        title = result[index]['title']
        anime_session = result[index]['session']

        menu1 = RichMenu({'rows': ['See episodes', 'Download']})
        res = menu1.run()
        console.clear()

        match res:
            case 0:
                await show_episodes(anime_session, title)
            case 1:
                await download_anime(anime_session, title)


async def download_video(source: str, referer: str, path: Path):
    """expcects absoulute url of m3u8 file"""

    headers = {'origin': referer, 'referer': referer}
    res = await clt.get(source, headers=headers)
    parsed = m3u8.loads(res.text)
    key = await clt.get(parsed.keys[0].absolute_uri, headers=headers)
    key = key.content

    bar = BarColumn(
        None,
        style=Style(color=Mocha.yellow),
        complete_style=Style(color=Mocha.sky),
        finished_style=Style(color=Mocha.green),
    )

    with Progress(
        SpinnerColumn(),
        TextColumn(f'[{Mocha.sky}]{path}'),
        bar,
        TaskProgressColumn(),
        TimeElapsedColumn(),
        expand=True,
    ) as progress:
        total = sum([float(i.duration or 0) for i in parsed.segments])
        task = progress.add_task('dowload', total=total)
        f = open(f'{path}', 'wb')
        async_tasks = []
        parallel_downloads = 4

        async def helper(url, iv):
            res = await clt.get(url, headers=headers)
            return res, iv

        for i, segment in enumerate(parsed.segments):
            url = segment.absolute_uri
            iv = (i).to_bytes(16, byteorder='big')
            async_tasks.append(asyncio.create_task(helper(url, iv)))

            if (
                len(async_tasks) >= parallel_downloads
                or (len(parsed.segments) - 1) == i
            ):
                done = await asyncio.gather(*async_tasks)

                for dn, iv in done:
                    cipher = AES.new(key, AES.MODE_CBC, iv)
                    data = cipher.decrypt(dn.content)
                    f.write(data)
                    progress.update(task, advance=(segment.duration or 0))

                async_tasks.clear()
                gc.collect()

        f.close()
    console.clear()


async def watch_video(source: str, referer: str):
    """expects an absolute url of m3u8 file"""
    try:
        subprocess.Popen(
            [
                'mpv',
                source,
                f'--http-header-fields=Referer:{referer},User-Agent:{USER_AGENT}',
            ],
            stdout=subprocess.DEVNULL,
        )

    except FileNotFoundError:
        console.print(f'[{Mocha.red}]Mpv is propably not installed.')
        sys.exit()


async def show_episode(episode: tuple, path: Path = Path('.')):
    res = await ani.get_episode_options(*episode)

    options = {
        'rows': [],
        'columns': ['Audio', 'Resolution'],
    }

    for data in res['data']:
        options['rows'].append((data['audio'], data['resolution']))

    menu = RichMenu(options, res['title'])
    index = menu.run()
    console.clear()

    url = res['data'][index]['src']
    m3u8 = await ani.get_m3u8_url(url)
    url = urlparse(url)
    referer = f'{url.scheme}://{url.hostname}'
    menu = RichMenu({'rows': ['Watch', 'Download']})
    result = menu.run()
    console.clear()

    name = path / f'{res["title"]}.mp4'

    match result:
        case 0:
            await watch_video(m3u8, referer)
        case 1:
            await download_video(m3u8, referer, name)


async def show_recent_episodes():
    page = 1

    while True:
        result = await ani.get_latest_releases(page)
        next_page = result['next_page_url']
        prev_page = result['prev_page_url']
        data = result['data']

        options = []
        ui_options = {
            'columns': ('Title', 'Episode'),
            'rows': [],
            'config': [('n', 'next'), ('p', 'prev'), ('b', 'back')],
        }

        for res in data:
            title = res['anime_title']
            episode = res['episode']
            anime_session = res['anime_session']
            episode_session = res['session']
            ui_options['rows'].append((title, episode))
            options.append((anime_session, episode_session))

        menu = RichMenu(ui_options)
        result = menu.run()
        console.clear()

        match result:
            case 'next' if next_page:
                page += 1
            case 'prev' if prev_page:
                page -= 1
            case 'back':
                return
            case index:
                await show_episode(options[index])


async def main():
    await ani.initialize()
    options = {'rows': ['Search an anime.', 'See recent episode releases.']}
    menu = RichMenu(options)

    while True:
        result = menu.run()

        console.clear()

        match result:
            case 0:
                await search_anime()
            case 1:
                await show_recent_episodes()


if __name__ == '__main__':
    asyncio.run(main())
