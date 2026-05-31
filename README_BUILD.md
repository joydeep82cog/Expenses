# 📱 How to Build the Android APK

## Option 1 – GitHub Actions (Recommended, easiest – no Linux needed)

> Build happens in the cloud for free. You just download the finished APK.

### Steps

1. **Create a GitHub repository** (free account at https://github.com)

2. **Push this project folder to your repo:**
   ```powershell
   cd "c:\Joydeep\Learnings\GenAI\Myapps\Expenses\reference"
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

3. **GitHub Actions will automatically start building** when you push.  
   Go to: `https://github.com/YOUR_USERNAME/YOUR_REPO/actions`

4. **Download the APK:**  
   - Click the latest workflow run  
   - Scroll to **Artifacts**  
   - Download **TrackYourExpense-debug-apk**  
   - Extract the zip → you'll find `trackyourexpense-*.apk`

5. **Install on Android:**  
   - Copy the APK to your phone  
   - Enable **"Install from unknown sources"** in Settings → Security  
   - Tap the APK file to install

---

## Option 2 – WSL2 on Windows (Local build)

> Requires WSL2 with Ubuntu installed. First build takes ~20-30 minutes.

### Steps

1. **Install WSL2** (if not already):
   ```powershell
   wsl --install -d Ubuntu-22.04
   ```

2. **Open Ubuntu in WSL2**, navigate to the project:
   ```bash
   cd /mnt/c/Joydeep/Learnings/GenAI/Myapps/Expenses/reference
   chmod +x build_apk_wsl.sh
   ./build_apk_wsl.sh
   ```

3. The APK will appear in the `bin/` folder.

4. Copy to your phone and install (same as step 5 above).

---

## Option 3 – Google Colab (Free, browser-based)

1. Go to https://colab.research.google.com
2. Create a new notebook and run:

```python
# Install buildozer
!pip install buildozer cython==0.29.37

# Install system deps
!apt-get install -y git zip unzip openjdk-17-jdk autoconf libtool \
    pkg-config zlib1g-dev libncurses5-dev libffi-dev libssl-dev

# Upload your project files using the Files panel on the left,
# then run buildozer from that directory:
import os
os.chdir('/content/reference')  # adjust path
!buildozer -v android debug
```

3. Download the APK from the `bin/` folder in Colab's file browser.

---

## Notes

- **First build** downloads Android SDK/NDK (~2 GB) – subsequent builds are faster due to caching.
- The APK produced is a **debug APK** – suitable for personal use and testing.
- For a **release APK** (for Play Store), change `android debug` to `android release` in the build command and sign it with a keystore.
- The `Trip Archive/` folder on Android will be stored in the app's private storage directory.
