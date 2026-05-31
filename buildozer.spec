[app]

title = Track Your Expense
package.name = trackyourexpense
package.domain = org.joydeep

source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,webp,xlsx
source.include_patterns = Trip Archive/*.xlsx
source.exclude_dirs = .git,.venv,.venv-py314-backup,__pycache__,unit test
source.exclude_exts = pyc,pyo,log

version = 1.0.0

requirements = python3,kivy==2.3.1,openpyxl

presplash.filename = presplash.png
icon.filename = icon.png

orientation = portrait
fullscreen = 0

android.api = 34
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True

# Keep app data private and writable across Android versions.
android.storage = app

[buildozer]
log_level = 2
warn_on_root = 1
