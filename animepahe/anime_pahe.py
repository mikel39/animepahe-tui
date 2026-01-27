import re

from bs4 import BeautifulSoup

from .client import clt

#
from .utils import generate_cookie, get_source

POSSIBLE_HOSTS = ['animepahe.si', 'animepahe.com', 'animepahe.org']


class AnimePahe:
    async def get_m3u8_url(self, url: str) -> str:
        """expects and absolute url of the src of the episode and returns the m3u8 url"""
        res = await clt.get(url)
        html = BeautifulSoup(res.text, 'html.parser')
        html = html.find('script', src=False)
        script = re.sub(
            r'.*?eval.*?eval.*?return p.*?\((.*?)\)\)\s.*', r'\1', str(html)
        )
        p = h.group() if (h := re.search(r'.*?;\'', script)) else None
        script = script.replace(p or '', '')
        a, c = (
            match.groups()
            if (match := re.search(r'(\d+),(\d+)', script))
            else (None, None)
        )

        k = (
            match.group(1)
            if (match := re.search(r'.*?\'(.*?)..split.*', script))
            else None
        )

        if not p or not a or not c or not k:
            raise Exception('One of the arguments is None, update the regex.')

        source = get_source(p, int(a), int(c), k.split('|'))
        source = (
            match.group(1)
            if (match := re.search(r'.*?source.*?(http.*?m3u8)', source))
            else None
        )

        if not source:
            raise Exception(
                'Got None while getting the m3u8 url, update regex or algo.'
            )

        return source

    async def search_serie(self, query: str) -> list:
        """expects a query and retuns an array of possible matches"""
        res = await clt.get('/api', params={'m': 'search', 'q': query})
        result: dict = res.json()
        data = result.get('data', [])
        return data

    async def get_episodes_by_anime(self, anime_session: str) -> list:
        """expext the anime session code and retuns a list of episodes asc"""
        res = await clt.get(
            '/api',
            params={
                'm': 'release',
                'id': anime_session,
                'sort': 'episode_asc',
                'page': 1,
            },
        )

        res = res.json()
        return res['data']

    async def get_latest_releases(self, page: int):
        res = await clt.get('/api', params={'m': 'airing', 'page': page})
        return res.json()

    async def get_episode_options(
        self, anime_session: str, episode_session: str
    ) -> dict:
        """expects an url: /anime_session/ep_session of the episode and retuns all of its options"""
        res = await clt.get(f'/play/{anime_session}/{episode_session}')
        html = BeautifulSoup(res.text, 'html.parser')
        title = match.text if (match := html.find('title')) else ''
        title = (
            match.group(1).strip() if (match := re.search(r'(.*?)::', title)) else None
        )
        html = html.find(id='resolutionMenu')
        html = html.find_all('button') if html else None

        if not title or not html:
            raise Exception('Could not get episodes source options. update parsing.')

        options = {'title': title, 'data': []}

        for v in html:
            src = v.get('data-src')
            audio = v.get('data-audio')
            resolution = v.get('data-resolution')
            options['data'].append(dict(src=src, audio=audio, resolution=resolution))

        return options

    async def initialize(self) -> None:
        for host in POSSIBLE_HOSTS:
            hst = 'https://' + host
            res = await clt.get(hst)
            if res.status_code in (200, 403):
                clt.base_url = hst
                if res.status_code == 403:
                    break
                else:
                    return
        else:
            raise Exception('Not avaliable hosts found, need to update hosts.')

        clt.cookies.update(generate_cookie())
