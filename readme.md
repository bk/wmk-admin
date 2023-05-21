# wmkAdmin

wmkAdmin is a simple admin system for websites built with [wmk].

## Getting started

1. Go to a wmk project directory
2. Clone this repository as a suitable subdirectory, e.g. `admin`.
3. Create a file called `wmk_admin.yaml` in the project directory. It must
   contain an `admin_password` value. (The password should preferably be hashed
   with SHA-256 but can be written as plaintext if desired).
4. Run either (a) `python admin/admin.py` ([Bottle] needs to be installed),
   or (b) `wmk admin .` (with wmk version 1.3.0 or greater).
5. Access the admin system on `http://localhost:7077/_/admin/` (or with the
   `host` and `port` configured in the `wmk_admin.yaml` file) and log in.

## TODO

Potential features and improvements in the future:

- Git interaction.
- Validate yaml and json before saving.
- Catch more errors and notify sensibly about them.
- View build logs.
- Deployment action (configurable in either `wmk_admin.yaml` or
  `wmk_config.yaml`).
- Manage `assets` directory in addition to the other three (?)

## License

The license is [MIT].

[wmk]: https://github.com/bk/wmk
[Bottle]: https://bottlepy.org/
[MIT]: https://opensource.org/license/mit/
