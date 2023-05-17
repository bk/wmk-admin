% rebase('base.tpl', title='Edit ' + section + ' file: '+filename)

<form action="/_/admin/edit/{{ section }}/{{ filename }}" method="POST">
  <p>Filename: {{ filename }}</p>
  <div><label for="file-contents">File contents</label></div>
  <div><textarea rows="20" cols="80" id="file-contents" name="contents">{{ contents }}</textarea></div>
  <div><input type="submit" value="Save"></div>
</form>
