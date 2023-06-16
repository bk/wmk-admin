% is_in_content = (section and section == 'content')

<div class="mt-2 mb-2">
  <label for="create-dir-modal" role="button" class="d-inl">{{! svg['folder-plus'] }} Create folder</label>
  <label for="create-file-modal" role="button" class="d-inl">{{! svg['file-plus'] }} {{ 'New page' if is_in_content else 'New file' }}</label>
  <label for="upload-file-modal" role="button" class="d-inl">{{! svg['upload'] }} Upload file</label>
  <form class="d-inl" action="" method="GET">
    <input type="hidden" name="sort" value="{{ 'date' if sort_by_date else 'name' }}">
    <input type="text" class="d-inl m-0" size="12" name="search" value="{{ search if search else '' }}" placeholder="Search">
  </form>
</div>

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
      <h4>Create new {{ '...' if is_in_content else 'file' }}</h4>
    </header>
    % if is_in_content:
      <div class="tabs ta-l">
        <input type="radio" name="tabgroup" id="tab1" checked>
        <label for="tab1">Page</label>
        <input type="radio" name="tabgroup" id="tab2">
        <label for="tab2">File</label>
        <div class="pane pane1">
          <p>Create a new page in the currently active folder, <code>{{section}}/{{dirname}}</code>.</p>
            <form action="/_/admin/create-page/{{ section }}/{{ dirname }}" method="POST">
              <label>Title of new page:</label>
              <input type="text" name="title" required>
              <input type="submit" class="d-inl" value="Create">
              <p class="smaller ta-c">
                The editing form for the new page will automatically be opened.
              </p>
            </form>
        </div>
        <div class="pane pane2">
          <p>Create a new file inside the currently active folder, <code>{{section}}/{{dirname}}</code>.</p>
            <form action="/_/admin/create-file/{{ section }}/{{ dirname }}" method="POST">
              <label>Filename of new file:</label>
              <input type="text" name="new_filename">
              <input type="submit" class="d-inl" value="Create">
              <p class="smaller ta-c">
                <strong>Note:</strong>
                The file will initially be empty, but you can Edit it after creation
                to add content.
              </p>
            </form>
        </div>
      </div>
    % else:
      <p>Create a new file inside the currently active folder, <code>{{section}}/{{dirname}}</code>.</p>
      <form action="/_/admin/create-file/{{ section }}/{{ dirname }}" method="POST">
        <label>Filename of new file:</label>
        <input type="text" name="new_filename">
        <input type="submit" class="d-inl" value="Create">
        <p class="smaller ta-c">
          <strong>Note:</strong>
          The file will initially be empty, but you can Edit it after creation
          to add content.
        </p>
      </form>
    % end
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
