import ctypes

try:
	import obspython
except ImportError:
	print("Error: As this is an OBS targeted script, you should be running this in OBS. Just sayin\'")

try:
	import win32gui
	import win32com.client
except ImportError:
	print("Error: Corvinus Now Playing could not find pywin32 installed in your python path. Please make sure it's installed properly.")

#----------------------------------------------
# global properties/options
#----------------------------------------------
enabled = True
latency = 4000
display_text = ""
alt_display_text = ""
debug_mode = False
source_name = ""
output_buffer = 5

#----------------------------------------------
# OBS Properties Handling
#----------------------------------------------
def script_defaults(settings):
	global debug_mode
	if debug_mode: print("Calling defaults")
	
	global enabled
	global source_name
	global display_text
	global alt_display_text
	global latency
	global output_buffer
	
	obspython.obs_data_set_default_bool(settings, "enabled", enabled)
	obspython.obs_data_set_default_int(settings, "latency", latency)
	obspython.obs_data_set_default_string(settings, "source_name", source_name)
	obspython.obs_data_set_default_string(settings, "display_text", display_text)
	obspython.obs_data_set_default_string(settings, "alt_display_text", alt_display_text)
	obspython.obs_data_set_default_int(settings, "output_buffer", output_buffer)
	
def script_description():
	return "<b>Corvinus: Now Playing</b>" + \
		"<hr>" + \
		"Check the boxes of audio sources you wish to capture current data from.<br/><br/>" + \
		"Available services:<br/>" + \
		"YouTube: Will get current page title from any browser window with 'YouTube' in its title and format it appropriately as possible.<br/>" + \
		"foobar2000: Will automatically obtain track data from Foobar.<br/><br/>" + \
		"Available Placeholder Strings:<br/>" + \
		"<code>%artist</code> to display current artist<br/><code>%title</code> to display the current track title<br/><code>%source</code> to display the current source name<br/><br/>" + \
		"<hr>"
		
def script_load(settings):
	global debug_mode
	if(debug_mode): 
		print("Loaded script for Corvinus Now Playing")
	
def script_properties():
	global debug_mode
	if debug_mode: print("Loaded properties for Corvinus Now Playing")
	
	props = obspython.obs_properties_create()
	obspython.obs_properties_add_bool(props, "enabled", "Enabled")
	obspython.obs_properties_add_text(props, "source_name", "Text (GDI+) Target's Name", obspython.OBS_TEXT_DEFAULT)
	obspython.obs_properties_add_int(props, "latency", "Check Frequency (ms)", 150, 10000, 100)
	obspython.obs_properties_add_text(props, "display_text", "Display Text", obspython.OBS_TEXT_DEFAULT)
	obspython.obs_properties_add_text(props, "alt_display_text", "Fallback Display Text", obspython.OBS_TEXT_DEFAULT)
	obspython.obs_properties_add_int(props, "output_buffer", "Display Text Buffer Space", 1, 10, 1)
	obspython.obs_properties_add_bool(props, "debug_mode", "Debug Mode")
	
	return props
	
def script_save(settings):
	global debug_mode
	if debug_mode: print("Saved properties for Corvinus Now Playing")
	script_update(settings)

def script_unload():
	global debug_mode
	if debug_mode: print("Unloaded script for Corvinus Now Playing")
	obspython.timer_remove(get_song_info)
	
def script_update(settings):
	global debug_mode
	if debug_mode: print("Updated properties for Corvinus Now Playing")
	
	global enabled
	global display_text
	global alt_display_text
	global latency
	global source_name
	global output_buffer
	
	debug_mode = obspython.obs_data_get_bool(settings, "enabled")
	debug_mode = obspython.obs_data_get_bool(settings, "debug_mode")
	output_buffer = obspython.obs_data_get_int(settings, "output_buffer")
	display_text = obspython.obs_data_get_string(settings, "display_text")
	alt_display_text = obspython.obs_data_get_string(settings, "alt_display_text")
	latency = obspython.obs_data_get_int(settings, "latency")
	source_name = obspython.obs_data_get_string(settings, "source_name")
	

	if obspython.obs_data_get_bool(settings, "enabled") is True:
		if (not enabled):
			if debug_mode: print("Enabled song timer for Corvinus Now Playing")
		enabled = True
		obspython.timer_add(get_song_info, latency)
	else:
		if(enabled):
			if debug_mode: print("Disabled song timer for Corvinus Now Playing")
			enabled = False
			obspython.timer_remove(get_song_info)
	
#----------------------------------------------
# Corvinus Now Playing Functionality
#----------------------------------------------
def get_song_info():
	global debug_mode
	global now_playing
	global display_text
	global alt_display_text
	global latency
	global output_buffer
	
	source_foobar = False
	source_youtube = False
	
	song_artist = ""
	song_title = ""
	song_album = ""
	song_length = ""
	song_tracking = 0
	now_playing = ""
	buffer_string = ""

	for x in range(output_buffer):
		buffer_string = buffer_string + " "
	
	def format_browser_title(input_array):
		str = ""
		for i in input_array:
			if("YouTube" in i):
				str = i;
				try:
					index = str.index("- YouTube - ")
					str = str[:index-1]
				except:
					if debug_mode: print("Something went wrong formatting YouTube's title.")
			# remove notification count
			if(str[:1] == "("):
				for x in range(len(str)):
					if(str[x] == ")"):
						str = str[x+1:]
						return str
		return str
		
	# get running window titles
	EnumWindows = ctypes.windll.user32.EnumWindows
	
	EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
	
	GetWindowText = ctypes.windll.user32.GetWindowTextW
	GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
	IsWindowVisible = ctypes.windll.user32.IsWindowVisible
	
	titles = []
	
	def foreach_window(hwnd, lParam):
		if IsWindowVisible(hwnd):
			length = GetWindowTextLength(hwnd)
			buff = ctypes.create_unicode_buffer(length + 1)
			GetWindowText(hwnd, buff, length + 1)
			titles.append(buff.value)
		return True
		
	EnumWindows(EnumWindowsProc(foreach_window), 0)
		
	#---------------------------------------
	# foobar2000 handler
	#---------------------------------------
	for i in titles:
		if("foobar2000" in i):
			source_foobar = True
			break
		elif("YouTube" in i):
			source_youtube = True
			break
		else:
			source_foobar = False
			source_youtube = False
			
	# attempt connecting to fb2k handling service
	try:
		ProgID = "Foobar2000.Application.0.7"
		foobar_COM_object = win32com.client.Dispatch(ProgID)
		fb2k = foobar_COM_object.Playback
		source_foobar = True
	except:
		source_foobar = False
		if debug_mode: print("Error: Could not connect to foobar2000 COM service. Please make sure it's installed properly.")	

	if(source_foobar == True and fb2k.IsPlaying == True):
		song_artist = fb2k.FormatTitle("[%artist%]")
		song_title = fb2k.FormatTitle("[%title%]")
		song_album = fb2k.FormatTitle("[%album%]")
			
		now_playing = display_text.replace("%artist", song_artist).replace("%title", song_title).replace("%album", song_album) + buffer_string
	elif(source_youtube == True):
		song_title_new = format_browser_title(titles)
		now_playing = song_title_new + buffer_string
	else:
		now_playing = alt_display_text + buffer_string

	update_song()
	
def update_song():
	global debug_mode
	global now_playing
	
	settings = obspython.obs_data_create()
	obspython.obs_data_set_string(settings, "text", now_playing)
	source = obspython.obs_get_source_by_name(source_name)
	obspython.obs_source_update(source, settings)
	obspython.obs_data_release(settings)
	obspython.obs_source_release(source)