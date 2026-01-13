# Changelog

## [2026.01.12] - 2026-01-12

### 🚀 New Features
- **Rebranding:** Renamed add-on to **Smart Captcha Solver**.
- **Native Implementation:** Completely rewrote the core logic using standard Python libraries (`urllib`). Removed **all** external dependencies and `pip` usage.
- **Smart Context Capture:** Updated screen capture logic to grab the **entire foreground window** instead of just the focused object. This allows Gemini to see the captcha instructions, grid, and buttons simultaneously.
- **Grid Captcha Support:** Optimized Gemini prompts to correctly identify and solve 3x3 and 4x4 grid captchas (e.g., hCaptcha, reCAPTCHA), returning image numbers (e.g., "1, 5, 9").
- **Gemini Flash:** Switched to `gemini-flash-latest` model for faster response times.
- **Timeout Handling:** Increased API timeout to 60 seconds to prevent "Read Operation Timed Out" errors on slower connections.

### 🧹 Improvements
- **Zero Comments:** Cleaned source code by removing all comments and legacy code blocks.
- **Documentation:** Created a comprehensive `README.md` for GitHub and a simplified User Guide in `docs/`.
- **Build System:** Simplified `build_linux.sh` to a pure packaging script (no downloads required).

### 🐛 Fixes
- Fixed `ModuleNotFoundError` for Google libraries by switching to native implementation.
- Fixed `HTTP 404` errors by using the correct Gemini model alias.
- Fixed accuracy issues where Gemini couldn't see the grid or instructions.
