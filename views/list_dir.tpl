% rebase('base.tpl', title='List directory: %s/%s' % (section, dirname))

<%
import os, datetime, hashlib, re

fileid = lambda s: hashlib.sha1(s.encode('utf-8')).hexdigest()[:7]
prefix = '/_/admin/list'
paths = dirname.strip('/').split('/') if dirname else []
edit_ok = tuple(['.'+_ for _ in editable_exts])
view_ok = tuple(['.'+_ for _ in editable_exts[:18]])
current_path = "%s%s%s" % (section, '/' if dirname else '', dirname)

svg_files = [_ for _ in os.listdir(svg_dir) if _.endswith('.svg')]
slurp = lambda nam: (f:=open(nam),f.read(),f.close())[1]
svg = dict([ (os.path.splitext(it)[0], slurp(os.path.join(svg_dir, it))) for it in svg_files ])
%>

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

% include('create-here-modals.tpl', section=section, dirname=dirname, svg=svg, sort_by_date=sort_by_date, search=search)

% if dir_entries:
<div class="x-scroll">
<table class="dir-entries mt-0">
  <tr>
    <th style="width:36px" class="icn"></th>
    <th class="nam"><a href="?sort=name">Name</a></th>
    <th class="ta-r size">Size</th>
    <th class="mtime"><a href="?sort=date">Modified</a></th>
    <th class="ta-r">Actions</th>
   </tr>
  </tr>
  % for it in dir_entries:
    % stat = it.stat()
    % typ = 'dir' if it.is_dir() else 'file' if it.is_file() else 'link' if it.is_symlink() else '?'
    % mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
  <tr>
    <td class="icn">
      % svgkey = 'file-text' if it.name.endswith(edit_ok) else 'file' if typ == 'file' else 'folder' if typ == 'dir' else 'minus'
      {{! svg[svgkey] }}
    </td>
    <td class="nam">
      % if typ == 'file' and it.name.endswith(edit_ok):
        <a href="/_/admin/edit/{{ current_path }}/{{ it.name }}">{{ it.name }}</a>
      % elif typ == 'dir':
        <a href="{{ prefix }}/{{ current_path }}/{{ it.name }}">{{ it.name }}</a>
      % else:
        {{ it.name }}
      % end
    </td>
    <td class="ta-r size">{{ stat.st_size }}</td>
    <td class="mtime">{{ str(mtime)[:16] }}</td>
    <td class="actions ta-r">
    % if typ == 'file':
      % if it.name.endswith(edit_ok):
        <a href="/_/admin/edit/{{ current_path }}/{{ it.name }}" title="Edit">{{! svg['edit'] }}</a>
      % end
      <a href="/_/admin/delete/{{ current_path }}/{{ it.name }}" onclick="return confirm('Are you sure you want to delete this?')" title="Delete">{{! svg['trash']}}</a>
      <label role="link" class="d-inl" for="move-{{ fileid(it.name) }}-modal" title="Move/Rename">{{! svg['copy'] }}</label>
      % if section == 'content' and it.name.endswith(view_ok):
        % if it.name.startswith('index.'):
          <a href="/{{ dirname }}{{ '/' if dirname else ''}}" target="_blank" title="View">{{! svg['eye'] }}</a>
        % else:
          <a href="/{{ dirname }}{{ '/' if dirname else ''}}{{ os.path.splitext(it.name)[0] }}/" target="_blank" title="View">{{! svg['eye'] }}</a>
        % end
      % elif section in ('content', 'static'):
        <a href="/{{ dirname }}{{ '/' if dirname else ''}}{{ it.name }}" target="_blank" title="View">{{! svg['eye'] }}</a>
      % end
    % elif typ == 'dir':
      <a href="{{ prefix }}/{{ current_path }}/{{ it.name }}" title="Open">{{! svg['arrow-right'] }}</a>
      % if not os.listdir(os.path.join(full_dirname, it.name)):
        <a href="/_/admin/rmdir/{{ current_path }}/{{ it.name }}" title="Remove folder">{{! svg['trash'] }}</a>
      % end
      <label role="link" class="d-inl" for="move-{{ fileid(it.name) }}-modal" title="Move/Rename">{{! svg['copy'] }}</label>
    % end
    </td>
  </tr>
  % end
</table>
</div>
% else:
<div class="admonition"><p>No files or subdirectories in this directory</p></div>
% end

% if paginated:
<div class="prevnext mt-2 mb-4 bg-contrast ta-c p-1">
  <div class="smaller">Page {{page}} of {{pagecount}} ({{entry_count}} files/directories{{ f' (out of a total of {total_entries})' if total_entries != entry_count else ''}})</div>
  <div>[<strong>
    % if page == 1:
    <span class="text-muted">« Previous</span>
    % else:
    <a href="./?p={{ page - 1}}{{ '&sort=date' if sort_by_date else '' }}{{ f'&search={search}' if search else '' }}">« Previous</a>
    % end
    |
    % if page == pagecount:
    <span class="text-muted">Next »</span>
    % else:
    <a href="./?p={{ page + 1}}{{ '&sort=date' if sort_by_date else '' }}{{ f'&search={search}' if search else '' }}">Next »</a>
    % end
    </strong>]</div>
</div>
% elif total_entries != entry_count:
<div class="prevnext mt-2 mb-4 bg-contrast ta-c p-1">
  <div class="smaller">Showing {{ entry_count }} entries (out of a total of {{ total_entries }} in this folder)</div>
</div>
% end

% for it in dir_entries:
  % if it.is_dir() or it.is_file():
    % include("rename-move-modal.tpl", section=section, dirname=dirname, is_dir=it.is_dir(), orig_name=it.name, directories=directories, fileid=fileid(it.name))
  % end
% end
