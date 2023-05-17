% rebase('base.tpl', title='Upload file')

<form action="/_/admin/upload/" enctype="multipart/form-data" method="POST">
  <div>Root folder:
    <select name="dest_dir">
    % for dir in dest_dirs:
      <option value="{{ dir }}">{{ dir }}/</option>
    % end
    </select>
  </div>
  <div>
    <label for="dest-name">Destination filename (leave blank to keep same name):</label>
    <input type="text" name="dest_name" id="dest-name">
  </div>
  <div>Upload file: <input type="file" name="upload"></div>
  <div><input type="submit" value="Start upload"></div>
</form>
