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

- `password`: The SHA-256 sum of the password to the admin pages, in hexadecimal
  form. (There is no distinction between different users, so only a password is
  needed.)

- `host`: The host or IP for the admin server. Default: `localhost`.

- `port`: The port for the admin server: Default: 7077.

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

All settings except `password` are optional.

## TODO

Potential features and improvements in the future:

- Git interaction.
- Validate yaml and json before saving.
- Catch more errors and notify sensibly about them.
- View build logs.
- Manage `assets` directory in addition to the other three (?)

## License

The license is [MIT].

[wmk]: https://github.com/bk/wmk
[Bottle]: https://bottlepy.org/
[MIT]: https://opensource.org/license/mit/
