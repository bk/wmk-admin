% rebase('base.tpl', title='Edit ' + (section or '') + ' file: '+filename)

<hgroup>
  <h2>Edit file</h2>
% if is_config:
  <p><strong>Editing site configuration file:</strong> <code>{{ filename }}</code></p>
% else:
  <p><strong>Editing:</strong> <code>{{ section }}/{{ filename }}</code></p>
% end
</hgroup>

% form_action = 'edit-config/' if is_config else 'edit/%s/%s' % (section, filename)

<form action="/_/admin/{{ form_action }}" method="POST">
  <div><label for="file-contents">File contents</label></div>
  <div><textarea rows="20" cols="80" id="file-contents" name="contents">{{ contents }}</textarea></div>
  <div><input type="submit" value="Save"></div>
</form>
