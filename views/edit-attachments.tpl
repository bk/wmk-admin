% from PIL import Image
% import datetime
% is_image = lambda nam: nam.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))
% htdir = attachment_dir.replace('content', '', 1) or '/'
<%
def imsiz(f):
    with Image.open(f.path) as im:
        return im.size
%>

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
      <th>Insert</th>
    </tr>
    % for file in files:
    %  stat = file.stat()
    <tr>
      <td>
        % if is_image(file.name):
        <img src="{{ htdir }}/{{ file.name }}" loading="lazy" width="80" alt="preview">
        % end
        <a href="{{ htdir }}/{{ file.name }}" target="_blank" class="plain">{{ file.name }}</a>
      </td>
      <td class="ta-r">
        {{ stat.st_size }}
        % if is_image(file.name):
        <br>({{ '%dx%d' % imsiz(file) }})
        % end
      </td>
      <td>{{ str(datetime.datetime.fromtimestamp(stat.st_mtime))[:16] }}</td>
      <td>
        % if file.name.lower().endswith(img_exts):
        <a href="#" onclick="return img_to_editor('{{file.name}}')" class="plain">image</a>
        % elif file.name.lower().endswith(att_exts):
        <a href="#" onclick="return attachment_to_editor('{{file.name}}')" class="plain">link</a>
        % end
      </td>
    </tr>
    % end
  </table>
  </div>
  % else:
    <p><em>No image/attachment files are yet present</em></p>
  % end
  <p><label>Upload new images or attachments:</label></p>
  <div class="grid-sm">
    <input type="file" name="upload" id="upload" multiple class="m-0">
    <button onclick="submit_attachment_upload()" id="start-upload" style="d-inl" class="m-0">Upload</button>
  </div>
</div>
