import os
import re
import random
import datetime
import string
import subprocess
import yaml
import shutil
import hashlib

import bottle
from bottle import (
        route, request, response, run, static_file,
        HTTPError, get, post, template, redirect, abort)

# Assumes the admin.py file is in immediate subdir of the project directory
BASEDIR = os.path.split(os.path.dirname(__file__))[0]
bottle.TEMPLATE_PATH = [os.path.join(os.path.dirname(__file__), 'views')]

COOKIE_NAME = 'wmk_' + re.sub(r'\W', '', BASEDIR)


# ----- Decorator(s) --------

def authorize(fn):
    def inner(*args, **kwargs):
        response.set_header('Cache-Control', 'no-store')
        if not is_logged_in(request):
            redirect('/_/admin/login/')
        else:
            return fn(*args, **kwargs)
    return inner


# ----- Routed actions (other than static) below -----------

@get('/_/admin/login/')
def login_get():
    if is_logged_in(request):
        return template('soft_redirect.tpl')
    conf = get_config(BASEDIR)
    conf_err = False
    if not conf.get('admin_password'):
        conf_err = True
    response.set_header('Cache-Control', 'no-store')
    return template('login.tpl', err=False, conf_err=conf_err)


@post('/_/admin/login/')
def login_post():
    conf = get_config(BASEDIR)
    if not conf.get('admin_password'):
        abort(403, 'admin_password is missing from wmk_config.yaml')
    # Preferably sha256-hashed
    conf_pass = conf['admin_password']
    is_hashed = len(conf_pass) == 64 and re.match(r'^[0-9a-f]+$', conf_pass)
    submitted_pass = request.forms.getunicode('password', '')
    pass_match = False
    msg = None
    response.set_header('Cache-Control', 'no-store')
    if is_hashed and hashlib.sha265(submitted_pass.encode('utf-8')).hexdigest() == conf_pass:
        pass_match = True
    if not is_hashed and conf_pass == submitted_pass:
        pass_match = True
        msg = 'The password in wmk_config.yaml is in plaintext. For increased security, you should hash it using SHA256.'
    if pass_match:
        val = ''.join(random.choices(string.ascii_letters, k=20))
        tmpdir = os.path.join(BASEDIR, 'tmp')
        filename = os.path.join(tmpdir, val + '.session')
        with open(filename, 'w') as f:
            f.write(COOKIE_NAME + ' ' + str(datetime.datetime.now()))
        response.set_cookie(COOKIE_NAME, val, path='/')
        if msg:
            set_flash_message(request, msg, filename=filename)
        return template('soft_redirect.tpl')
    else:
        return template('login.tpl', err=True, conf_err=False)


@get('/_/admin/logout/')
def logout():
    filename = is_logged_in(request)
    if filename:
        os.remove(filename)
    response.delete_cookie(COOKIE_NAME, path='/')
    response.set_header('Cache-Control', 'no-store')
    redirect('/_/admin/login/')


@get('/_/admin/upload/')
@authorize
def upload_get():
    return upload_form()


@post('/_/admin/upload/')
@authorize
def upload_post():
    return handle_upload(request)


@get('/_/admin/build/')
@authorize
def build_site():
    hard_rebuild = request.params.get('hard', False)
    wmk_build('Manually requested', hard_rebuild)
    msg = 'The site was rebuilt.'
    if hard_rebuild:
        msg += ' The contents of the htdocs directory and the cache were removed first (hard rebuild).'
    # the S says that the status is success
    set_flash_message(request, 'S:'+msg)
    redirect('/_/admin/')


@get('/_/admin/edit/<section:re:content|data|static>/<filename:re:.*>')
@authorize
def content_file_form(section, filename):
    root = os.path.join(BASEDIR, section)
    full_path = os.path.join(root, filename)
    if not os.path.isfile(full_path):
        abort(404, "Not found")
    found = re.search(r'\.(\w+)', filename)
    if found:
        ext = found.group(1)
        if not ext in ('md', 'html', 'css', 'js'):
            abort(403, "Forbidden")
    else:
        abort(405, "Bad input")
    return edit_form(section, filename, full_path)


@post('/_/admin/edit/<section:re:content|data|static>/<filename:re:.*>')
@authorize
def content_file_save(section, filename):
    return save_file(section, filename, request)


@route('/_/admin')
@route('/_/admin/')
@authorize
def admin_frontpage():
    msg = get_flash_message(request) or ''
    wcc = ''
    with open(os.path.join(BASEDIR, 'wmk_config.yaml')) as f:
        wcc = f.read()
    msg_status = 'warning'
    if msg.startswith('S:'):
        msg = msg[2:]
        msg_status = 'success'
    return template('frontpage.tpl', flash_message=msg,
                    msg_status=msg_status, wmk_config_contents=wcc)


@route('/_/admin/list/<section:re:content|data|static>/<dirname:re:.*>')
@authorize
def list_dir(section, dirname):
    full_dirname = os.path.join(BASEDIR, section, dirname)
    dir_entries = [_ for _ in os.scandir(full_dirname)]
    dir_entries.sort(key=lambda x: x.name)
    flash_message = get_flash_message(request)
    return template(
            'list_dir.tpl', section=section, dirname=dirname,
            dir_entries=dir_entries, full_dirname=full_dirname,
            flash_message=flash_message, directories=get_directories())

@post('/_/admin/move/')
@authorize
def move_or_rename():
    """
      <form action="/_/admin/move/" method="POST">
        <input type="hidden" name="from_dir" value="{{ from_dir }}">
        <input type="hidden" name="orig_name" value="{{ orig_name }}">
        <input type="hidden" name="is_dir" value="{{ '1' if is_dir else '0' }}">
        <label>New name</label>
        <input type="text" name="new_name" value="{{ orig_name }}">
        <label>New directory</label>
        <select name="dest_dir">
          % for d in directories:
            <option value="{{ d }}"{{ ' selected' if d == from_dir else '' }}>{{ d }}</option>
          % end
        </select>
        <input type="submit" value="Rename/Move">
    """
    is_dir = request.forms.getunicode('is_dir') == '1'
    from_dir = request.forms.getunicode('from_dir')
    dest_dir = request.forms.getunicode('dest_dir')
    orig_name = request.forms.getunicode('orig_name')
    new_name = request.forms.getunicode('new_name')
    okdirs = ('content', 'data', 'static')
    if not from_dir.startswith(okdirs) and dest_dir.startswith(okdirs):
        abort(403, 'Move/rename outside authorized directories attempted')
    if not new_name or new_name.startswith('.'):
        abort(403, 'New name must be filled out and must not start with a dot')
    if from_dir == dest_dir and orig_name == new_name:
        # No need to do anything
        redirect('/_/admin/list/' + from_dir)
    full_from_dir = os.path.join(BASEDIR, from_dir)
    full_dest_dir = os.path.join(BASEDIR, dest_dir)
    if not os.path.isdir(full_from_dir) and os.path.isdir(full_dest_dir):
        abort(403, "Both origin and destination directories must exist")
    full_from = os.path.join(full_from_dir, orig_name)
    full_dest = os.path.join(full_dest_dir, new_name)
    if not os.path.exists(full_from):
        abort(403, "The origin file/directory does not exist")
    if os.path.exists(full_dest):
        abort(403, "The move/rename conflicts with an existing file/directory")
    typ = 'directory' if is_dir else 'file'
    if from_dir == dest_dir:
        msg = 'Renamed a %s from %s to %s (in %s)' % (typ, orig_name, new_name, from_dir)
    elif orig_name == new_name:
        msg = 'Moved the %s %s from %s to %s' % (typ, orig_name, from_dir, dest_dir)
    else:
        msg = 'Moved the %s %s from %s to %s and gave it the new name %s' % (
            typ, orig_name, from_dir, dest_dir, new_name)
    shutil.move(full_from, full_dest)
    set_flash_message(request, msg)
    wmk_build(msg)
    maybe_slash = '/' if from_dir in okdirs else ''
    # NOTE: should we go to dest_dir instead?
    redirect('/_/admin/list/%s%s' % (from_dir, maybe_slash))


@post('/_/admin/create-dir/<section:re:content|data|static>/<dirname:re:.*>')
@authorize
def create_dir(section, dirname):
    full_dirname = os.path.join(BASEDIR, section, dirname) if dirname else os.path.join(BASEDIR, section)
    new_dirname = request.forms.getunicode('new_dir')
    if not new_dirname:
        abort(403, 'New dirname must not be empty')
    if '/' in new_dirname:
        abort(403, 'Slashes not allowed in new dirname')
    new_path = os.path.join(full_dirname, new_dirname)
    if os.path.exists(new_path):
        abort(403, 'A directory/file of that name already exists')
    os.mkdir(new_path)
    msg = 'Created directory %s in %s' % (new_dirname, full_dirname[len(BASEDIR)+1:])
    set_flash_message(request, msg)
    wmk_build(msg)
    redirect('/_/admin/list/%s/%s' % (section, dirname))


@post('/_/admin/create-file/<section:re:content|data|static>/<dirname:re:.*>')
@authorize
def create_file(section, dirname):
    full_dirname = os.path.join(BASEDIR, section, dirname) if dirname else os.path.join(BASEDIR, section)
    new_filename= request.forms.getunicode('new_filename')
    if not new_filename:
        abort(403, 'New filename must not be empty')
    if '/' in new_filename:
        abort(403, 'Slashes not allowed in new filename')
    new_path = os.path.join(full_dirname, new_filename)
    if os.path.exists(new_path):
        abort(403, 'A directory/file of that name already exists')
    with open(new_path, 'w') as f:
        f.write('')
    msg = 'Created file %s in %s' % (new_filename, full_dirname[len(BASEDIR)+1:])
    set_flash_message(request, msg)
    wmk_build(msg)
    redirect('/_/admin/list/%s/%s' % (section, dirname))


@get('/_/admin/rmdir/<section:re:content|data|static>/<dirname:re:.+>')
@authorize
def remove_dir(section, dirname):
    full_dirname = os.path.join(BASEDIR, section, dirname)
    os.rmdir(full_dirname)
    list_dirname = re.sub(r'/[^/]+$', '', dirname) if '/' in dirname else ''
    msg = 'Removed directory %s from %s' % (dirname, section)
    set_flash_message(request, msg)
    wmk_build(msg)
    redirect('/_/admin/list/%s/%s' % (section, list_dirname))


@get('/_/admin/delete/<section:re:content|data|static>/<filename:re:.+>')
@authorize
def del_file(section, filename):
    full_filename = os.path.join(BASEDIR, section, filename)
    os.remove(full_filename)
    list_dirname = re.sub(r'/[^/]+$', '', filename) if '/' in filename else ''
    msg = 'Deleted file %s from %s' % (filename, section)
    wmk_build(msg)
    set_flash_message(request, msg)
    redirect('/_/admin/list/%s/%s' % (section, list_dirname))


# ------ Helpers below ------------

def get_config(dirname):
    "Will raise an error if wmk_config.yaml is not at the expected location."
    config_file = os.path.join(dirname, 'wmk_config.yaml')
    conf = {}
    with open(config_file) as f:
        conf = yaml.safe_load(f)
    return conf


def wmk_build(msg=None, hard=False):
    start = datetime.datetime.now()
    if hard and msg:
        msg += ' - HARD REBUILD!'
    if hard:
        tmpdir = os.path.join(BASEDIR, 'tmp')
        tmpfiles = os.listdir(tmpdir)
        for fn in tmpfiles:
            if fn.startswith('wmk_render_cache'):
                os.unlink(os.path.join(tmpdir, fn))
        shutil.rmtree(os.path.join(BASEDIR, 'htdocs'))
    ret = subprocess.run(["wmk", "b", "."], cwd=BASEDIR,
                         capture_output=True, text=True)
    if msg:
        logfile = os.path.join(BASEDIR, 'tmp/admin.log')
        end = datetime.datetime.now()
        duration = end - start
        with open(logfile, 'a') as f:
            f.write("\n=====\nRan wmk build. Reason: %s\n" % msg)
            f.write("[Timing: %s to %s; duration=%s]\n" % (str(start), str(end), str(duration)))
            f.write(ret.stdout)


def get_flash_message(request):
    msg = None
    filename = (is_logged_in(request) or '').replace('.session', '.flash')
    if os.path.exists(filename):
        with open(filename) as f:
            msg = f.read()
        os.remove(filename)
    return msg


def set_flash_message(request, msg, filename=None):
    if filename is None:
        filename = is_logged_in(request) or ''
    filename = filename.replace('.session', '.flash')
    if filename and filename.endswith('.flash'):
        with open(filename, 'w') as f:
            f.write(msg)


def is_logged_in(request):
    val = request.get_cookie(COOKIE_NAME) or ''
    if val and re.match(r'^\w+$', val):
        tmpdir = os.path.join(BASEDIR, 'tmp')
        filename = os.path.join(tmpdir, val + '.session')
        if os.path.exists(filename):
            return filename
    else:
        return False


def edit_form(section, filename, full_path):
    with open(full_path) as f:
        contents = f.read()
    return template('edit_form.tpl', filename=filename, contents=contents, section=section)


def handle_upload(request):
    dest_dir = request.forms.getunicode('dest_dir')
    ok_dirs = ('static', 'content', 'data')
    if not (dest_dir in ok_dirs or dest_dir.startswith(tuple([_+'/' for _ in ok_dirs]))):
        abort(403, "Invalid destination directory: {}".format(dest_dir))
    if not os.path.isdir(os.path.join(BASEDIR, dest_dir)):
        abort(403, "Destination directory '{}' does not exist".format(dest_dir))
    filename = request.forms.getunicode('dest_name').strip('/') or ''
    automatic_name = False
    if '/' in filename:
        abort(403, "Slashes in filenames not allowed; please create directory first if needed")
    upload = request.files.get('upload')
    if not filename:
        filename = upload.filename.lower()
        filename = re.sub(r'^.*[/\\]', '', filename)
        filename = re.sub(r'\s+', '_', filename)
        filename = re.sub(r'__+', '_', filename)
        automatic_name = True
    if filename.startswith('.'):
        abort(403, "Names of uploaded files must not start with a dot")
    if not re.search(r'\.\w{1,8}$', filename):
        abort(403, "Uploaded files must have a valid file extension")
    full_path = os.path.join(BASEDIR, dest_dir, filename)
    if os.path.exists(full_path) and automatic_name:
        rand = '__' + ''.join(random.choices(string.ascii_uppercase, k=5))
        full_path = re.sub(r'(\.\w{1,8})$', rand + r'\1', full_path)
        filename = re.sub(r'(\.\w{1,8})$', rand + r'\1', filename)
    if os.path.exists(full_path):
        abort(403, 'Overwriting files via upload is not allowed')
    #if not os.path.isdir(os.path.dirname(full_path)):
    #    os.makedirs(os.path.dirname(full_path))
    upload.save(full_path)
    msg = "File %s uploaded to %s" % (filename, dest_dir)
    wmk_build(msg)
    set_flash_message(request, msg)
    redirect('/_/admin/list/%s' % dest_dir)
    #return template('file_saved.tpl', dest_dir=dest_dir, filename=filename)


def get_directories():
    "content, data, static and their subdirectories as a flat, sorted list"
    dest_dirs = []
    for d in ('content', 'data', 'static'):
        dest_dirs.append(d)
        walker = os.walk(d)
        for it in walker:
            if it[1]:
                for sd in it[1]:
                    dest_dirs.append(os.path.join(it[0], sd))
    dest_dirs.sort()
    return dest_dirs


def upload_form():
    dest_dirs = get_directories()
    return template('upload_form.tpl', dest_dirs=dest_dirs)


def save_file(section, filename, request):
    root = os.path.join(BASEDIR, section)
    full_path = os.path.join(root, filename)
    new_contents = request.forms.getunicode('contents')
    new_contents = new_contents.replace("\r\n", "\n")
    with open(full_path, 'w') as f:
        f.write(new_contents)
    wmk_build()
    display_path = os.path.join(section, filename)
    display_dir, display_filename = os.path.split(display_path)
    set_flash_message(request, 'Saved file "%s" in %s' % (display_filename, display_dir))
    redirect('/_/admin/list/%s' % display_dir)
    # return template('file_saved.tpl', dest_dir='content', filename=filename)


# ---------------------- Static routes below ----


@route('/_/<filename:re:(?:img|js|css)/.+>')
def admin_static(filename):
    "Images, css and js for admin site."
    root = os.path.join(os.path.dirname(__file__), 'static')
    return static_file(filename, root=root)


@route('/')
@route('/<filename:re:.+>')
def wmk_site(filename='index.html'):
    "The built wmk site from htdocs."
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
        body = body.replace(b'</body>', admin_marker() + b'</body>')
        resp.body = body
        resp.headers['Content-Length'] = str(len(body))
    return resp

def admin_marker():
    return b'''
    <div id="in-admin-notice"
         style="background:red;color:yellow;padding:.5em;position:fixed;bottom:0;right:0;width:200px;text-align:center">
         <strong><small><a href="/_/admin/" style="color:yellow">Admin</a></small></strong></div>'''



if __name__ == '__main__':
    run(host='localhost', port=7077, debug=True)
