% import os

% modal_id = 'move-' + fileid + '-modal'
% typ_name = 'folder' if is_dir else 'file'
% from_dir = os.path.join(section, dirname) if dirname else section

<div class="modal">
  <input id="{{ modal_id }}" type="checkbox" />
  <label for="{{ modal_id }}" class="overlay"></label>
  <article>
    <header>
      <label for="{{ modal_id }}" class="close">&times;</label>
      <h4>Rename or move {{ typ_name }}</h4>
    </header>
    <div class="ta-l">
      <p class="smaller">If you want to rename the {{ typ_name }} but keep it in the same place, just edit the name. Conversely, if you want to move it to a new location but not change the name, just pick the destination folder before pressing the Rename/Move button.</p>
      <p><strong>Original name:</strong> {{ orig_name }}</p>
      <form action="/_/admin/move/" method="POST">
        <input type="hidden" name="from_dir" value="{{ from_dir }}">
        <input type="hidden" name="orig_name" value="{{ orig_name }}">
        <input type="hidden" name="is_dir" value="{{ '1' if is_dir else '0' }}">
        <label>New name</label>
        <input type="text" name="new_name" value="{{ orig_name }}">
        <label>Destination folder</label>
        <select name="dest_dir">
          % for d in directories:
            <option value="{{ d }}"{{ ' selected' if d == from_dir else '' }}>{{ d }}</option>
          % end
        </select>
        <input type="submit" value="Rename/Move">
      </form>
    </div>
  </article>
</div>
