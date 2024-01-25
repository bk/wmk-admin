# wmkAdmin

wmkAdmin is a simple admin system for websites built with [wmk].
It requires wmk v1.3.0 or later.

## Getting started

1. Go to a wmk project directory

2. Clone this repository as a suitable subdirectory, e.g. `admin`.

3. Create a file called `wmk_admin.yaml` in the project directory. It must
   contain an `admin_password` value. (The password should preferably be hashed
   with SHA-256 but can be written as plaintext if desired).

4. Run `wmk admin .` (with wmk version 1.3.0 or greater). Alternatively,
   run `python admin/admin.py` after having loaded the wmk venv (or otherwise
   made all required python modules available).

5. Access the admin system on `http://localhost:7077/_/admin/` (or with the
   `host` and `port` configured in the `wmk_admin.yaml` file) and log in.

## Settings in `wmk_admin.yaml`

The following settings are currently supported:

- `admin_password`: The SHA-256 sum of the password to the admin pages, in
  hexadecimal form. (There is no distinction between different users, so only a
  password is needed.)

- `host`: The host or IP for the admin server. Default: `localhost`.

- `port`: The port for the admin server: Default: 7077.

- `server`: The wsgi server to use. The default is wsgiref, but something else
  is recommended for any kind of heavy use. Good options are `bjoern`, `cheroot`
  and `paste`.

- `deploy`: A shell command to run from the base directory of the project.
  The intention if for this to deploy any changes to the webserver where
  the published site is running, but obviously it can be used for other purposes
  as well. The command will be passed to `subprocess.run()`, so if it has
  arguments, it should be specified as a list rather than as a string.

- `auto_metadata`: Which metadata fields to add automatically to the YAML
  frontmatter when saving files with a given extension. Example: `auto_metadata:
  {'md': ['modified_date', 'created_date']}`. The field `modified_date` will be
  updated on each save, while other fields will only be added if missing.
  Supported fields: `date`, `created_date`, `modified_date`. Take care that
  you only specify the extensions for file formats that support YAML
  frontmatter.

- `preview_css`: CSS source (not URL) to use for the *Quick preview*
  function on the Edit page.

- `img_to_editor_template` and `attachment_to_editor_template`: Content for
  javascript string templates for adding images or links to attachments into
  markdown text when clicking on the appropriate links in the file list below
  the editor. The string `{src}` indicates the placement of the image src or
  link href value.

- `show_admin_overlay`: By default, the preview of the website includes a
  prominent overlay in the bottom-right corner of each page, with a link to the
  admin frontpage as well as to an editing form for the current page (if
  applicable). This can be turned off by setting `show_admin_overlay` to `false`.
  The overlay can also be set to be visible only to a logged-in user by setting
  the value of this key to either `logged-in` or `admin`.

- `recently_changed`: A dictionary with settings for the "Recently changed
  files" component, which is an optional part of the admin front page. The
  dictionary should have at least the key `type` (which must have a value of
  either `git` or `find`). It can optionally have the keys `days_back` (default:
  30), `dirs` (default `['content', 'data', 'templates', 'static']`),
  `extensions` (default: all editatble extensions), and `limit` (default: 20).

All `wmk_admin.yaml` settings except `admin_password` are optional.

## TODO

Potential features and improvements in the future:

- Improved Git interaction.
- Validate yaml and json before saving.
- Catch more errors and notify sensibly about them.
- View build logs.
- Manage `assets` directory in addition to the other three (?)

## License

The license is [MIT].

[wmk]: https://github.com/bk/wmk
[Bottle]: https://bottlepy.org/
[MIT]: https://opensource.org/license/mit/
