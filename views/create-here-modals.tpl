<p>
<label for="create-dir-modal" role="button" class="d-inl">{{! svg['folder-plus'] }} Create folder</label>
<label for="create-file-modal" role="button" class="d-inl">{{! svg['file-plus'] }} Create file</label>
<label for="upload-file-modal" role="button" class="d-inl">{{! svg['upload'] }} Upload file</label>
</p>

<div class="modal">
  <input id="create-dir-modal" type="checkbox" />
  <label for="create-dir-modal" class="overlay"></label>
  <article>
    <header>
      <label for="create-dir-modal" class="close">&times;</label>
      <h4>Create new folder</h4>
    </header>
    <p>Create a new folder inside the currently active one, <code>{{section}}/{{dirname}}</code>.</p>
    <form action="/_/admin/create-dir/{{ section }}/{{ dirname }}" method="POST">
      <label class="ta-l">Name of new folder:</label>
      <input type="text" name="new_dir">
      <input type="submit" class="d-inl" value="Create">
    </form>
  </article>
</div>

<div class="modal">
  <input id="create-file-modal" type="checkbox" />
  <label for="create-file-modal" class="overlay"></label>
  <article>
    <header>
      <label for="create-file-modal" class="close">&times;</label>
      <h4>Create new file</h4>
    </header>
    <p>Create a new file inside the currently active folder, <code>{{section}}/{{dirname}}</code>.</p>
    <form action="/_/admin/create-file/{{ section }}/{{ dirname }}" method="POST">
      <label class="ta-l">Name of new file:</label>
      <input type="text" name="new_filename">
      <input type="submit" class="d-inl" value="Create">
      <p class="smaller">
        <strong>Note:</strong>
        The file will initially be empty, but you can Edit it after creation
        to add content.
      </p>
    </form>
  </article>
</div>

<div class="modal">
  <input id="upload-file-modal" type="checkbox" />
  <label for="upload-file-modal" class="overlay"></label>
  <article>
    <header>
      <label for="upload-file-modal" class="close">&times;</label>
      <h4>Upload file</h4>
    </header>
    <p>The file will be placed inside the currently active folder, <code>{{section}}/{{dirname}}</code>.</p>
    <form action="/_/admin/upload/" enctype="multipart/form-data" method="POST">
      <input type="hidden" name="dest_dir" value="{{ section }}{{ '/' if dirname else '' }}{{ dirname }}">
      <label for="dest-name" class="ta-l">Destination filename (optional):</label>
      <input type="text" name="dest_name" id="dest-name">
      <div class="smaller">Leave blank for automatic name based on original filename</div>
      <label class="ta-l">Upload file:</label>
      <input type="file" name="upload">
      <input type="submit" value="Start upload">
    </form>
  </article>
</div>
