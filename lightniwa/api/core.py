import hashlib
import os
import re
import time
import zipfile

from bs4 import BeautifulSoup
from flask import Blueprint, json, request, render_template, jsonify
from flask import redirect
from flask import send_from_directory
from flask import url_for
from flask_login import login_required
from qiniu import Auth
from sqlalchemy import func
from lightniwa import app

from database import Article, User, db_session, engine, Book, Volume, Anime, Count, Chapter

mod = Blueprint('api', __name__, url_prefix='/api/v1')


@mod.route('/checkupdate')
def version():
    resp = {}
    resp['versionCode'] = 18
    resp['url'] = 'http://ltype.me/assets/LightNiwa_v0.8.2_build20151208_beta.apk'
    resp['message'] = '\n1.修复了一些BUG'
    return json.dumps(resp, ensure_ascii=False), 200, {'ContentType': 'application/json'}


@mod.route('/search')
def search():
    keyword = request.args.get('keyWord')
    if keyword.find('ln') == 0:
        keyword = keyword.replace('ln', '')
    result = db_session.query(Book, func.sum(Volume.download).label('download')).join(Volume, Volume.book_id == Book.id)\
        .filter(func.concat(Volume.name, Book.name, Book.author, Book.illustrator).like('%' + keyword + '%'))\
        .group_by(Book.id).order_by(Volume.download.desc())
    resp = []
    for item in result:
        book = item.Book.to_json()
        book['download'] = int(item.download)
        resp.append(book)
    print(resp)
    return json.dumps(resp, ensure_ascii=False), 200, {'ContentType': 'application/json'}


@mod.route('/book/<int:book_id>')
def book(book_id):
    version_code = request.args.get('version_code')
    version_code = (version_code, 0)[not version_code]
    resp = None
    if version_code >= app.config['VERSION_CODE']:
        b = Book.query.filter_by(id=book_id).first()
        volumes = Volume.query.filter_by(book_id=book_id).all()
        resp = b.to_json()
        resp['volumes'] = volumes
    else:
        sql = 'SELECT b.id book_id, b.name book_name, b.author book_author, b.illustrator book_illustrator,' \
              ' b.publisher book_publisher, b.cover book_cover' \
              ' FROM book b WHERE b.id = %s'
        sql = 'SELECT v.id vol_id, v.book_id book_id, v.name vol_name, v.description vol_description,' \
              ' v.cover vol_cover, v.index vol_index' \
              ' FROM volume v WHERE v.book_id = %s'
        b = Book.query.filter_by(id=book_id).first()
        volumes = Volume.query.filter_by(book_id=book_id).all()
        resp = b.to_json()
        resp['volumes'] = [v.to_json() for v in volumes]
        # result = {'book': book, 'volumes': volumes}
    return json.dumps(resp, ensure_ascii=False), 200, {'ContentType': 'application/json'}


@mod.route('/volume/<int:volume_id>', methods=['GET', 'POST'])
def volume_get(volume_id):
    v = Volume.query.filter_by(id=volume_id).first()
    resp = v.to_json()
    return json.dumps(resp, ensure_ascii=False), 200, {'ContentType': 'application/json'}


@login_required
@mod.route('/volume/<int:volume_id>', methods=['PATCH'])
def volume_patch(volume_id):
    v = Volume.query.filter_by(id=volume_id).first()
    print('name:%s' % request.form['name'])
    print('desc:%s' % request.form['desc'])
    print('file:%s' % request.files['file'].filename)
    # v.name = name
    # v.description = desc
    resp = v.to_json()
    return json.dumps(resp, ensure_ascii=False), 200, {'ContentType': 'application/json'}


@login_required
@mod.route('/volume/new', methods=['POST'])
def volume_post():
    v = Volume()
    data = request.json
    name = data['name']
    desc = data['desc']
    # v.name = name
    # v.description = desc
    print('name:%s,desc:%s' % (name, desc))
    resp = v.to_json()
    return json.dumps(resp, ensure_ascii=False), 200, {'ContentType': 'application/json'}


@mod.route('/chapter/<int:volume_id>', methods=['GET'])
def chapter_get(volume_id):
    chapters = Chapter.query.filter_by(vol_id=volume_id).all()
    resp = [c.to_json() for c in chapters]
    return json.dumps(resp, ensure_ascii=False), 200, {'ContentType': 'application/json'}


@login_required
@mod.route('/chapter/<int:volume_id>', methods=['POST'])
def chapter_post(volume_id):
    name = request.form.get('name')
    editor = request.form.get('editor')
    soup = BeautifulSoup(editor)
    for p in soup.find_all('p'):
        print(p.get_text())
    # print(editor)
    v = Volume.query.filter_by(id=volume_id).first()
    c = Chapter(book_id=v.book_id, vol_id=v.id, name=name, content=editor)
    return json.dumps({}, ensure_ascii=False), 200, {'ContentType': 'application/json'}


@login_required
@mod.route('/chapter/<int:chapter_id>', methods=['PATCH'])
def chapter_patch(chapter_id):
    data = request.json
    print('data:%s' % data)
    name = data['name']
    desc = data['desc']
    print('name:%s, desc:%s' % (name, desc))
    return json.dumps({}, ensure_ascii=False), 200, {'ContentType': 'application/json'}

latest_update_cache = []
latest_update_time = 0


@mod.route('/latestupdate')
def latest_update():
    global latest_update_cache
    global latest_update_time
    if not latest_update_cache or latest_update_time + 3600 < time.time():
        result = db_session.query(Book, Volume).join(Volume, Volume.book_id == Book.id)\
            .order_by(Volume.id.desc()).limit(20)
        resp = []
        for line in result:
            item = {}
            item['vol_id'] = line.Volume.id
            item['vol_index'] = line.Volume.index
            item['vol_name'] = line.Volume.name
            item['vol_cover'] = line.Volume.cover
            item['vol_description'] = line.Volume.description
            item['book_id'] = line.Book.id
            item['book_name'] = line.Book.name
            item['book_author'] = line.Book.author
            item['book_illustrator'] = line.Book.illustrator
            resp.append(item)
        latest_update_cache = resp
    return json.dumps(latest_update_cache, ensure_ascii=False), 200, {'ContentType': 'application/json'}


@mod.route('/popular')
def popular():
    version_code = request.args.get('version_code')
    version_code = int((version_code, 0)[not version_code])
    resp = []
    if version_code >= app.config['VERSION_CODE']:
        sql = 'SELECT b.id, b.name, b.author, b.illustrator, b.publisher, b.cover, SUM(v.download) total' \
              ' FROM volume v' \
              ' LEFT JOIN book b ON b.id = v.book_id' \
              ' GROUP BY v.book_id ORDER BY total DESC limit 0,20'
        result = db_session.query(Book, func.sum(Volume.download).label('total')) \
            .join(Volume, Volume.book_id == Book.id) \
            .group_by(Book.id).order_by(Volume.download.desc()).limit(20)
        for item in result:
            book = item.Book.to_json()
            book['total'] = int(item.total)
            resp.append(book)
    elif version_code > 16:
        sql = 'SELECT b.id book_id, b.name book_name, b.author book_author, b.illustrator book_illustrator,' \
              ' b.publisher book_publisher, b.cover book_cover,' \
              'SUM(v.download) total' \
              ' FROM volume v' \
              ' LEFT JOIN book b ON b.id = v.book_id' \
              ' GROUP BY v.book_id ORDER BY total DESC limit 0,20'
        result = db_session.query(Book, func.sum(Volume.download).label('total')) \
            .join(Volume, Volume.book_id == Book.id) \
            .group_by(Book.id).order_by(Volume.download.desc()).limit(20)
        for line in result:
            item = {}
            item['book_id'] = line.Book.id
            item['book_name'] = line.Book.name
            item['author'] = line.Book.id
            item['illustrator'] = line.Book.id
            item['publisher'] = line.Book.id
            item['cover'] = line.Book.id
            item['total'] = int(line.total)
            resp.append(item)
    else:
        sql = 'SELECT b.id book_id, b.name book_name, b.author, b.illustrator, b.publisher, b.cover book_cover' \
              ', v.id volume_id, v.name volume_name, v.cover volume_cover, v.`index` volume_index' \
              ', v.description volume_description, SUM(v.download) total' \
              ' FROM volume v' \
              ' LEFT JOIN book b ON b.id = v.book_id' \
              ' GROUP BY book_id ORDER BY total DESC limit 0,20'
        result = db_session.query(Book, Volume, func.sum(Volume.download).label('total')) \
            .join(Volume, Volume.book_id == Book.id) \
            .group_by(Book.id).order_by(Volume.download.desc()).limit(20)
        for line in result:
            item = {}
            item['book_id'] = line.Book.id
            item['book_name'] = line.Book.name
            item['author'] = line.Book.id
            item['illustrator'] = line.Book.id
            item['publisher'] = line.Book.id
            item['cover'] = line.Book.id
            item['volume_id'] = line.Volume.id
            item['volume_name'] = line.Volume.name
            item['volume_cover'] = line.Volume.cover
            item['volume_index'] = line.Volume.index
            item['volume_description'] = line.Volume.description
            item['total'] = int(line.total)
            resp.append(item)
    return json.dumps(resp, ensure_ascii=False), 200, {'ContentType': 'application/json'}


@mod.route('/anime/<int:month>')
def anime(month):
    sql = ' SELECT b.id book_id, b.name book_name, b.author, b.illustrator, b.publisher, b.cover book_cover' \
          ' FROM anime a LEFT JOIN book b ON b.id = a.book_id WHERE a.month = %s'
    result = db_session.query(Book, Anime).join(Anime, Anime.book_id == Book.id).filter(Anime.month == month)
    resp = []
    for line in result:
        item = {}
        item['book_id'] = line.Book.id
        item['book_name'] = line.Book.name
        item['book_cover'] = line.Book.cover
        item['author'] = line.Book.author
        item['illustrator'] = line.Book.illustrator
        item['publisher'] = line.Book.publisher
        resp.append(item)
    return json.dumps(resp, ensure_ascii=False), 200, {'ContentType': 'application/json'}


@app.route('/cover/image/<file_dir>/<file_name>.jpg')
def cover(file_dir, file_name):
    key = 'cover/image/%s/%s.jpg' % (file_dir, file_name)
    # if not os.path.isfile(app.config['PRIVATE_PATH'] + '/' + key):
        # lkcore.download_img('/' + key)
        # return 404
    q = Auth(app.config['QN_ACCESS_KEY'], app.config['QN_SECRET_KEY'])
    base_url = 'http://%s/%s' % (app.config['QN_BUCKET_DOMAIN'], key)
    private_url = q.private_download_url(base_url, expires=3600)
    # global cover_cache_time
    # if cover_cache_time + 3000 < time.time():
    #     q = Auth(qiniu.access_key, qiniu.secret_key)
    #     key1 = 'cover/image/christmas/cover_wa2_1.jpg'
    #     key2 = 'cover/image/christmas/cover_wa2_2.jpg'
    #     key3 = 'cover/image/christmas/cover_wa2_3.jpg'
    #     christmas_cover[0] = q.private_download_url('http://%s/%s' % (qiniu.bucket_domain, key1), expires=3600)
    #     christmas_cover[1] = q.private_download_url('http://%s/%s' % (qiniu.bucket_domain, key2), expires=3600)
    #     christmas_cover[2] = q.private_download_url('http://%s/%s' % (qiniu.bucket_domain, key3), expires=3600)
    #     cover_cache_time = time.time()
    # private_url = christmas_cover[random.randrange(0, 3)]
    return redirect(private_url)


# volume_id.zip
# |--info
# |--|--book.json
# |--|--volume.json
# |--|--chapters.json
# |--content
# |--|--chapter_id.json
# |--img
# |--|--|md5('/cover/image/20120803/20120803215640_24363.jpg').jpg
@app.route('/download/volume/<int:volume_id>')
def download_volume(volume_id):
    ip = request.remote_addr
    now = int(str(time.time()).split('.')[0])
    count = Count.query.filter_by(ip=ip).first()
    if count:
        if count.last_time < now - 60 * 1:
            sql = 'UPDATE download_ip SET frequency=1, total = total + 1, last_time=%s WHERE (ip=%s)'
            count.frequency = 1
        else:
            if count.frequency >= 5:
                raise FileNotFoundError
            sql = 'UPDATE download_ip SET frequency=frequency+1, total = total + 1, last_time=%s WHERE (ip=%s)'
            count.frequency += 1
        count.total += 1
        count.last_time = now
    else:
        count = Count(ip=ip, last_time=now, frequency=0, total=0)
        sql = 'INSERT INTO download_ip (ip, last_time) VALUES (%s, %s)'
        db_session.add(count)

    sql = 'UPDATE volume SET download = download + 1 WHERE id = %s'
    Volume.query.filter_by(id=volume_id).update({"download": (Volume.download + 1)})

    db_session.commit()

    sql = 'SELECT b.id book_id, b.name book_name, b.author, b.illustrator, b.publisher, b.cover book_cover ' \
          ' , v.id volume_id, v.name volume_name, v.cover volume_cover, v.`index` volume_index, v.description volume_desc' \
          ' FROM volume v LEFT JOIN book b on b.id = v.book_id ' \
          ' WHERE v.id = %s'
    result = db_session.query(Book, Volume).join(Volume, Volume.book_id == Book.id).filter(Volume.id == volume_id).first()
    if not result:
        return 404
    print(result)
    path = '/zip/%s/%s.zip' % (result.Book.id, volume_id)
    if os.path.exists(app.config['PRIVATE_PATH'] + path):
        q = Auth(app.config['QN_ACCESS_KEY'], app.config['QN_SECRET_KEY'])
        base_url = 'http://%s/%s' % (app.config['QN_BUCKET_DOMAIN'], path)
        private_url = q.private_download_url(base_url, expires=3600)
        return redirect(url_for(private_url))
    else:
        if not os.path.isdir(os.path.dirname(app.config['PRIVATE_PATH'] + path)):
            os.makedirs(os.path.dirname(app.config['PRIVATE_PATH'] + path))

        vol_cover = '/%s/img/%s.jpg' \
                    % (volume_id, hashlib.md5(result.Volume.cover.encode('utf-8')).hexdigest())
        if result.Book.cover:
            book_cover = '/%s/img/%s.jpg' \
                         % (volume_id, hashlib.md5(result.Book.cover.encode('utf-8')).hexdigest())
        else:
            book_cover = vol_cover
        book_json = {}
        book_json['book_id'] = result.Book.id
        book_json['author'] = result.Book.author
        book_json['illustrator'] = result.Book.illustrator
        book_json['publisher'] = result.Book.publisher
        book_json['name'] = result.Book.name
        book_json['cover'] = book_cover
        book_json['description'] = result.Volume.description

        vol_json = {}
        vol_json['index'] = result.Volume.index
        vol_json['book_id'] = result.Book.id
        vol_json['volume_id'] = result.Volume.id
        vol_json['name'] = result.Volume.id
        vol_json['cover'] = vol_cover
        vol_json['description'] = result.Volume.description

        try:
            # create a empty zip file
            zf = zipfile.ZipFile(app.config['PRIVATE_PATH'] + path, 'w', zipfile.ZIP_DEFLATED)
            zfi = zipfile.ZipInfo('info/')
            zf.writestr(zfi, '')
            zfi = zipfile.ZipInfo('img/')
            zf.writestr(zfi, '')
            zfi = zipfile.ZipInfo('content/')
            zf.writestr(zfi, '')

            # lkcore.download_img(result.Volume.cover)
            zf.write(app.config['PRIVATE_PATH'] + result.Volume.cover,
                     'img/%s.jpg' % hashlib.md5(result.Volume.cover.encode('utf-8')).hexdigest())

            sql = ' SELECT c.id chapter_id, c.book_id book_id, c.vol_id volume_id, c.name chapter_name, c.file_path file_path' \
                  ' , c.`index` chapter_index FROM chapter c' \
                  ' WHERE c.vol_id = %s'
            chapters = Chapter.query.filter_by(vol_id=volume_id).all()
            chapters_json = []
            for row in chapters:
                chapter_json = {}
                chapter_json['index'] = row.Chapter.index
                chapter_json['book_id'] = row.Chapter.book_id
                chapter_json['volume_id'] = row.Chapter.vol_id
                chapter_json['chapter_id'] = row.Chapter.id
                chapter_json['name'] = row.Chapter.name
                chapters_json.append(chapter_json)

                # lkcore.download_txt(row['chapter_id'], row['file_path'])
                contents = []
                f = open(app.config['PRIVATE_PATH'] + row.Chapter.file_path, 'r', encoding='utf-8')
                for line in f.readlines():
                    m = re.search(r"^/[^\s]*?\.(jpg|jpeg|png)", line)
                    is_img = '0'
                    if m:
                        is_img = '1'
                        img_path = m.group(0)
                        # lkcore.download_img(img_path)
                        if os.path.exists(app.config['PRIVATE_PATH'] + img_path):
                            encode_path = hashlib.md5(img_path.encode('utf-8')).hexdigest() + \
                                          os.path.splitext(img_path)[1]
                            zf.write(app.config['PRIVATE_PATH'] + img_path, 'img/%s' % encode_path)
                            line = '/%s/img/%s' % (volume_id, encode_path)
                        else:
                            line = '缺少插画，请联系管理'

                    content = {}
                    content['index'] = len(contents)
                    content['is_img'] = is_img
                    content['content'] = line
                    contents.append(content)
                zf.writestr('content/%s.json' % row.Chapter.id, json.dumps(contents, ensure_ascii=False))

            zf.writestr('info/book.json', json.dumps(book_json, ensure_ascii=False))
            zf.writestr('info/volume.json', json.dumps(vol_json, ensure_ascii=False))
            zf.writestr('info/chapters.json', json.dumps(chapters_json, ensure_ascii=False))
            zf.close()
        except FileNotFoundError as e:
            print(e)
            zf.close()
            os.remove(zf.filename)
            raise e
        except:
            zf.close()
            os.remove(zf.filename)
    print(os.path.dirname(zf.filename) + os.path.basename('%s.zip' % volume_id))
    return send_from_directory(os.path.dirname(zf.filename), os.path.basename('%s.zip' % volume_id))


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))


def async_download_volume(volume_id):
    v = Volume.query.filter_by(id=volume_id).first()
    # if not v:
    #     if 0 < v.id < 10000:
            # threading.Thread(target=lkcore.download_volume(volume_id, 1)).start()