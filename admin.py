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
from PIL import Image

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

# Extensions for images and attachments (used on the edit page):
IMG_EXTENSIONS = ('jpg', 'jpeg', 'png', 'gif', 'svg', )
ATTACHMENT_EXTENSIONS = ('pdf', 'docx', 'odt', 'zip', 'tar', 'gz', 'mp3', 'm4a', )

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


@post('/_/admin/edit-upload/')
@authorize
def edit_upload():
    return handle_attachment_upload(request)


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


@get('/_/admin/deploy/')
@authorize
def deploy_site():
    conf = get_config(BASEDIR, 'wmk_admin')
    deploy_command = conf.get('deploy')
    if deploy_command:
        wmk_build('Rebuilding before DEPLOY action')
        depl_res = subprocess.run(deploy_command, cwd=BASEDIR,
                                  capture_output=True, text=True)
        logfile = os.path.join(BASEDIR, 'tmp/admin.log')
        depl_log = os.path.join(BASEDIR, 'tmp/deploy.log')
        now = datetime.datetime.now()
        with open(logfile, 'a') as f:
            f.write("\n=====\nRan DEPLOY at %s. Output:\n" % str(now))
            if depl_res.stdout:
                f.write(depl_res.stdout)
        with open(depl_log, 'a') as f:
            f.write("DEPLOY " + str(now) + "\n")
        set_flash_message(request, 'S:Rebuilt and published site (ran deployment command).')
    else:
        set_flash_message('No deployment command specified in configuration file')
    redirect('/_/admin/')


@get('/_/admin/edit/<section:re:content|data|static>/<filename:re:.*>')
@authorize
def content_file_form(section, filename):
    root = os.path.join(BASEDIR, section)
    full_path = os.path.join(root, filename)
    if not os.path.isfile(full_path):
        abort(404, "Not found")
    ext = os.path.splitext(filename)[1]
    if ext:
        ext = ext[1:]
    if not ext in EDITABLE_EXTENSIONS:
        abort(403, "Extension '{}' not supported".format(ext) )
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
    adm_conf = get_config(BASEDIR, 'wmk_admin')
    status_info = get_status()
    deploy = adm_conf.get('deploy', False)
    site_title = None
    for k in ('name', 'title', 'site_name', 'site_title'):
        site_title = site.get(k, None)
        if site_title:
            break
    return template('frontpage.tpl', flash_message=msg,
                    msg_status=msg_status, site_title=site_title,
                    deploy=deploy, status_info=status_info)


@route('/_/admin/list/<section:re:content|data|static>')
@route('/_/admin/list/<section:re:content|data|static>/<dirname:re:.*>')
@authorize
def list_dir(section, dirname=''):
    start = datetime.datetime.now()
    full_dirname = os.path.join(BASEDIR, section, dirname)
    if not os.path.exists(full_dirname):
        abort(404, f"Directory {full_dirname} not found")
    dir_entries = [_ for _ in os.scandir(full_dirname)
                   if not _.name in ('.git', '.gitignore')]
    sort_by_date = request.params.get('sort', '') == 'date'
    if sort_by_date:
        ordering = {
            'reverse': True,
            'key': lambda x: x.stat().st_mtime,
        }
    else:
        ordering = {'key': lambda x: x.name}
    dir_entries.sort(**ordering)
    total_entries = len(dir_entries)
    search = request.params.getunicode('search')
    if search and search.strip():
        search_expr = wmk.slugify(search)
        if search_expr:
            keep = []
            for it in dir_entries:
                if search_expr in it.name:
                    keep.append(it)
            dir_entries = keep
    flash_message = get_flash_message(request)
    svg_dir = os.path.join(bottle.TEMPLATE_PATH[0], 'svg')
    end = datetime.datetime.now()
    page = int(request.params.get('p', 1))
    pagesize = 50
    pagecount = 1
    paginated = len(dir_entries) > pagesize
    entry_count = len(dir_entries)
    if paginated:
        pagecount = len(dir_entries) // pagesize
        if len(dir_entries) % 100:
            pagecount += 1
        dir_entries = dir_entries[(page-1)*pagesize:page*pagesize]
    return template(
        'list_dir.tpl', section=section, dirname=dirname,
        dir_entries=dir_entries, full_dirname=full_dirname,
        flash_message=flash_message, directories=get_directories(),
        editable_exts=EDITABLE_EXTENSIONS, svg_dir=svg_dir,
        paginated=paginated, pagecount=pagecount, page=page,
        entry_count=entry_count, sort_by_date=sort_by_date,
        search=search, total_entries=total_entries, imsiz=imsiz,
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


@post('/_/admin/create-page/<section:re:content|data|static>/<dirname:re:.*>')
@authorize
def create_page(section, dirname):
    "Create new Markdown page based on title. Also fills autofields in."
    full_dirname = os.path.join(BASEDIR, section, dirname) if dirname else os.path.join(BASEDIR, section)
    title = request.forms.getunicode('title')
    conf = get_config(BASEDIR, 'wmk_admin')
    auto_metadata = conf.get('auto_metadata') or {}
    content = f"---\ntitle: {title}\n---\n\n"
    if 'md' in auto_metadata:
        content = maybe_add_metadata(content, auto_metadata['md'])
    new_filename = wmk.slugify(title) + '.md'
    new_path = os.path.join(full_dirname, new_filename)
    if os.path.exists(new_path):
        abort(403, f'A file named {new_filename} already exists at {section}/{dirname}')
    with open(new_path, 'w') as f:
        f.write(content)
    msg = f'Created page "{title}" in {section}/{dirname}'
    set_flash_message(request, msg)
    path = os.path.join(section, dirname, new_filename) \
            if dirname else os.path.join(section, new_filename)
    redirect('/_/admin/edit/' + path)


@post('/_/admin/create-file/<section:re:content|data|static>/<dirname:re:.*>')
@authorize
def create_file(section, dirname):
    "Create empty file"
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
    # wmk_build(msg)
    ext = os.path.splitext(new_filename)
    if ext in EDITABLE_EXTENSIONS:
        path = os.path.join(section, dirname, new_filename) \
            if dirname else os.path.join(section, new_filename)
        redirect('/_/admin/edit/' + path)
    else:
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
    page = int(request.params.get('p', 1))
    maybe_page = f'?p={page}' if page > 1 else ''
    redirect('/_/admin/list/%s/%s%s' % (section, list_dirname, maybe_page))


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


def get_status():
    ret = {
        'deployed_date': None,
        'git_status': '',
        'git_last_commit': '',
    }
    deploy_status_file = os.path.join(BASEDIR, 'tmp', 'deploy.log')
    if os.path.exists(deploy_status_file):
        st = os.stat(deploy_status_file)
        ret['deployed_date'] = datetime.datetime.fromtimestamp(st.st_mtime)
    if os.path.isdir(os.path.join(BASEDIR, '.git')):
        gitstatus = subprocess.run(
            ["git", "status", "-s"], cwd=BASEDIR, capture_output=True, text=True)
        ret['git_status'] = gitstatus.stdout
        commitinfo = subprocess.run(
            ['git', 'log', '-1', '--date=iso', '--pretty=[%h] %ad'],
            cwd=BASEDIR, capture_output=True, text=True)
        ret['git_last_commit'] = re.sub(r' [+\-]\d\d\d\d$', '', commitinfo.stdout)
    return ret


def wmk_build(msg=None, hard=False, quick=False):
    start = datetime.datetime.now()
    if hard and msg:
        msg += ' - HARD REBUILD!'
    if hard:
        quick = False
        tmpdir = os.path.join(BASEDIR, 'tmp')
        tmpfiles = os.listdir(tmpdir)
        for fn in tmpfiles:
            if fn.startswith('wmk_render_cache'):
                os.unlink(os.path.join(tmpdir, fn))
        shutil.rmtree(os.path.join(BASEDIR, 'htdocs'))
    old_stdout = sys.stdout
    tmp_stdout = io.StringIO()
    sys.stdout = tmp_stdout
    wmk.main(BASEDIR, quick=quick)
    sys.stdout = old_stdout
    if msg:
        logfile = os.path.join(BASEDIR, 'tmp/admin.log')
        end = datetime.datetime.now()
        duration = end - start
        with open(logfile, 'a') as f:
            f.write("\n=====\nRan wmk %sbuild. Reason: %s\n" % ('quick ' if quick else '', msg))
            f.write("[Timing: %s to %s; duration=%s]\n" % (str(start), str(end), str(duration)))
            show_lines = [_ for _ in tmp_stdout.getvalue().split("\n")
                          if 'WARN' in _ or 'ERR' in _]
            if show_lines:
                f.write("\n".join(show_lines)+"\n")
    tmp_stdout.close()


def imsiz(f):
    path = f.path if hasattr(f, 'path') else f
    with Image.open(path) as im:
        return im.size


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
    if msg.startswith('S:'):
        msg = msg[2:]
    if is_config:
        attachment_dir = None
        fn = filename
    else:
        attachment_dir, fn = os.path.split(filename)
        attachment_dir = os.path.join(section, attachment_dir).strip('/')
    fn_base, fn_ext = os.path.splitext(fn)
    potential_attachments = fn_ext[1:] in EDITABLE_EXTENSIONS[:18]
    nearby_files = []
    if potential_attachments:
        if not os.path.splitext(fn)[0] == 'index':
            attachment_dir = os.path.join(attachment_dir, fn_base)
        if os.path.isdir(os.path.join(BASEDIR, attachment_dir)):
            nearby_files = get_potential_attachments(attachment_dir)
    imged_tpl = conf.get('img_to_editor_template')
    atted_tpl = conf.get('attachment_to_editor_template')
    return template('edit_form.tpl', filename=filename,
                    contents=contents, section=section, is_config=is_config,
                    editable_exts=EDITABLE_EXTENSIONS, ace_modes=ACE_EDITOR_MODES,
                    img_exts=IMG_EXTENSIONS, att_exts=ATTACHMENT_EXTENSIONS,
                    preview_css=conf.get('preview_css', ''), flash_message=msg,
                    potential_attachments=potential_attachments,
                    attachment_dir=attachment_dir, nearby_files=nearby_files,
                    img_to_editor_template=imged_tpl,
                    attachment_to_editor_template=atted_tpl, imsiz=imsiz)


def get_potential_attachments(attachment_dir):
    fulldir = os.path.join(BASEDIR, attachment_dir)
    ret = [_ for _ in os.scandir(fulldir)
           if _.is_file() and (
                   _.name.lower().endswith(IMG_EXTENSIONS)
                   or _.name.endswith(ATTACHMENT_EXTENSIONS))]
    ret.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return ret


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
    if len(filename) > 42:
        filename = filename[:20] + '__' + filename[-20:]
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


def handle_attachment_upload(request):
    dest_dir = request.forms.getunicode('attachment_dir') or ''
    if not dest_dir.startswith('content'):
        abort(403, "Invalid destination directory: {}".format(dest_dir))
    full_dest_dir = os.path.join(BASEDIR, dest_dir)
    if not os.path.isdir(full_dest_dir):
        os.mkdir(full_dest_dir)
    upload_count = int(request.forms.get('upload_count', 0))
    for i in range(upload_count):
        upload = request.files.get(f'upload_{i}')
        filename = upload.filename.lower()
        filename = re.sub(r'^.*[/\\]', '', filename)
        filename = re.sub(r'\s+', '_', filename)
        filename = re.sub(r'__+', '_', filename)
        while filename.startswith('.'):
             filename = filename[1:]
        if len(filename) > 42:
             filename = filename[:20] + '__' + filename[-20:]
        if not re.search(r'\.\w{1,8}$', filename):
            filename += '.bin'
        full_path = os.path.join(full_dest_dir, filename)
        if os.path.exists(full_path) and automatic_name:
            rand = '__' + ''.join(random.choices(string.ascii_uppercase, k=5))
            full_path = re.sub(r'(\.\w{1,8})$', rand + r'\1', full_path)
            filename = re.sub(r'(\.\w{1,8})$', rand + r'\1', filename)
        upload.save(full_path)
    if upload_count == 1:
        msg = "Attachment file %s uploaded to %s" % (filename, dest_dir)
        feedback = "Uploaded: '%s'" % filename
    else:
        msg = "%d files uploaded to %s" % (upload_count, dest_dir)
        feedback = "Uploaded %d files" % upload_count
    wmk_build(msg)
    files = get_potential_attachments(dest_dir)
    return template('edit-attachments.tpl',
                    attachment_dir=dest_dir, files=files, msg=feedback,
                    img_exts=IMG_EXTENSIONS, att_exts=ATTACHMENT_EXTENSIONS,
                    imsiz=imsiz)


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


def maybe_add_metadata(text, metafields):
    """
    Add the specified YAML metadata fields to the document if they are missing.
    If the document has no metadata block, it will be added.

    Currently only the metafields `date`, `modified_date` and `created_date` are
    supported.  If specified, each is added if missing. In addition,
    `modified_date` will be updated even if present. If `date` is present and
    `created_date` is not, the value of `date` will be used rather than the
    current timestamp for `created_date`.
    """
    metafields = [_ for _ in metafields
                  if _ in ('date', 'modified_date', 'created_date')]
    if not metafields:
        return text
    text = text.replace("\r\n", "\n")
    now = str(datetime.datetime.now())[:16]
    add = []
    chg = {}
    dateval = None
    if 'created_date' in metafields:
        found = re.search(r'^date: *\D?(\d\d\d\d-\d\d-\d\d[ T\d:]*)', text, flags=re.M)
        if found:
            dateval = found.group(1).strip()
    for field in metafields:
        val = dateval if dateval and field=='created_date' else now
        add.append({'field': field, 'val': '%s: "%s"' % (field, val)})
    if 'modified_date' in metafields:
        chg = {'field': 'modified_date', 'val': 'modified_date: "%s"' % now}
    if text.startswith("---\n"):
        prepend = ''
        found = re.search(r'^---\n(.*?)\n---\n', text, flags=re.S)
        if found:
            meta_block = found.group(1)
            for it in add:
                if re.search(r'^%s:' % it['field'], meta_block, flags=re.M):
                    continue
                text = text.replace("---\n", "---\n%s\n" % it['val'], 1)
            if chg and re.search(r'^%s:' % chg['field'], meta_block, flags=re.M):
                text = re.sub(
                    r'^%s:.*' % chg['field'], chg['val'],
                    text, flags=re.M, count=1)
    else:
        prepend = "---\n"
        for it in add:
            prepend += it['val'] + "\n"
        prepend += "---\n\n"
        text = prepend + text
    return text


def save_file(section, filename, request):
    is_config = section is None and filename == 'wmk_config.yaml'
    root = BASEDIR if is_config else os.path.join(BASEDIR, section)
    full_path = os.path.join(root, filename)
    new_contents = request.forms.getunicode('contents')
    new_contents = new_contents.replace("\r\n", "\n")
    conf = get_config(BASEDIR, 'wmk_admin') or {}
    auto_metadata = conf.get('auto_metadata') or {}
    ext = os.path.splitext(filename)[1]
    if auto_metadata and ext[1:] in auto_metadata:
        # auto_metadata is a map from file extension to list of datetime
        # fields to be automatically added/updated.
        new_contents = maybe_add_metadata(
            new_contents, auto_metadata[ext[1:]])
    with open(full_path, 'w') as f:
        f.write(new_contents)
    quick_build = section and section == 'content'
    wmk_build('Saved file ' + full_path, quick=quick_build)
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
    conf = get_config(BASEDIR, 'wmk_admin')
    show_admin_overlay = True
    if 'show_admin_overlay' in conf:
        if str(conf['show_admin_overlay']) in ('', '0', 'false', 'False', 'no'):
            show_admin_overlay = False
        if conf['show_admin_overlay'] in ('logged-in', 'admin', 'admin-only'):
            show_admin_overlay = True if is_logged_in(request) else False
    resp = static_file(filename, root=root)
    if 'Content-Type' in resp.headers and resp.headers['Content-Type'].startswith('text/html'):
        if isinstance(resp.body, str):
            body = resp.body.encode('utf-8')
        elif isinstance(resp.body, bytes):
            body = resp.body
        else:
            body = resp.body.read()
            resp.body.close()
        edit_url = filename.replace('//', '/').replace('/index.html', '.md').replace('index.html', 'index.md')
        edit_url = '/_/admin/edit/content/%s' % edit_url
        if show_admin_overlay:
            body = body.replace(b'</body>', admin_marker(edit_url).encode('utf-8') + b'</body>')
        resp.body = body
        resp.headers['Content-Length'] = str(len(body))
    return resp

def admin_marker(edit_url):
    return f'''
    <div id="in-admin-notice"
         style="background:red;color:yellow;padding:.5em;position:fixed;bottom:0;right:0;width:230px;text-align:center">
         <strong><small><a href="/_/admin/" style="color:yellow;text-decoration:none">Admin</a></small></strong>
         | <small><a href="{edit_url}" style="color:yellow;text-decoration:none">edit</a></small>
    </div>'''



if __name__ == '__main__':
    host = 'localhost'
    port = 7077
    server = None
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
        if 'server' in conf:
            server = conf['server']
    except Exception as e:
        print("WARNING: Error in loading wmk_admin.yaml: %s" % str(e))
    run(host=host, port=port, debug=True, server=server)
