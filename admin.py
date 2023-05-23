#!/usr/bin/env python3

import os
import sys
import io
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

EDITABLE_EXTENSIONS = (
    # wmk content which can be handled without pandoc:
    'md', 'mdwn', 'mdown', 'markdown', 'mmd', 'gfm', 'html', 'htm',
    # wmk content which requires pandoc:
    'org', 'rst', 'tex', 'man', 'rtf', 'textile', 'xml', 'jats', 'tei', 'docbook',
    # other common text-based formats:
    'yaml', 'yml', 'json', 'js', 'css', 'scss',
    'csv', 'txt', 'sgml', 'ini', 'toml', 'svg', )

# Map the above extensions to Ace Editor modes.
# Without available Ace modes: org, man, rtf, csv, txt
ACE_EDITOR_MODES = {
    'md': 'markdown',
    'mdwn': 'markdown',
    'mdown': 'markdown',
    'markdown': 'markdown',
    'mmd': 'markdown',
    'gfm': 'markdown',
    'html': 'html',
    'htm': 'html',
    'rst': 'rst',
    'tex': 'latex',
    'textile': 'textile',
    'xml': 'xml', # actually JATS by default
    'jats': 'xml',
    'tei': 'xml',
    'docbook': 'xml',
    'yaml': 'yaml',
    'yml': 'yaml',
    'json': 'json',
    'js': 'javascript',
    'css': 'css',
    'scss': 'scss',
    'sgml': 'html',
    'ini': 'ini',
    'toml': 'toml',
    'svg': 'xml',
}

# Find out where wmk resides and add it to the python path
wmkenv_info = subprocess.run(["wmk", "env", "."], cwd=BASEDIR,
                         capture_output=True, text=True)
wfound = re.search(r'wmk home: (.*)', wmkenv_info.stdout)
if wfound:
    sys.path.append(wfound.group(1))
    import wmk
else:
    print("ERROR: Could not load wmk environment. Is wmk installed?")
    sys.exit(1)

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
    pw = get_configured_password(errors_fatal=False)
    conf_err = not pw
    response.set_header('Cache-Control', 'no-store')
    return template('login.tpl', err=False, conf_err=conf_err)


@post('/_/admin/login/')
def login_post():
    conf_pass = get_configured_password()
    is_hashed = len(conf_pass) == 64 and re.match(r'^[0-9a-f]+$', conf_pass)
    submitted_pass = request.forms.getunicode('password', '')
    pass_match = False
    msg = None
    response.set_header('Cache-Control', 'no-store')
    if is_hashed and hashlib.sha256(submitted_pass.encode('utf-8')).hexdigest() == conf_pass:
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
        if not ext in EDITABLE_EXTENSIONS:
            abort(403, "Extension '{}' not supported".format(ext) )
    else:
        abort(405, "Bad input")
    return edit_form(section, filename, full_path)


@post('/_/admin/edit/<section:re:content|data|static>/<filename:re:.*>')
@authorize
def content_file_save(section, filename):
    return save_file(section, filename, request)


@get('/_/admin/edit-config/')
@authorize
def edit_config_form():
    return edit_form(
        None, 'wmk_config.yaml', os.path.join(BASEDIR, 'wmk_config.yaml'))


@post('/_/admin/edit-config/')
@authorize
def edit_config_save():
    return save_file(None, 'wmk_config.yaml', request)


@post('/_/admin/preview/')
def preview_html():
    filename = request.params.get('filename')
    source = request.params.get('source')
    html = wmk.preview_single(BASEDIR, filename, source)
    return html


@route('/_/admin')
@route('/_/admin/')
@authorize
def admin_frontpage():
    msg = get_flash_message(request) or ''
    msg_status = 'warning'
    if msg.startswith('S:'):
        msg = msg[2:]
        msg_status = 'success'
    conf = get_config(BASEDIR)
    site = conf.get('site', {})
    site_title = None
    for k in ('name', 'title', 'site_name', 'site_title'):
        site_title = site.get(k, None)
        if site_title:
            break
    return template('frontpage.tpl', flash_message=msg,
                    msg_status=msg_status, site_title=site_title)


@route('/_/admin/list/<section:re:content|data|static>')
@route('/_/admin/list/<section:re:content|data|static>/<dirname:re:.*>')
@authorize
def list_dir(section, dirname=''):
    full_dirname = os.path.join(BASEDIR, section, dirname)
    dir_entries = [_ for _ in os.scandir(full_dirname)]
    sort_by_date = request.params.get('sort', '') == 'date'
    if sort_by_date:
        ordering = {
            'reverse': True,
            'key': lambda x: x.stat().st_mtime,
        }
    else:
        ordering = {'key': lambda x: x.name}
    dir_entries.sort(**ordering)
    flash_message = get_flash_message(request)
    svg_dir = os.path.join(bottle.TEMPLATE_PATH[0], 'svg')
    return template(
        'list_dir.tpl', section=section, dirname=dirname,
        dir_entries=dir_entries, full_dirname=full_dirname,
        flash_message=flash_message, directories=get_directories(),
        editable_exts=EDITABLE_EXTENSIONS, svg_dir=svg_dir,
    )

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

def get_config(dirname, identifier='wmk_config'):
    """
    Will NOT raise an error if the yaml file is not at the expected location,
    only print a warning to the console.
    """
    config_file = os.path.join(dirname, '%s.yaml' % identifier)
    conf = {}
    try:
        with open(config_file) as f:
            conf = yaml.safe_load(f)
    except FileNotFoundError:
        print("WARNING: File '{}' not found".format(config_file))
    return conf or {}


def get_configured_password(errors_fatal=True):
    conf = get_config(BASEDIR, 'wmk_admin')
    # Preferably sha256-hashed
    conf_pass = conf.get('admin_password', None)
    if errors_fatal and not conf_pass:
        abort(403, 'admin_password is missing from wmk_admin.yaml')
    return conf_pass


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
    old_stdout = sys.stdout
    tmp_stdout = io.StringIO()
    sys.stdout = tmp_stdout
    wmk.main(BASEDIR)
    sys.stdout = old_stdout
    if msg:
        logfile = os.path.join(BASEDIR, 'tmp/admin.log')
        end = datetime.datetime.now()
        duration = end - start
        with open(logfile, 'a') as f:
            f.write("\n=====\nRan wmk build. Reason: %s\n" % msg)
            f.write("[Timing: %s to %s; duration=%s]\n" % (str(start), str(end), str(duration)))
            show_lines = [_ for _ in tmp_stdout.getvalue().split("\n")
                          if 'WARN' in _ or 'ERR' in _]
            if show_lines:
                f.write("\n".join(show_lines)+"\n")
    tmp_stdout.close()


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
    is_config = section is None and filename == 'wmk_config.yaml'
    conf = get_config(BASEDIR,  'wmk_admin') or {}
    msg = get_flash_message(request) or ''
    return template('edit_form.tpl', filename=filename,
                    contents=contents, section=section, is_config=is_config,
                    editable_exts=EDITABLE_EXTENSIONS, ace_modes=ACE_EDITOR_MODES,
                    preview_css=conf.get('preview_css', ''), flash_message=msg)


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
    is_config = section is None and filename == 'wmk_config.yaml'
    root = BASEDIR if is_config else os.path.join(BASEDIR, section)
    full_path = os.path.join(root, filename)
    new_contents = request.forms.getunicode('contents')
    new_contents = new_contents.replace("\r\n", "\n")
    with open(full_path, 'w') as f:
        f.write(new_contents)
    wmk_build('Saved file ' + full_path)
    redir_url = ''
    if is_config:
        set_flash_message(
            request, 'S:Updated main site configuration file, wmk_config.yaml')
        redir_url = '/_/admin/'
    else:
        display_path = os.path.join(section, filename)
        display_dir, display_filename = os.path.split(display_path)
        set_flash_message(request, 'Saved file "%s" in %s' % (display_filename, display_dir))
        redir_url = '/_/admin/list/%s' % display_dir
    if 'save_and_edit' in request.forms:
        redir_url = request.url
    redirect(redir_url)


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
    host = 'localhost'
    port = 7077
    try:
        basedir = os.path.split(os.path.dirname(__file__))[0]
        config_file = os.path.join(basedir, 'wmk_admin.yaml')
        conf = {}
        if os.path.exists(config_file):
            with open(config_file) as f:
                conf = yaml.safe_load(f)
        else:
            print("WARNING: wmk_admin.yaml not found in %s" % basedir)
        if 'port' in conf:
            port = conf['port']
        if 'host' in conf:
            host = conf['host']
    except Exception as e:
        print("WARNING: Error in loading wmk_admin.yaml: %s" % str(e))
    run(host=host, port=port, debug=True)
