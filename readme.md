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

## License

The license is [MIT].

[wmk]: https://github.com/bk/wmk
[Bottle]: https://bottlepy.org/
[MIT]: https://opensource.org/license/mit/
