import globalPluginHandler
import scriptHandler
import api
import ui
import wx
import config
import struct
import io
import json
import threading
import base64
import sys
import os
import urllib.request
import urllib.error
from gui import guiHelper
from gui.settingsDialogs import SettingsPanel, NVDASettingsDialog
import addonHandler
import logHandler

addonHandler.initTranslation()

CONF_SECTION = "captchaSolver"
CONF_KEY_API_KEY = "geminiApiKey"

class CaptchaSolverSettingsPanel(SettingsPanel):
	title = _("Captcha Solver")

	def makeSettings(self, settingsSizer):
		sHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		
		self.apiKeyEdit = sHelper.addLabeledControl(
			_("Google Gemini API Key:"),
			wx.TextCtrl,
		)
		try:
			current_key = config.conf[CONF_SECTION][CONF_KEY_API_KEY]
			self.apiKeyEdit.SetValue(current_key)
		except KeyError:
			pass

	def onSave(self):
		if CONF_SECTION not in config.conf:
			config.conf[CONF_SECTION] = {}
		
		config.conf[CONF_SECTION][CONF_KEY_API_KEY] = self.apiKeyEdit.GetValue()

class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	def __init__(self):
		super(GlobalPlugin, self).__init__()
		NVDASettingsDialog.categoryClasses.append(CaptchaSolverSettingsPanel)

	def terminate(self):
		super(GlobalPlugin, self).terminate()
		if CaptchaSolverSettingsPanel in NVDASettingsDialog.categoryClasses:
			NVDASettingsDialog.categoryClasses.remove(CaptchaSolverSettingsPanel)

	def script_solveCaptcha(self, gesture):
		focus = api.getFocusObject()
		
		api_key = ""
		try:
			api_key = config.conf[CONF_SECTION][CONF_KEY_API_KEY]
		except KeyError:
			ui.message(_("Please configure the Gemini API Key in NVDA Settings."))
			return

		if not api_key:
			ui.message(_("Please configure the Gemini API Key in NVDA Settings."))
			return

		nav_obj = api.getForegroundObject()
		
		try:
			left, top, width, height = nav_obj.location
		except Exception:
			ui.message(_("Could not determine location of the active window."))
			return

		if width <= 0 or height <= 0:
			ui.message(_("Window has no visible dimensions."))
			return

		bmp = wx.Bitmap(width, height)
		mem_dc = wx.MemoryDC(bmp)
		screen_dc = wx.ScreenDC()
		
		mem_dc.Blit(0, 0, width, height, screen_dc, left, top)
		mem_dc.SelectObject(wx.NullBitmap)
		
		img_data = io.BytesIO()
		img = bmp.ConvertToImage()
		img.SaveFile(img_data, wx.BITMAP_TYPE_PNG)
		png_bytes = img_data.getvalue()
		
		t = threading.Thread(target=self._queryGemini, args=(png_bytes, api_key))
		t.start()
		ui.message(_("Analyzing captcha..."))

	def _queryGemini(self, image_bytes, api_key):
		try:
			b64_image = base64.b64encode(image_bytes).decode('utf-8')

			url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
			
			prompt_text = (
				"You are a captcha solving assistant for a blind user. "
				"The image usually contains a captcha challenge with a 3x3 or 4x4 grid. "
				"1. Read the instructions (e.g. 'Select all images with cars'). "
				"2. Analyze the grid numbering from 1 to 9 (left-to-right, top-to-bottom). "
				"3. Return ONLY the numbers of the images that match. "
				"Example output: '2, 4, 6'. "
				"If it represents text, output the characters. "
				"Keep it extremely concise."
			)

			payload = {
				"contents": [{
					"parts": [
						{"text": prompt_text},
						{
							"inline_data": {
								"mime_type": "image/png",
								"data": b64_image
							}
						}
					]
				}]
			}
			
			data = json.dumps(payload).encode('utf-8')
			
			req = urllib.request.Request(
				url, 
				data=data, 
				headers={'Content-Type': 'application/json'}
			)

			with urllib.request.urlopen(req, timeout=60) as response:
				response_body = response.read().decode('utf-8')
				result = json.loads(response_body)
				
				try:
					answer = result['candidates'][0]['content']['parts'][0]['text']
					if answer:
						wx.CallAfter(ui.message, _("Captcha solution: ") + answer)
					else:
						wx.CallAfter(ui.message, _("Gemini returned no answer."))
				except (KeyError, IndexError):
					wx.CallAfter(ui.message, _("Could not parse Gemini response."))
					logHandler.log.error("CaptchaSolver: Raw response: " + response_body)

		except urllib.error.HTTPError as e:
			err_msg = _("API Error: ") + str(e.code)
			try:
				err_body = e.read().decode('utf-8')
				logHandler.log.error("CaptchaSolver: API Error Body: " + err_body)
			except:
				pass
			wx.CallAfter(ui.message, err_msg)
		except Exception as e:
			logHandler.log.error("CaptchaSolver: Error query: " + str(e))
			wx.CallAfter(ui.message, _("Error solving captcha: ") + str(e))

	__gestures = {
		"kb:control+NVDA+h": "solveCaptcha",
	}

