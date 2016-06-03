#Copyright NT
import inspect

TITLE = 'HRTi Plex'
LOGO = 'icon-default.png'
URL = 'https://hrti.hrt.hr/'
LOGIN_URL = 'https://clientapi.hrt.hr/user/login/session_id/%(session_id)s/format/json'
IDENTIFY_URL = 'https://clientapi.hrt.hr/client_api.php/config/identify/format/json'
CLIENT_HOST = 'clientapi.hrt.hr'
SESSION_DATA_KEY = 'session_response'
LOGIN_DATA_KEY = 'login_response'
REQUEST_HEADERS = {'Content-Type': 'application/json'}

def Start():
	
	ObjectContainer.title1 = TITLE
	DirectoryObject.thumb = R(LOGO)
	if(not Data.Exists(SESSION_DATA_KEY)):
		HTTP.Request( IDENTIFY_URL, method='OPTIONS').load()
		identity_request = HTTP.Request( IDENTIFY_URL, headers = REQUEST_HEADERS,
		 data=JSON.StringFromObject({"application_publication_id": "all_in_one"})
		)
		identity_request.load()
		Dict['uuid'] = JSON.ObjectFromString(identity_request.content)['uuid']
		session_request_body = JSON.StringFromObject({
			"application_publication_id":"all_in_one", "application_version":"1.1",
			"device_model_string_id":Platform.MachineIdentifier,
			"os":Platform.OS, "os_version":Platform.OSVersion, # evtl. Platform.CPU
			"screen_height":"1080", "screen_width":"1920", "uuid":Dict['uuid']
		})
		session_request = HTTP.Request( IDENTIFY_URL, headers=REQUEST_HEADERS, method='PUT',
			data = session_request_body
		)
		session_request.load()
		Data.SaveObject(SESSION_DATA_KEY,JSON.ObjectFromString(session_request.content))
		login_request = HTTP.Request( LOGIN_URL % Data.LoadObject(SESSION_DATA_KEY),
			headers = REQUEST_HEADERS, data = '{"username":"%(username)s","password":"%(password)s"}' % Prefs
		)
		login_request.load()
		Data.SaveObject(LOGIN_DATA_KEY,JSON.ObjectFromString(login_request.content))
	#~ Log.Info(Data.LoadObject(SESSION_DATA_KEY).viewitems())
	#~ for key,value in Data.LoadObject(SESSION_DATA_KEY).items():
		#~ if key == 'modules':
			#~ for k,v in value.items():
				#~ Log.Info("module %s: %s",k,v)
		#~ else:
			#~ Log.Info("%s: %s",key,value)
	#~ Log.Info(Data.LoadObject(LOGIN_DATA_KEY).viewitems())
	
	
@handler('/video/hrti', TITLE)
def MainMenu():
	
	Log.Debug('entering MainMenu')
	session_data = Data.LoadObject(SESSION_DATA_KEY)
	
	oc = ObjectContainer()
	for k,v in session_data['modules'].items():
		oc.add(DirectoryObject( key = Callback(SecondMenu), title = k ))
	
	Log.Debug('returning oc for MainMenu')
	
	return oc


def SecondMenu():
	oc = ObjectContainer()
	return oc
