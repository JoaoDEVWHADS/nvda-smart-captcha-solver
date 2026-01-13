# Smart Captcha Solver for NVDA 🧠🚀

**Smart Captcha Solver** is an advanced NVDA add-on that empowers visually impaired users to instantly solve **Visual** and **Grid-based** Captchas (like reCAPTCHA and hCaptcha) using the power of **Google Gemini AI**.

> **Note:** This add-on requires a free Google Gemini API Key.

---

## 🌟 Features

### ⚡ Instant Analysis
- **Smart Context Capture:** Automatically scans the entire active window to understand the full context (instructions + grid + buttons).
- **Zero Latency:** Optimized with `Gemini Flash` for lightning-fast responses.

### 🧩 Advanced Captcha Support
- **Grid Challenges (hCaptcha/reCAPTCHA):** Identifies specific images in 3x3 or 4x4 grids.
    - *Example Output:* "Select cars: 2, 4, 6"
- **Visual Description:** Describes standalone images or reads obscured text with high accuracy.
- **Audio Feedback:** Spoken results directly through NVDA's speech synthesizer.

### 🛠️ Native & Lightweight
- **Zero External Dependencies:** Built with pure Python standard libraries (`urllib`).
- **No Pip Required:** Just install and use. No complex setup or downloads.

---

## 📥 Installation

1. Go to the [Releases Page](https://github.com/JoaoDEVWHADS/nvda-smart-captcha-solver/releases).
2. Download the latest `smartCaptchaSolver.nvda-addon` file.
3. Open the file and follow the NVDA prompts to install.
4. **Restart NVDA** to finish the installation.

---

## ⚙️ Configuration

Before using the add-on, you need to configure your API Key.

### 🔑 Getting an API Key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey).
2. Sign in with your Google account.
3. Click on **Create API Key**.

### 🛠️ Setting up in NVDA
1. Open the **NVDA Menu** (`Insert + N`).
2. Navigate to **Preferences** -> **Settings**.
3. In the categories list, select **Captcha Solver**.
4. Paste your **API Key** into the text field.
5. Click **OK** to save.

---

## 🚀 Usage

Using the add-on is extremely simple.

### 1. Locate the Captcha
Navigate to the webpage containing the captcha. Ensure the captcha challenge (images and instructions) is visible on your screen.

### 2. Activate the Solver
Press the magic shortcut:
> **Shortcut:** `Ctrl + NVDA + H`

### 3. Listen to the Solution
NVDA will announce: *"Analyzing captcha..."*.
Wait a few seconds, and the AI will speak the solution, for example:
> *"Solution: The traffic lights are in images 1, 5 and 9."*

---

## 🏗️ Building from Source

If you want to modify or package the add-on yourself:

### Prerequisites
- Linux environment (WSL or Native)
- Basic tools: `zip`, `gettext`

### One-Click Build
Run the automated build script:
```bash
./build_linux.sh
```
This will generate the `smartCaptchaSolver.nvda-addon` file ready for installation.

---

## 👨‍💻 Author & Credits

**Author:** [JoaoDEVWHADS](https://github.com/JoaoDEVWHADS)
**Version:** 2026.01.12
**License:** MIT

_Empowering accessibility with Artificial Intelligence._
