% rebase('base.tpl', with_ace=True, title='Edit ' + (section or '') + ' file: '+filename)

% import os
% ext = os.path.splitext(filename)[1][1:]
% content_exts = editable_exts[:18]
% view_url = None
% is_index = os.path.basename(filename).startswith('index.')
% if ext in content_exts and section == 'content':
  % view_url = '/' + (os.path.dirname(filename) if is_index else filename[:-(len(ext)+1)]) + '/'
  % view_url = view_url.replace('//', '/')
% end

<hgroup>
  <h2>Edit file</h2>
% if is_config:
  <p><strong>Editing site configuration file:</strong> <code>{{ filename }}</code></p>
% else:
  <p>
    <strong>Editing:</strong> <code>{{ section }}/{{ filename }}</code>
  % if view_url:
    &ndash; <a href="{{ view_url }}" target="_blank">View</a>
  % end
  </p>
% end
</hgroup>

% form_action = 'edit-config/' if is_config else 'edit/%s/%s' % (section, filename)

<form action="/_/admin/{{ form_action }}" method="POST">
  <div id="ace-editor" class="mb-1 ba-1" style="height:596px;max-height:80vh">{{ contents }}</div>
  <div><textarea rows="20" cols="80" id="file-contents" name="contents" style="display:none">{{ contents }}</textarea></div>
  <div><input type="submit" value="Save"></div>
</form>
<script src="/_/js/ace/ace.js"></script>
<script src="/_/js/ace/theme-textmate.js"></script>
<script src="/_/js/ace/theme-github_dark.js"></script>
<script src="/_/js/ace/mode-markdown.js"></script>
% if ext in ace_modes:
<script src="/_/js/ace/mode-{{ ace_modes[ext] }}.js"></script>
% end
<script>
var editor = ace.edit('ace-editor');
var textarea = document.getElementById('file-contents');
editor.getSession().on("change", function () {
    textarea.value = editor.getSession().getValue();
});
if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    // dark mode
    editor.setTheme('ace/theme/github_dark');
} else {
    editor.setTheme('ace/theme/textmate');
}
editor.setFontSize(14);
editor.setOption("wrap", true);
editor.setOption("showFoldWidgets", false);
editor.setOption("showPrintMargin", false);
% if ext in ace_modes:
editor.session.setMode("ace/mode/{{ ace_modes[ext] }}");
% end
</script>
