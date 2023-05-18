% rebase('base.tpl', title='List directory: %s/%s' % (section, dirname))

% import os, datetime
% prefix = '/_/admin/list'
% paths = [_ for _ in os.path.split(dirname) if _] if dirname else []

<a href="/_/admin/">To admin frontpage</a>
<div class="breadcrumbs bg-contrast mb-3">
  <strong>Current path:</strong>
  <a href="/_/admin/">(admin)</a> /
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

% if dir_entries:
<table>
  <tr>
    <th>Name</th>
    <th>Type</th>
    <th>Size</th>
    <th>Modified</th>
    <th>Actions</th>
    </tr>
  </tr>
  % for it in dir_entries:
    % stat = it.stat()
    % typ = 'dir' if it.is_dir() else 'file' if it.is_file() else 'link' if it.is_symlink() else '?'
    % mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
  <tr>
    <td>{{ it.name }}</td>
    <td>{{ typ }}</td>
    <td class="ta-r">{{ stat.st_size }}</td>
    <td>{{ str(mtime)[:16] }}</td>
    <td>
    % if typ == 'file':
      <a href="/_/admin/edit/{{ section }}/{{ dirname }}{{ '/' if dirname else ''}}{{ it.name }}">Edit</a>
      <a href="/_/admin/delete/{{ section }}/{{ dirname }}{{ '/' if dirname else ''}}{{ it.name }}">Delete</a>
      % if section == 'content' and it.name.endswith(('.md', '.html', '.rst', '.org')):
        % if it.name.startswith('index.'):
          <a href="/{{ dirname }}{{ '/' if dirname else ''}}" target="_blank">View</a>
        % else:
          <a href="/{{ dirname }}{{ '/' if dirname else ''}}{{ os.path.splitext(it.name)[0] }}/" target="_blank">View</a>
        % end
      % end
    % elif typ == 'dir':
      <a href="{{ prefix }}/{{ section }}/{{ dirname }}{{ '/' if dirname else ''}}{{ it.name }}">Open</a>
      % if not os.listdir(os.path.join(full_dirname, it.name)):
        <a href="/_/admin/rmdir/{{ section }}/{{ dirname }}{{ '/' if dirname else ''}}{{ it.name }}">Remove</a>
      % end
    % end
    </td>
  </tr>
  % end
</table>
% else:
<div class="admonition"><p>No files or subdirectories in this directory</p></div>
% end

% include('create-here-modals.tpl', section=section, dirname=dirname)
