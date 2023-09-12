from PIL import Image, ImageTk
import tkinter as tk
import win32gui
import time
import random
import threading
from ctypes import windll, wintypes, WINFUNCTYPE, byref
import pygetwindow as gw

isExiting = False
verbose = 5
# 0 = no verbose
# 1 = basic info
# 2 = + hooks
# 3 = + function triggers
# 4 = + idk
# 5 = everything

### MAIN WINDOW
class App(tk.Tk):
	def __init__(self):
		tk.Tk.__init__(self)

		self.title("pneko")
		# self.iconbitmap('pneko.ico')
		# self.geometry("32x32")
		self.overrideredirect(True) # borderless
		self.wm_attributes("-toolwindow", True) # no taskbar icon
		self.wait_visibility(self) # wait for window to be visible
		self.wm_attributes('-transparentcolor', self['bg']) # click-through
		self.attributes('-topmost', True)
		# self.call('wm', 'attributes', '.', '-topmost', '1') # always on top
		# needs to be re-called on minimize/maximize
  
		self.hwnd = int(self.frame(), 16)
		self.state = 1
			#  1 = idle
			#  2 = window change
			#  3 = sleeping
			#  4 = action
		self.activeWindowID = 0
		self.animation = "idle"
			## [ "idle", "sleep", "idle2", "idle3", "run" ]

		self.spritesheet = Image.open("neko_spritesheet.png")
		self.sprite_width = 32
		self.sprite_height = 32
		self.spr_cols = 4
		self.spr_rows = 5
		self.images = [ self.subimage(c*self.sprite_width, r*self.sprite_height,
						(c+1)*self.sprite_width, (r+1)*self.sprite_height)
						for r in range(self.spr_rows)
						for c in range(self.spr_cols) ]
					   
		self.canvas = tk.Canvas(self, width=self.sprite_width, height=self.sprite_height)
		self.canvas.pack()
		self.last_img = self.canvas.create_image(self.sprite_width/2, self.sprite_height/2, image=None)

		self.canvas.bind("<Button-2>", self.close_window)
		self.canvas.bind("<B1-Motion>", self.move)
		threading.Thread(target=nekoLogic).start()
		self.after(500, self.transportCheck)

	def subimage(self, l, t, r, b):
		return ImageTk.PhotoImage(self.spritesheet.crop((l, t, r, b)))

	def updateImage(self, sprite, action, force=False):
		''' updates canvas image '''
		if verbose > 2: print(f"updateImage: {sprite}, {action}, {force}")
		if not force and action != self.animation:
			raise Exception(f"Animation mismatch: requested {action}, current {self.animation}")

		self.canvas.itemconfig(self.last_img, image=self.images[sprite])

	def transportCheck(self):
		''' checks if window has changed, then moves neko to the new window '''
		if self.state == 2:
			if verbose > 2: print(f"self.animation set to {self.animation} -> 'transport'")
			self.animation = "transport"
			self.updateImage(7, "transport", True)
			time.sleep(2)
			try:
    			# using hwnd to get position of the window
				rect = win32gui.GetWindowRect(app.activeWindowID)
				if verbose > 1: print(rect)
				app.moveNeko(rect[0] + self.sprite_width/2, rect[1] - self.sprite_height)
				self.animation = "idle"
				self.updateImage(0, "idle", True)
			except:
				print("Failed to get window position.")
			self.state = 1
		self.after(500, self.transportCheck)


	def moveNeko(self, x, y):
		''' move neko window to x, y '''
		win32gui.MoveWindow(self.hwnd, int(x), int(y), self.sprite_width, self.sprite_height, True)

	def close_window(self, event):
		global isExiting
		isExiting = True
		self.destroy()

	def move(self, event):
		''' mouse drag event '''
		if self.state == 3:
			x, y = self.winfo_pointerxy()
			self.geometry(f"+{int(x - self.sprite_width/2)}+{int(y - self.sprite_height/2 - 1)}")

### EVENT HOOKS
def eventHooker():
	user32 = windll.user32

	def callback(hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
		realActiveWindow = gw.getActiveWindow()
		if getattr(realActiveWindow, '_hWnd', None) == app.hwnd:
			return
		if getattr(realActiveWindow, '_hWnd', None) == hwnd:
			if event == EVENT_SYSTEM_FOREGROUND:
				if app.activeWindowID == realActiveWindow._hWnd: return
				if verbose > 1: print("EVENT_SYSTEM_FOREGROUND", hwnd, realActiveWindow)
				app.activeWindowID = realActiveWindow._hWnd
				if not app.state == 3: app.state = 2
			elif event == EVENT_SYSTEM_MOVESIZESTART:
				if verbose > 1: print("EVENT_SYSTEM_MOVESIZESTART", hwnd, realActiveWindow)
			elif event == EVENT_OBJECT_LOCATIONCHANGE:
				if not idObject == 0: return
				if verbose > 1: print("EVENT_OBJECT_LOCATIONCHANGE", hwnd, realActiveWindow)
			elif event == EVENT_SYSTEM_MOVESIZEEND:
				if verbose > 1: print("EVENT_SYSTEM_MOVESIZEEND", hwnd, realActiveWindow)

		try:
			if isExiting:
				user32.UnhookWinEvent(hookForeground)
				user32.UnhookWinEvent(hookMoveStart)
				user32.UnhookWinEvent(hookMoveEnd)
				user32.UnhookWinEvent(hookLocationChange)
				if verbose: print("Hooks terminated.")
				threadId = windll.kernel32.GetCurrentThreadId()
				user32.PostThreadMessageW(threadId, 0x0012, 0, 0)  # WM_QUIT is 0x0012
		except:
			if verbose > 1: print("failed to do smth idk")
			time.sleep(1)


	# Define the callback function type and event hooks
	WinEventProc = WINFUNCTYPE(None, wintypes.HANDLE, wintypes.DWORD, wintypes.HWND, wintypes.LONG, wintypes.LONG, wintypes.DWORD, wintypes.DWORD)
	callback = WinEventProc(callback)
	user32.SetWinEventHook.restype = wintypes.HANDLE

	EVENT_SYSTEM_FOREGROUND = 0x0003
	EVENT_SYSTEM_MOVESIZESTART = 0x000A
	EVENT_SYSTEM_MOVESIZEEND = 0x000B
	EVENT_OBJECT_LOCATIONCHANGE = 0x800B
	hookForeground = user32.SetWinEventHook(EVENT_SYSTEM_FOREGROUND, EVENT_SYSTEM_FOREGROUND, 0, callback, 0, 0, 0)
	hookMoveStart = user32.SetWinEventHook(EVENT_SYSTEM_MOVESIZESTART, EVENT_SYSTEM_MOVESIZESTART, 0, callback, 0, 0, 0)
	hookMoveEnd = user32.SetWinEventHook(EVENT_SYSTEM_MOVESIZEEND, EVENT_SYSTEM_MOVESIZEEND, 0, callback, 0, 0, 0)
	hookLocationChange = user32.SetWinEventHook(EVENT_OBJECT_LOCATIONCHANGE, EVENT_OBJECT_LOCATIONCHANGE, 0, callback, 0, 0, 0)


	# Run a message loop
	msg = wintypes.MSG()
	while user32.GetMessageW(byref(msg), None, 0, 0):
		user32.TranslateMessageW(msg)
		user32.DispatchMessageW(msg)

def animator(self, action):
	''' handles animation requests '''
	if verbose > 2: print(f"animator: {action}")
	if self.state == 2: return
	try:
		if action == "idle2":
			self.updateImage(1, action, False)
			time.sleep(1.5)
			for i in range(1, 4):
				self.updateImage(2, action, False)
				time.sleep(0.25)
				self.updateImage(3, action, False)
				time.sleep(0.25)
			pass
		elif action == "idle3":
			self.updateImage(2, action, False)
			for i in range(1, random.randint(2, 10)):
				self.updateImage(14, action, False)
				time.sleep(0.25)
				self.updateImage(15, action, False)
				time.sleep(0.25)
			pass
		elif action == "run":
			direction = random.randint(0, 1)
			for i in range(1, random.randint(2, 30)):
				if direction == 0: # go left
					self.updateImage(8, action, False)
					time.sleep(0.2)
					self.updateImage(9, action, False)
					time.sleep(0.2)
				else: # go right
					self.updateImage(10, action, False)
					time.sleep(0.2)
					self.updateImage(11, action, False)
					time.sleep(0.2)
			self.updateImage(3, action, False)
			pass
		else:
			raise Exception("Invalid action: " + action)
		if verbose > 2: print(f"self.animation set to {self.animation} -> 'idle'")
		self.animation = "idle"
		self.updateImage(0, "idle", True)
	except Exception as e:
		if verbose: print(e)


def nekoLogic():
    # init
	threading.Thread(target=eventHooker).start()
	if verbose: print("Hooks started successfully.")
	# time.sleep(1)  # to give Tkinter time to display - not needed - self.wait_visibility(self)
	# app.hwnd = win32gui.FindWindow("TkTopLevel", "pneko") # not needed - self.winfo_id()
	if verbose: print(f"Hi! My window id is {app.hwnd}")
	app.updateImage(0, "idle", False)
	time.sleep(random.randint(10, 30))
	# main 
	while not isExiting:
		if verbose > 2: print("nekoLogic awake...")
		if not app.state == 2:
			actionList = ["sleep", "idle2", "idle2", "idle3", "idle3", "idle3", "idle3", "run", "run", "run" ]
			action = actionList[random.randint(0, len(actionList) - 1)]
			if verbose > 2: print(f"self.animation set to {app.animation} -> {action}")
			app.animation = action
			# UNINTERUPTABLE ACTIONS
			if action == "sleep":
				app.state = 3
				app.updateImage(4, "sleep", True)
				time.sleep(2)
				for i in range(random.randint(10, 60)):
					app.updateImage(5, "sleep", True)
					time.sleep(0.6)
					app.updateImage(6, "sleep", True)
					time.sleep(0.6)
				app.state = 2
				time.sleep(5)
			else:
				app.state = 4
				try:
					animator(app, action)
				except Exception as e:
					if verbose: print(e)
				time.sleep(1)
		if verbose > 2: print("nekoLogic sleeping...")
		time.sleep(random.randint(10, 30))
	if verbose: print("Exiting nekoLogic.")


app = App()
if __name__ == '__main__':
	if verbose: print("Verbose mode enabled, level", verbose)
	try:
		app.activeWindowID = gw.getActiveWindow()._hWnd
		app.mainloop()

		# Exit 0 code
		isExiting = True
		print("Goodbye!")

	except KeyboardInterrupt:
		isExiting = True
		print("Program terminated.")