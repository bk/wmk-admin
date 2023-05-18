<p>
<label for="create-dir-modal" role="button" class="d-inl">Create directory here</label>
<label for="create-file-modal" role="button" class="d-inl">Create new file here</label>
</p>

<div class="modal">
  <input id="create-dir-modal" type="checkbox" />
  <label for="create-dir-modal" class="overlay"></label>
  <article>
    <header>
      <label for="create-dir-modal" class="close">&times;</label>
      <h4>Create new directory</h4>
    </header>
    <form action="/_/admin/create-dir/{{ section }}/{{ dirname }}" method="POST">
      <label class="">Name of new directory to create in <code>{{section}}/{{dirname}}</code></label>
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
    <form action="/_/admin/create-file/{{ section }}/{{ dirname }}" method="POST">
      <label class="">Name of new file to create in <code>{{section}}/{{dirname}}</code></label>
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
