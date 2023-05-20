% rebase('base.tpl', title='List directory: %s/%s' % (section, dirname))

% import os, datetime, hashlib
% fileid = lambda s: hashlib.sha1(s.encode('utf-8')).hexdigest()[:7]
% prefix = '/_/admin/list'
% paths = dirname.strip('/').split('/') if dirname else []
% edit_ok = tuple(['.'+_ for _ in editable_exts])
% view_ok = tuple(['.'+_ for _ in editable_exts[:18]])
% current_path = "%s%s%s" % (section, '/' if dirname else '', dirname)

<hgroup>
<h2>File manager</h2>
<p>Files and directories in <code>{{ current_path }}</code>
</hgroup>

<div class="breadcrumbs p-half pl-1 bg-contrast mb-2">
  <strong>Current path:</strong>&nbsp;
  <a href="{{ prefix }}/{{ section }}/">{{ section }}</a> /
  % for i, path in enumerate(paths):
    <a href="{{ prefix }}/{{ section }}/{{ '/'.join(paths[:i+1]) }}">{{ path }}</a> /
  % end
</div>

% if flash_message:
  <div class="admonition success">
    <p class="admonition-title">Success</p>
    <p>{{ flash_message }}</p>
  </div>
% end

% include('create-here-modals.tpl', section=section, dirname=dirname)

% if dir_entries:
<table class="dir-entries">
  <tr>
    <th style="width:36px"></th>
    <th>Name</th>
    <th class="ta-r">Size</th>
    <th>Modified</th>
    <th>Actions</th>
    </tr>
  </tr>
  % for it in dir_entries:
    % stat = it.stat()
    % typ = 'dir' if it.is_dir() else 'file' if it.is_file() else 'link' if it.is_symlink() else '?'
    % mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
  <tr>
    <td style="color:var(--accent)">
      % svg = 'file-text' if it.name.endswith(edit_ok) else 'file' if typ == 'file' else 'folder' if typ == 'dir' else 'minus'
      % include('svg/%s.svg' % svg)
    </td>
    <td>
      % if typ == 'file' and it.name.endswith(edit_ok):
        <a href="/_/admin/edit/{{ current_path }}/{{ it.name }}">{{ it.name }}</a>
      % elif typ == 'dir':
        <a href="{{ prefix }}/{{ current_path }}/{{ it.name }}">{{ it.name }}</a>
      % else:
        {{ it.name }}
      % end
    </td>
    <td class="ta-r">{{ stat.st_size }}</td>
    <td>{{ str(mtime)[:16] }}</td>
    <td>
    % if typ == 'file':
      % if it.name.endswith(edit_ok):
        <a href="/_/admin/edit/{{ current_path }}/{{ it.name }}">Edit</a>
      % end
      <a href="/_/admin/delete/{{ current_path }}/{{ it.name }}" onclick="return confirm('Are you sure you want to delete this?')">Delete</a>
      <label role="link" class="d-inl" for="move-{{ fileid(it.name) }}-modal">Move</label>
      % if section == 'content' and it.name.endswith(view_ok):
        % if it.name.startswith('index.'):
          <a href="/{{ dirname }}{{ '/' if dirname else ''}}" target="_blank">View</a>
        % else:
          <a href="/{{ dirname }}{{ '/' if dirname else ''}}{{ os.path.splitext(it.name)[0] }}/" target="_blank">View</a>
        % end
      % elif section in ('content', 'static'):
        <a href="/{{ dirname }}{{ '/' if dirname else ''}}{{ it.name }}" target="_blank">View</a>
      % end
    % elif typ == 'dir':
      <a href="{{ prefix }}/{{ current_path }}/{{ it.name }}">Open</a>
      % if not os.listdir(os.path.join(full_dirname, it.name)):
        <a href="/_/admin/rmdir/{{ current_path }}/{{ it.name }}">Remove</a>
      % end
      <label role="link" class="d-inl" for="move-{{ fileid(it.name) }}-modal">Move</label>
    % end
    </td>
  </tr>
  % end
</table>
% else:
<div class="admonition"><p>No files or subdirectories in this directory</p></div>
% end

% for it in dir_entries:
  % if it.is_dir() or it.is_file():
    % include("rename-move-modal.tpl", section=section, dirname=dirname, is_dir=it.is_dir(), orig_name=it.name, directories=directories, fileid=fileid(it.name))
  % end
% end
