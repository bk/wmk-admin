% import datetime
% htdir = attachment_dir.replace('content', '', 1) or '/'

<div id="att-container-inner" class="ba-1 mt-2 mb-2 p-2 bg-accent borad">
  <hgroup>
    <h3>Images and attachments</h3>
    <p>Files which will end up in the same destination <a href="/_/admin/list/{{ attachment_dir }}" target="_blank">folder</a> as the document being edited – newest at top.</p>
  </hgroup>
  % if msg:
  <div class="admonition success bg-contrast">{{ msg }}</div>
  % end
  % if files:
  <div class="x-scroll">
  <table>
    <tr>
      <th>Name</th>
      <th class="ta-r">Size</th>
      <th>Date</th>
    </tr>
    % for file in files:
    %  stat = file.stat()
    <tr>
      <td><a href="{{ htdir }}/{{ file.name }}" target="_blank" class="plain">{{ file.name }}</a></td>
      <td class="ta-r">{{ stat.st_size }}</td>
      <td>{{ str(datetime.datetime.fromtimestamp(stat.st_mtime))[:16] }}</td>
    </tr>
    % end
  </table>
  </div>
  % else:
    <p><em>No image/attachment files are yet present</em></p>
  % end
  <p><label>Upload new image/attachment:</label></p>
  <div class="grid-sm">
    <input type="file" name="upload" id="upload" class="m-0">
    <button onclick="submit_attachment_upload()" id="start-upload" style="d-inl" class="m-0">Upload</button>
  </div>
</div>
