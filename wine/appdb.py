#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# AUTHOR:
# Christian Dannie Storgaard <cybolic@gmail.com>

import re
import urllib2, urllib
from BeautifulSoup import BeautifulSoup

APPDB_CACHE = {}

class Request(urllib2.Request):
    # To fix this bug: http://bugs.python.org/issue8280
    def get_selector(self):
        return self.__r_host.split('#')[0]

def get_version_lookup_url(app, gotofirst=True):
    url = 'http://www.google.com/search'
    data = {
        'q': '"{0}" inurl:sClass=version site:http://appdb.winehq.org'.format(
            app
        ),
    }
    if gotofirst:
        data['btnI'] = ''
    url_values = urllib.urlencode(data)
    return '{0}?{1}'.format(url, url_values)

def get_application_lookup_url(app, gotofirst=True):
    url = 'http://www.winehq.org/search'
    data = {
        #'q': '"{0}" inurl:sClass=application site:http://appdb.winehq.org'.format(
        #    app
        #)
        'cx': 'partner-pub-0971840239976722:w9sqbcsxtyf',
        'cof': 'FORID:10',
        'ie': 'UTF-8',
        'q': '"{0}" inurl:sClass=application'.format(app),
        'siteurl': 'appdb.winehq.org'
    }
    if gotofirst:
        data['btnI'] = ''
    url_values = urllib.urlencode(data)
    return '{0}?{1}'.format(url, url_values)

def _get_appdb_page(app):
    if app in APPDB_CACHE:
        return APPDB_CACHE[app]
    else:
        url = 'http://www.google.com/search'
        data = {
            'q': '"{0}" inurl:sClass=application site:http://appdb.winehq.org'.format(app),
            'btnI': ''
        }
        url_values = urllib.urlencode(data)

        request = Request('{0}?{1}'.format(url, url_values), None, {
            'User-Agent': 'Vineyard Web Reader',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Referer': 'http://www.google.com/ig'
        })
        content = urllib2.urlopen(request).read()
        APPDB_CACHE[app] = content
        return content

def get_application_info(app):
    page = _get_appdb_page(app)
    soup = BeautifulSoup(page)

    header = soup.find('td', 'white')
    sections = [ tag.text for tag in header.findAll('a') ]
    name = str(header).split('</a>')[-1].split('<')[0].replace('&gt;','').strip()

    versions = {}
    for tr in soup.findAll('tr', onmouseover=True):
        if 'OBSOLETE - ' not in str(tr):
            (version, description, rating,
             wine_version, test_results, comments) = tr.findChildren('td')

            link = version.find('a').attrs[0][1]
            version = str(version.text)
            description = description.text
            rating = str(rating.text)
            wine_version = str(wine_version.text)
            test_results = test_results.text
            comments = comments.text

            versions[version] = Version({
                    'description': description,
                    'rating': rating,
                    'wine_version': wine_version,
                    'test_results': test_results,
                    'comments': comments,
                    'url': link
            })

    return {'sections':sections, 'name':name, 'versions':versions}

def get_application_link_and_name(app):
    appdb_page = _get_appdb_page(app)
    match = re.search('<a .*?href=[\'"]([^\'"\s]*?objectManager\.php\?[^\'"\s]*?sClass=application&[^\'"\s]*?iId=[^\'"\s]*?)[\'"] ?>(.*?)<', appdb_page)
    if match:
        url, name = match.groups()
        if not url.lower().startswith('http'):
            url = 'http://http://appdb.winehq.org/%s' % url
        return url, name

def get_version_info_from_url(url):
    if url in APPDB_CACHE:
        page = APPDB_CACHE[url]
    else:
        page = urllib2.urlopen(url).read()
        APPDB_CACHE[url] = page
    soup = BeautifulSoup(page)

    header = soup.find('td', 'white')
    sections = [ tag.text for tag in header.findAll('a') ]
    name = sections[-1]
    sections = sections[:-1]
    version = str(header).split('</a>')[-1].split('<')[0].replace('&gt;','').strip()

    infobox = soup.find('td', 'color4')
    infobox_start = BeautifulSoup(str(infobox).split('screenshot')[0])

    info = {'sections': sections}
    for tr in infobox_start.findAll('tr'):
        tds = tr.findAll('td')
        if len(tds) == 2:
            info[ tds[0].text.lower() ] = tds[1].text
    # The following is getting a bit too much, since every program has several
    # versions than in return each have several test results, the user really
    # should use appdb.winehq.org directly instead.
    """
    results = dict([
        (div.find('div', 'title_class').text, div.find('div', 'info_contents'))
        for div
        in soup.findAll('td', 'topMenu')[1].findAll('div', 'info_container')
    ])"""
    return info


class Version(dict):
    def retrieve(self):
        if 'url' in self:
            return get_version_info_from_url(self['url'])