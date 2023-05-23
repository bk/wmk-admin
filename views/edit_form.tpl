% rebase('base.tpl', with_ace=True, title='Edit ' + (section or '') + ' file: '+filename)

% import os, re
% ext = os.path.splitext(filename)[1][1:]
% content_exts = editable_exts[:18]
% view_url = None
% is_index = os.path.basename(filename).startswith('index.')
% preview_base = re.sub(r'^\.\w+$', '.html', filename) if 'index.' in filename else os.path.splitext(filename)[0] + '/'
% preview_base = re.sub(r'/index.html$', '/', preview_base)
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
    &ndash; <a href="{{ view_url }}" target="_blank">View on site</a>
  % end
  </p>
% end
</hgroup>

% if flash_message:
  <div class="admonition success">
    <p class="admonition-title">Success</p>
    <p>{{ flash_message }}</p>
  </div>
% end

% form_action = 'edit-config/' if is_config else 'edit/%s/%s' % (section, filename)

<form action="/_/admin/{{ form_action }}" method="POST">
  <div id="ace-editor" class="mb-1 ba-1" style="height:596px;max-height:80vh">{{ contents }}</div>
  <div><textarea rows="20" cols="80" id="file-contents" name="contents" style="display:none">{{ contents }}</textarea></div>
  % if filename.endswith(content_exts):
  <div class="grid-sm">
    <a href="#" onclick="return show_preview()">Preview text</a>
    <input type="submit" name="save_and_edit" value="Save and keep editing">
    <input type="submit" name="save_and_close" value="Save and close">
  </div>
  % else:
  <div><input type="submit" value="Save"></div>
  % end
</form>


% if filename.endswith(content_exts):
  % if preview_css:
  <style type="text/css">
    {{! preview_css }}
  </style>
  % end
  <base href="/{{ preview_base }}" />
  <div class="modal">
    <input id="preview-modal" type="checkbox" />
    <label for="preview-modal" class="overlay"></label>
    <article>
      <header>
        <label for="preview-modal" class="close">&times;</label>
        <h4>Preview <code>{{ filename }}</code></h4>
      </header>
      <div class="ta-l" id="preview"></div>
      <footer>
        <p class="p-2 smaller">
          <strong>Note:</strong> The preview only shows the HTML output of the conversion process, not the final page.
          Therefore the appearance will be different.
        </p>
      </footer>
    </article>
  </div>
% end

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
var need_preview = true;
editor.getSession().on("change", function () {
  textarea.value = editor.getSession().getValue();
  have_preview = false;
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

async function get_preview(source) {
  const form_data = new FormData();
  form_data.append("source", source);
  form_data.append("filename", "{{ filename }}");
  const response = await fetch('/_/admin/preview/', {
    method: "POST",
    mode: "same-origin",
    cache: "no-cache",
    body: form_data,
  });
  const ret = await response.blob();
  return ret.text();
}

function show_preview() {
  if (! need_preview) {
    document.getElementById('preview-modal').checked = true;
    return false;
  }
  source = textarea.value;
  get_preview(source).then((data) => {
    // console.log(data);
    document.getElementById('preview').innerHTML = data;
    document.getElementById('preview-modal').checked = true;
    need_preview = false;
  });
  return false;
}
</script>
