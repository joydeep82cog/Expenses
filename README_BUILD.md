# How to Build the Android APK

This repository now includes all Android build files:

- `buildozer.spec`
- `build_apk_wsl.sh`
- `.github/workflows/android-apk.yml`

## Option 1 - GitHub Actions (Recommended)

1. Push to your GitHub repository.
2. Open the Actions tab for your repository.
3. Run or wait for the `Build Android APK` workflow.
4. Download the `TrackYourExpense-debug-apk` artifact.
5. Extract and install the `.apk` file on Android.

## Option 2 - WSL2 Local Build

Use Ubuntu in WSL2 and run:

```bash
cd /mnt/e/Joydeep/MyApps/Expenses
chmod +x build_apk_wsl.sh
./build_apk_wsl.sh
```

Output APK location:

```bash
bin/*.apk
```

## Build Notes

- First build can take a long time because SDK/NDK/toolchains are downloaded.
- This project uses `openpyxl` for Excel operations to keep Android packaging simpler.
- `matplotlib` charts are optional at runtime. If unavailable in a build, the app still runs and shows a fallback message instead of a chart.
- For release builds, use `buildozer android release` and sign the APK/AAB with your keystore.
