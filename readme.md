# wmkAdmin

wmkAdmin is a simple admin system for websites built with [wmk].

## Getting started

1. Go to a wmk project directory
2. Clone this repository as a suitable subdirectory, e.g. `admin`.
3. Create a file called `wmk_admin.yaml` in the project directory. It must
   contain an `admin_password` value. (The password should preferably be hashed
   with SHA-256 but can be written as plaintext if desired).
4. Run `python admin/admin.py`. ([Bottle] needs to be installed).
5. Access the admin system on `http://localhost:7077/_/admin/` and log in.

## TODO

Potential features and improvements in the future:

- Make a few things configurable in `wmk_admin.yaml` (beyond just the password).
- Accept command-line arguments for such things as IP address and port.
- Git interaction.
- Integrate better with wmk.
- Preview editing changes before saving.
- Validate yaml and json before saving.
- Catch more errors and notify sensibly about them.
- View build logs.
- Deployment action (configurable in `wmk_admin.yaml`).
- Rebuild site on login (?)
- Work with `assets` directory in addition to the other three (?)

## License

The license is [MIT].

[wmk]: https://github.com/bk/wmk
[Bottle]: https://bottlepy.org/
[MIT]: https://opensource.org/license/mit/
