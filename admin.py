import os
import re
import random
import datetime
import string
import bottle
from bottle import (
        route, request, response, run, static_file,
        HTTPError, get, post, template, redirect)

# Assumes we're in admin/ subdir of project directory
BASEDIR = os.path.dirname(__file__)[:-6]
bottle.TEMPLATE_PATH = [os.path.join(BASEDIR, 'admin', 'views')]

COOKIE_NAME = 'wmk_' + re.sub(r'\W', '', BASEDIR)
PASSWORD = 'abc123'


def authorize(fn):
    def inner():
        response.set_header('Cache-Control', 'no-store')
        if not is_logged_in(request):
            redirect('/_/admin/login/')
        else:
            return fn()
    return inner


def is_logged_in(request):
    val = request.get_cookie(COOKIE_NAME) or ''
    if val and re.match(r'^\w+$', val):
        # print("GOT COOKIE:", val)
        tmpdir = os.path.join(BASEDIR, 'tmp')
        filename = os.path.join(tmpdir, val + '.session')
        if os.path.exists(filename):
            # print("RETURNING FILENAME", filename)
            return filename
    else:
        # print("GOT NO COOKIE")
        return False


@get('/_/admin/login/')
def login_get():
    if is_logged_in(request):
        return template('soft_redirect.tpl')
    return template('login.tpl', err=False)


@post('/_/admin/login/')
def login_post():
    if request.forms.get('password', '') == PASSWORD:
        val = ''.join(random.choices(string.ascii_letters, k=20))
        tmpdir = os.path.join(BASEDIR, 'tmp')
        filename = os.path.join(tmpdir, val + '.session')
        with open(filename, 'w') as f:
            f.write(COOKIE_NAME + ' ' + str(datetime.datetime.now()))
        #print("SETTING COOKIE", COOKIE_NAME, "=", val)
        response.set_cookie(COOKIE_NAME, val, path='/')
        return template('soft_redirect.tpl')
    else:
        return template('login.tpl', err=True)


@get('/_/admin/logout/')
def logout():
    filename = is_logged_in(request)
    if filename:
        os.remove(filename)
    redirect('/_/admin/')


@get('/_/admin/upload/')
def upload_get():
    return upload_form()


@post('/_/admin/upload/')
def upload_post():
    return handle_upload(request)


@get('/_/admin/edit/<section:re:content|data>/<filename:re:.*>')
def content_file_form(section, filename):
    root = os.path.join(BASEDIR, section)
    full_path = os.path.join(root, filename)
    if not os.path.isfile(full_path):
        return HTTPError(404, "Not found")
    found = re.search(r'\.(\w+)', filename)
    if found:
        ext = found.group(1)
        if not ext in ('md', 'html'):
            return HTTPError(403, "Forbidden")
    else:
        return HTTPError(405, "Bad input")
    return edit_form(section, filename, full_path)


@post('/_/admin/edit/<section:re:content|data>/<filename:re:.*>')
def content_file_save(section, filename):
    return save_file(filename, request)


@route('/_/admin')
@route('/_/admin/')
@authorize
def server_admin_main():
    return template('frontpage.tpl')


@route('/_/admin/list/<section:re:content|data|static>/<dirname:re:.*>')
def list_dir(section, dirname):
    full_dirname = os.path.join(BASEDIR, section, dirname)
    dir_entries = [_ for _ in os.scandir(full_dirname)]
    dir_entries.sort(key=lambda x: x.name)
    return template(
            'list_dir.tpl', section=section, dirname=dirname,
            dir_entries=dir_entries, full_dirname=full_dirname)


def edit_form(section, filename, full_path):
    with open(full_path) as f:
        contents = f.read()
    return template('edit_form.tpl', filename=filename, contents=contents, section=section)


def handle_upload(request):
    dest_dir = request.forms.get('dest_dir')
    ok_dirs = ('static', 'content', 'data')
    if not dest_dir in ok_dirs or dest_dir.startswith(tuple([_+'/' for _ in ok_dirs])):
        return HTTPError(403, "Invalid destination directory: {}".format(dest_dir))
    if not os.path.isdir(os.path.join(BASEDIR, dest_dir)):
        return HTTPError(403, "Destination directory '{}' does not exist".format(dest_dir))
    filename = request.forms.get('dest_name').strip('/')
    if '/' in filename:
        return HTTPError(403, "Slashes in filenames not allowed; please create directory first if needed")
    full_path = os.path.join(BASEDIR, dest_dir, filename)
    if os.path.exists(full_path):
        return HTTPError(403, 'Overwriting not allowed')
    if not os.path.isdir(os.path.dirname(full_path)):
        os.makedirs(os.path.dirname(full_path))
    upload = request.files.get('upload')
    upload.save(full_path)
    return template('file_saved.tpl', dest_dir=dest_dir, filename=filename)


def upload_form():
    dest_dirs = []
    for d in ('content', 'data', 'static'):
        dest_dirs.append(d)
        walker = os.walk(d)
        for it in walker:
            if it[1]:
                for sd in it[1]:
                    dest_dirs.append(os.path.join(it[0], sd))
    dest_dirs.sort()
    return template('upload_form.tpl', dest_dirs=dest_dirs)


def save_file(filename, request):
    root = os.path.join(BASEDIR, 'content')
    full_path = os.path.join(root, filename)
    new_contents = request.forms.get('contents')
    new_contents = new_contents.replace("\r\n", "\n")
    with open(full_path, 'w') as f:
        f.write(new_contents)
    return template('file_saved.tpl', dest_dir='content', filename=filename)

# ---------------------- static below

@route('/')
@route('/<filename:re:.+>')
def server_static(filename='index.html'):
    root = os.path.join(BASEDIR, 'htdocs')
    full_path = os.path.join(root, filename)
    if os.path.isdir(full_path):
        filename += '/index.html'
    resp = static_file(filename, root=root)
    if 'Content-Type' in resp.headers and resp.headers['Content-Type'].startswith('text/html'):
        if isinstance(resp.body, str):
            body = resp.body.encode('utf-8')
        elif isinstance(resp.body, bytes):
            body = resp.body
        else:
            body = resp.body.read()
            resp.body.close()
        body = body.replace(b'</body>', bottle_marker() + b'</body>')
        resp.body = body
        resp.headers['Content-Length'] = str(len(body))
    return resp

def bottle_marker():
    return b'''
    <div id="bottle-notice"
         style="background:red;color:yellow;padding:.5em;position:fixed;bottom:0;right:0;width:250px;text-align:center">
         <strong><small>Admin server</small></strong></div>'''



if __name__ == '__main__':
    run(host='localhost', port=7077, debug=True)
