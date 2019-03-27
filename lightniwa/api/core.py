import hashlib
import os
import re
import time
import zipfile

from bs4 import BeautifulSoup
from flask import Blueprint, json, request
from flask import redirect
from flask import send_from_directory
from flask_login import login_required
from qiniu import Auth
from sqlalchemy import func
from lightniwa import app

from database import Article, User, db_session, engine, Book, Volume, Anime, Count, Chapter
from lightniwa.helper import api_helper

mod = Blueprint('api', __name__, url_prefix='/api/v1')


def update_info():
    resp = {}
    resp['versionCode'] = 21
    resp['url'] = 'https://ltype.me/static/LightNiwa_v0.8.4_build20190327.apk'
    resp['message'] = '\n*API已经大改需要更新(以前写的太烂我已经看不懂了)\n1.修复了一些BUG\n2.优化部分UI'
    return resp


@mod.route('/checkUpdate')
@mod.route('/checkupdate')
def check_update():
    return json.dumps(update_info(), ensure_ascii=False), 200, {'ContentType': 'application/json'}


@mod.route('/version')
def version():
    return api_helper.wrap_resp(update_info())


@mod.route('/search')
def search():
    check_bot(request, 30)
    version_code = request.args.get('version_code')
    version_code = int((version_code, 0)[not version_code])
    keyword = request.args.get('keyWord')
    if not keyword:
        keyword = request.args.get('keyword')
    if keyword.find('ln') == 0:
        keyword = keyword.replace('ln', '')
    result = db_session.query(Book, func.sum(Volume.download).label('download')).join(Volume, Volume.book_id == Book.id) \
        .filter(func.concat(Volume.name, Book.name, Book.author, Book.illustrator).like('%' + keyword + '%')) \
        .group_by(Book.id).order_by(Volume.download.desc())
    resp = []
    for item in result:
        book = item.Book.to_json()
        book['download'] = int(item.download)
        resp.append(book)
    if version_code >= app.config['VERSION_CODE']:
        return api_helper.wrap_resp(resp)
    else:
        return api_helper.dumps(resp)


@mod.route('/book/<int:book_id>')
def book(book_id):
    check_bot(request, 30)
    version_code = request.args.get('version_code')
    version_code = int((version_code, 0)[not version_code])
    if version_code >= app.config['VERSION_CODE']:
        b = Book.query.filter_by(id=book_id).first()
        volumes = Volume.query.filter_by(book_id=book_id).all()
        resp = b.to_json()
        resp['volumes'] = [v.to_json() for v in volumes]
        return api_helper.wrap_resp(resp)
    else:
        b = Book.query.filter_by(id=book_id).first()
        volumes = Volume.query.filter_by(book_id=book_id).all()
        resp = {}
        resp['book'] = b.to_json()
        resp['volumes'] = [v.to_json() for v in volumes]
        return api_helper.dumps(resp)


@mod.route('/volume/<int:volume_id>', methods=['GET', 'POST'])
def volume_get(volume_id):
    check_bot(request, 30)
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


latest_cache = []
latest_update_time = 0


@mod.route('/latest')
@mod.route('/latestupdate')
def latest():
    version_code = request.args.get('version_code')
    version_code = int((version_code, 0)[not version_code])
    global latest_cache
    global latest_update_time
    if not latest_cache or latest_update_time + 3600 < time.time():
        result = db_session.query(Book, Volume).join(Volume, Volume.book_id == Book.id) \
            .order_by(Volume.id.desc()).limit(30)
        resp = []
        if version_code >= app.config['VERSION_CODE']:
            for line in result:
                item = line.Volume.to_json()
                item['book'] = line.Book.to_json()
                resp.append(item)
            latest_cache = resp
            latest_update_time = time.time()
        else:
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
            return api_helper.dumps(resp)
    return api_helper.wrap_resp(latest_cache)


@mod.route('/popular')
def popular():
    version_code = request.args.get('version_code')
    version_code = int((version_code, 0)[not version_code])
    resp = []
    if version_code >= app.config['VERSION_CODE']:
        result = db_session.query(Book, func.sum(Volume.download).label('total')) \
            .join(Volume, Volume.book_id == Book.id) \
            .group_by(Book.id).order_by(Volume.download.desc()).limit(20)
        for item in result:
            book = item.Book.to_json()
            book['total'] = int(item.total)
            resp.append(book)
        return api_helper.wrap_resp(resp)
    else:
        result = db_session.query(Book, func.sum(Volume.download).label('total')) \
            .join(Volume, Volume.book_id == Book.id) \
            .group_by(Book.id).order_by(Volume.download.desc()).limit(20)
        for line in result:
            item = {}
            item['book_id'] = line.Book.id
            item['book_name'] = line.Book.name
            item['book_author'] = line.Book.author
            item['book_illustrator'] = line.Book.illustrator
            item['book_publisher'] = line.Book.publisher
            item['book_cover'] = line.Book.cover
            item['total'] = int(line.total)
            resp.append(item)
        return api_helper.dumps(resp)


@mod.route('/anime/<int:month>')
def anime(month):
    version_code = request.args.get('version_code')
    version_code = int((version_code, 0)[not version_code])
    result = db_session.query(Book, Anime).join(Anime, Anime.book_id == Book.id).filter(Anime.month == month)
    resp = []
    if version_code >= app.config['VERSION_CODE']:
        for line in result:
            resp.append(line.Book.to_json())
    else:
        for line in result:
            item = {}
            item['book_id'] = line.Book.id
            item['book_name'] = line.Book.name
            item['book_cover'] = line.Book.cover
            item['author'] = line.Book.author
            item['illustrator'] = line.Book.illustrator
            item['publisher'] = line.Book.publisher
            resp.append(item)
        return api_helper.dumps(resp)
    return api_helper.wrap_resp(resp)


@mod.route('/cover/image/<file_dir>/<file_name>.jpg')
def cover(file_dir, file_name):
    check_bot(request, 30)
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
@mod.route('/download/volume/<int:volume_id>')
def download_volume(volume_id):
    check_bot(request, 30)
    Volume.query.filter_by(id=volume_id).update({"download": (Volume.download + 1)})

    db_session.commit()

    result = db_session.query(Book, Volume).join(Volume, Volume.book_id == Book.id).filter(
        Volume.id == volume_id).first()
    if not result:
        return 404
    path = '/zip/%s/%s.zip' % (result.Book.id, volume_id)
    if os.path.exists(app.config['PRIVATE_PATH'] + path):
        q = Auth(app.config['QN_ACCESS_KEY'], app.config['QN_SECRET_KEY'])
        base_url = 'http://%s/%s' % (app.config['QN_BUCKET_DOMAIN'], path)
        private_url = q.private_download_url(base_url, expires=3600)
        return send_from_directory(app.config['PRIVATE_PATH'] + '/zip/%s' % result.Book.id, '%s.zip' % volume_id)
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

            chapters = Chapter.query.filter_by(vol_id=volume_id).all()
            chapters_json = []
            for row in chapters:
                chapter_json = {}
                chapter_json['index'] = row.index
                chapter_json['book_id'] = row.book_id
                chapter_json['volume_id'] = row.vol_id
                chapter_json['chapter_id'] = row.id
                chapter_json['name'] = row.name
                chapters_json.append(chapter_json)

                # lkcore.download_txt(row['chapter_id'], row['file_path'])
                contents = []
                f = open(app.config['PRIVATE_PATH'] + row.file_path, 'r', encoding='utf-8')
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
                zf.writestr('content/%s.json' % row.id, json.dumps(contents, ensure_ascii=False))

            zf.writestr('info/book.json', json.dumps(book_json, ensure_ascii=False))
            zf.writestr('info/volume.json', json.dumps(vol_json, ensure_ascii=False))
            zf.writestr('info/chapters.json', json.dumps(chapters_json, ensure_ascii=False))
            zf.close()
        except FileNotFoundError as e:
            print(e)
            zf.close()
            os.remove(zf.filename)
            raise e
        except OSError as e:
            print(e)
            zf.close()
            os.remove(zf.filename)
    return send_from_directory(os.path.dirname(zf.filename), '%s.zip' % volume_id)


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

    # threading.Thread(target=lkcore.download_volume(volume_id, 1)).start()


def check_bot(req, limit):
    ip = req.remote_addr
    now = int(str(time.time()).split('.')[0])
    count = Count.query.filter_by(ip=ip).first()
    if count:
        if count.last_time < now - 60 * 1:
            count.frequency = 1
        else:
            if count.frequency >= limit:
                raise FileNotFoundError
            count.frequency += 1
        count.total += 1
        count.last_time = now
    else:
        count = Count(ip=ip, last_time=now, frequency=0, total=0)
        db_session.add(count)
