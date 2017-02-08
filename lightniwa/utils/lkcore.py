import imghdr
import json
import os
import re
import requests

from database import Volume, Book
from lightniwa import app


def download_img(img_path, tag=''):
    print(img_path)
    if not img_path.startswith('/'):
        return
    # if not os.path.exists(d) or not imghdr.what(app.config['PRIVATE_PATH'] + img_path):
    d = os.path.dirname(app.config['PRIVATE_PATH'] + img_path)
    if not os.path.exists(d):
        os.makedirs(d)
    if not os.path.exists(app.config['PRIVATE_PATH'] + img_path) or not imghdr.what(app.config['PRIVATE_PATH'] + img_path):
        print('%s: %s' % (tag, img_path))
        r = requests.get(app.config['API_URL'] + img_path, headers=app.config['API_HEADER'])
        if r.status_code != 200:
            return
        with open(os.path.join(app.config['PRIVATE_PATH'] + img_path), 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)


def download_txt(chapter_id, file_path, tag=''):
    if not os.path.isfile(app.config['PRIVATE_PATH'] + file_path):
        d = os.path.dirname(app.config['PRIVATE_PATH'] + file_path)
        if not os.path.exists(d):
            os.makedirs(d)
        print('%s: %s' % (tag, file_path))
        path = '/api_node/view/%s' % chapter_id
        r = requests.get(app.config['API_URL'] + path, headers=app.config['API_HEADER'])
        if r.status_code != 200:
            return
        contents = json.loads(r.text)
        content = ''
        for line in contents['content']:
            line = line['content']
            m = re.search(r"http://[^\s]*?\.(jpg|jpeg|png)", line)
            if m:
                img_path = m.group(0).replace('http://lknovel.lightnovel.cn', '').replace('http://www.lightnovel.cn', '')
                download_img(img_path)
                line = img_path
            line = line.replace('<br>', '')
            content += line + '\n'
        if not os.path.exists(app.config['PRIVATE_PATH'] + file_path):
            d = os.path.dirname(app.config['PRIVATE_PATH'] + file_path)
            if not os.path.exists(d):
                os.makedirs(d)
            with open(os.path.join(app.config['PRIVATE_PATH'] + file_path), 'wb') as f:
                f.write(bytes(content, 'UTF-8'))
                f.close()


def download_volume(volume_id, redownload=0):
    v = Volume.query.filter_by(id=volume_id).first()
    if not v and redownload == 0:
        return

    path = '/api_node/vol/%s' % volume_id
    r = requests.get(app.config['API_URL'] + path, headers=app.config['API_HEADER'])
    if r.status_code != 200:
        return
    vol_content = json.loads(r.text)
    if len(vol_content['volDetail']) <= 0:
        return
    print(volume_id)
    vol_json = vol_content['volDetail'][0]

    b = Book.query.filter_by(id=vol_json['series_id']).first()
    sql = 'SELECT id FROM book WHERE id=%s'
    # cursor.execute(sql, (vol_json['series_id'],))
    # if cursor.rowcount == 0:
    #     sql = 'INSERT INTO book (id, name, author, publisher) VALUES (%s, %s, %s, %s)'
    #     cursor.execute(sql, (vol_json['series_id'], vol_json['novel_title'], vol_json['novel_author'],
    #                          vol_json['novel_pub']))
    #
    # sql = 'SELECT id FROM volume WHERE id=%s'
    # cursor.execute(sql, (vol_json['id'],))
    # if cursor.rowcount == 0:
    #     sql = 'INSERT INTO volume (id, book_id, name, description, cover, update_time, `index`, click) VALUES ' \
    #           '(%s, %s, %s, %s, %s, %s, %s, %s)'
    #
    #     cursor.execute(sql, (vol_json['id'], vol_json['series_id'], vol_json['vol_title'], vol_json['vol_desc'],
    #                          vol_json['vol_cover'], vol_json['vol_updatedate'], vol_json['vol_number'],
    #                          vol_json['vol_click'],))
    #
    # sql = 'UPDATE book SET cover=%s WHERE id=%s'
    # cursor.execute(sql, (vol_json['vol_cover'], vol_json['series_id']))
    # download_img(vol_json['vol_cover'])
    #
    # if len(vol_content['chapterResult']) <= 0:
    #     cursor.close()
    #     return
    # chapter_json = vol_content['chapterResult']
    # for chapters in chapter_json:
    #     sql = 'SELECT id FROM chapter WHERE id=%s'
    #     cursor.execute(sql, (chapters['chapter_id'],))
    #     if cursor.rowcount == 0:
    #         sql = 'INSERT INTO chapter ' \
    #               '(id, book_id, vol_id, name, update_by, update_time, file_path, `key`, `view`, `index`)' \
    #               ' VALUES' \
    #               ' (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    #         cursor.execute(sql, (chapters['chapter_id'], chapters['series_id'], chapters['vol_id'],
    #                              chapters['chapter_title'], chapters['chapter_updater'], chapters['chapter_updatedate'],
    #                              chapters['chapter_textfile'], chapters['chapter_key'], chapters['chapter_view'],
    #                              chapters['chapter_index']))
    #     download_txt(chapters['chapter_id'], chapters['chapter_textfile'])
    #
    # mysql.connection.commit()
    # cursor.close()


def download_chapter(chapter_id):
    return
    # cursor = mysql.connection.cursor()
    # sql = 'SELECT id FROM chapter WHERE id=%s'
    # cursor.execute(sql, chapter_id)

    # if cursor.rowcount != 0:
    #     cursor.close()
    #     return
    # print(chapter_id)
