# -*- coding: utf-8 -*-
import sys
import os
import discogs_client
import re
import urllib
import xml.dom.minidom
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

SAVE_PATH = os.getenv('SAVE_PATH')
USER_TOKEN = os.getenv('USER_TOKEN')
FILE_NAME_TEMPLATE = os.getenv('FILE_NAME_TEMPLATE')

d = discogs_client.Client('xml-for-audacity/0.1', user_token=USER_TOKEN)


def trim_artist_name(name):
    return re.sub(' \(\d\)$', '', name)


def audacity_tag(name, val):
    disc_info_xml = xml.dom.minidom.Document()
    subnode = disc_info_xml.createElement('tag')
    subnode_attr = disc_info_xml.createAttribute('name')
    subnode_attr.value = name
    subnode.setAttributeNode(subnode_attr)
    subnode_attr = disc_info_xml.createAttribute('value')
    subnode_attr.value = str(val)
    subnode.setAttributeNode(subnode_attr)
    return subnode


def discogs_info_toxml(release):
    info = {}
    disc_info_dic = {}
    disc_info_dic['YEAR'] = release.year
    disc_info_dic['GENRE'] = release.genres[0]
    # remove " (*)" of "artist name (*)"
    disc_info_dic['ARTIST'] = trim_artist_name(release.artists[0].name)
    disc_info_dic['ALBUM'] = release.title

    for i, t in enumerate(release.tracklist):
        disc_info_xml = xml.dom.minidom.Document()
        tags = disc_info_xml.createElement('tags')
        disc_info_xml.appendChild(tags)
        tags.appendChild(audacity_tag('TITLE', t.title))
        tags.appendChild(audacity_tag('TRACKNUMBER', i + 1))
        for name, val in disc_info_dic.items():
            tags.appendChild(audacity_tag(name, val))

        # print(disc_info_xml.toprettyxml())
        file_name_dict = {
                "artist": trim_artist_name(release.artists[0].name),
                "album": release.title,
                "number": i + 1,
                "song": t.title}
        try:
            file_name = FILE_NAME_TEMPLATE.format(**file_name_dict)
        except KeyError:
            file_name = "{number:02} {song}.xml".format(
                    **file_name_dict)
        file_name = re.sub('/', '_', file_name)
        print(file_name)
        info[file_name] = disc_info_xml
    return info


def download_album_artwork(release, save_path):
    image_url = release.images[0]['uri']
    try:
        image_name = '%s.jpg' % release.title
        urllib.request.urlretrieve(
            image_url, os.path.join(save_path, image_name))
    except:
        sys.exit('Unable to download image')


def download_album_info(discogs_id):
    release = d.release(discogs_id)
    artist_name = trim_artist_name(release.artists[0].name)
    sub_save_path = os.path.join(SAVE_PATH, artist_name, release.title)
    if not os.path.exists(sub_save_path):
        os.makedirs(sub_save_path)

    for file_name, x in discogs_info_toxml(release).items():
        xml_string = x.toprettyxml()
        with open(os.path.join(sub_save_path, file_name),
                  'w', encoding='utf-8') as f:
            f.write(xml_string)

    download_album_artwork(release, sub_save_path)

    print('complete!')


if __name__ == '__main__':
    argv = sys.argv
    if len(argv) != 2:
        print('Usage: python %s release_id' % argv[0])
        quit()
    release_id = int(argv[1])
    download_album_info(release_id)
