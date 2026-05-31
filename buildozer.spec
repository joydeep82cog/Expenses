[app]
title = TrackYourExpense
package.name = trackyourexpense
package.domain = org.joydeep82cog.expenses
source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,xlsx
source.exclude_dirs = .git,.venv,__pycache__,unit test
version = 1.0.0
requirements = python3,kivy,pandas,openpyxl,matplotlib
orientation = portrait
fullscreen = 0
icon.filename = icon.png
presplash.filename = presplash.png

# Android settings
android.api = 34
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
