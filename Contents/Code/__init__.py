#Copyright NT
import inspect

TITLE = 'HRTi Plex'
ICON = 'icon-default.png'
URL = 'https://hrti.hrt.hr/'
CLIENT_HOST = 'clientapi.hrt.hr'

DEBUG_RANDOM = Util.RandomInt( 0,67 )

def Start():
	Log( "starting plug-in" )
	HTTP.CacheTime = 0
	if( Prefs['username'] == None or Prefs['password'] == None):
		raise ValueError('username and password required')
	session = Data.LoadObject('session')
	auth = login()
	Dict['access_token'] =  Hash.SHA1( Dict['uuid'] + auth['session_token'] )
	Dict['language'] = auth['application_language']
	Dict['application_id'] = 'all_in_one'
	Dict['vsc'] = session['variables']['vsc']['uri'].format(language='hr',application_id='all_in_one')
	
	Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")
	Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
	Log.Debug( "parsed start" )

ObjectContainer.title1 = TITLE
ObjectContainer.view_group = 'List'
#######
DirectoryObject.thumb = R(ICON)
VideoClipObject.thumb = R(ICON)
	
@handler('/video/hrti', TITLE, thumb = ICON)
def MainMenu():
	Log( "entering MainMenu" )
	oc = ObjectContainer( header = 'loading', message='please wait ..',
		objects = [
			#~ DirectoryObject(key = Callback(VideoOnDemand), title = L('vod') ),
			#~ DirectoryObject(key = Callback(EPG), title = 'epg'),
			#DirectoryObject(key = Callback(Catchup), title = 'catchup')
			DirectoryObject(key = Callback(VideoListings), title = 'video_listings')
		]
	)
	return oc
	
@route('video/hrti/listings')
def VideoListings():
	oc = ObjectContainer(no_cache = True, title2='videos')
	for video in JSON.ObjectFromURL( Dict['vsc'], timeout=float(30) )['videos']:
		oc.add( DirectoryObject(
			key= Callback(VideoListing,id=video['id'],value=video),
			title = video['title']['title_long'],
			summary = video['title']['summary_short'],
			#originally_available_at = Datetime.ParseDate( video['properties']['broadcast_date'] ).date(),
			#url = video['url'].format( vsc = Dict['vsc'] )
		))
	return oc
	
@route('video/hrti/listings/{id}',method='PUT')
def VideoListing(id,value):
	Log.Debug('entering videolisting')
	oc = ObjectContainer(title2=id, no_cache = True)
	oc.add(VideoClipObject(
		title = value['title']['title_long'],summary='',
		url=value['url'].format(vsc=Dict['vsc'])
		#url="http://stafaband.info-muviza.com-bursamp3.wapka.mobi-sharelagu.wapka.mobi-4shared.com.laguzone.com/download_lagu_video_Bugs%20Bunny's%20Square%20Dance%20In%20'Hillbilly%20Hare'%20(best%20Quality%20+%20Subtitles!).mp4?v=NkiJDw1Kung"
		)
	)
		
	return oc
	

@route("video/hrti/catchup")
def Catchup():
	Log.Debug( 'entering catchup' )
	try:
		session = Data.LoadObject( 'session' )
		uri = session['modules']['catchup']['resources']['list']['uri']
		response = XML.ElementFromURL( uri.format(session_id=session['session_id'],access_token=Dict['access_token']), timeout = float(30) )
		oc = ObjectContainer( title2='catchup' )
		Log.Debug( 'parsing catchup' )
		for catchup in response.xpath('//catchup'):
			Log(XML.StringFromElement(catchup))
			stop = Datetime.ParseDate( catchup.xpath( '@stop/text()')[0] )
			Log("%s",stop)
			if( stop > Datetime.Now() ):
				Log( catchup.xpath( 'title/text()' )[0] )
			#~ oc.add( VideoClipObject(
				#~ url = catchup.xpath( 'streaming_url/text()' )[0].split('?')[0],
				#~ title = catchup.xpath( 'title/text()' )[0],
				#~ summary = catchup.xpath( 'description/text()' )[0],
				#~ #originally_available_at = Datetime.ParseDate( catchup.xpath( '@start/text()')[0] ).date(),
				#~ #duration = Datetime.ParseDate( catchup.xpath( '@stop')[0] ).date()
				#~ #							- Datetime.ParseDate( catchup.xpath( '@start')[0] ).date()
			#~ ))
	except:
		Log.Error("error")
	Log.Debug( 'exiting' )
	return oc
	
@route("video/hrti/vod")
def VideoOnDemand():
	oc = ObjectContainer( no_cache = True, title2=L('vod'))
	session = Data.LoadObject( SESSION_DATA_KEY )
	uri = session['modules']['channel']['resources']['all']['uri'].format(application_id="all_in_one",language="hr" )
	channel_list = XML.ElementFromURL( uri )
	for channel in channel_list.xpath("//channel"):
		oc.add( DirectoryObject(
			title = channel.xpath("./name/text()")[0],
			thumb = Resource.ContentsOfURLWithFallback(channel.xpath("./img/text()")[0])
			#~ url = channel.xpath("./live_img/text()")[0],
			#~ summary = 'summary'
			
		))
	return oc

@route("video/hrti/epg")
def EPG():
	oc = ObjectContainer( no_cache = True)
	try:
		uri = Data.LoadObject( SESSION_DATA_KEY )['modules']['epg']['resources']['program_category']['uri']
		programm_list = XML.ElementFromURL( uri)
		for programm_category in programm_list.xpath( '//epg_program_category' ):
			oc.add( DirectoryObject(
				key = Callback(EPGCategory,id = programm_category.xpath('./id/text()')[0]),
				title = programm_category.xpath('./name/text()')[0] )
			)
	except Exception as e:
		Log.Error('chaugth e')
	return oc

@route("video/hrti/epg/{id}")
def EPGCategory(id):
	return ObjectContainer( no_cache = True)


def login():
	KEY = 'login'
	if( Data.Exists( KEY ) ):
		data = Data.LoadObject( KEY )
		access_token = data[ 'secure_streaming_token' ]
		expires = Datetime.FromTimestamp( float(access_token.split('/')[2]) )
		if( expires > Datetime.Now() ):
			Log('session still valid')
			return data
	URL = 'https://clientapi.hrt.hr/user/login/session_id/%(session_id)s/format/json'
	request = HTTP.Request( URL % session(),
		headers = REQUEST_HEADERS, data = '{"username":"%(username)s","password":"%(password)s"}' % Prefs
	)
	request.load()
	response = JSON.ObjectFromString(request.content)
	Data.SaveObject(KEY,response)
	return response
	
MODULES_KEY = 'modules'
APPLICATION_ID_KEY = 'application_id'
LANGUAGE_SOURCE_KEY = 'language_source'
IDENTIFY_URL = 'https://clientapi.hrt.hr/client_api.php/config/identify/format/json'

def session():
	Log.Debug('entering session')
	KEY = 'session'
	data = identify()
	data.update({ "application_version":"1.1",
		"device_model_string_id":Platform.MachineIdentifier,
		"os":Platform.OS, "os_version":Platform.OSVersion, # evtl. Platform.CPU
		"screen_height":"1080", "screen_width":"1920"
	})
	session = HTTP.Request( IDENTIFY_URL, headers=REQUEST_HEADERS, method='PUT',
		data = JSON.StringFromObject( data )
	)
	session.load()
	response = JSON.ObjectFromString( session.content )
	Dict['session_id'] = response['session_id']
	Dict['uuid'] = data['uuid']
	Data.SaveObject(KEY, response )
	Log.Debug('exiting')
	return response

REQUEST_HEADERS = {'Content-Type': 'application/json'}

def identify():
	Log.Debug('entering identify')
	request = {"application_publication_id": "all_in_one"}
	HTTP.Request( IDENTIFY_URL, method='OPTIONS' ).load()
	identity = HTTP.Request( IDENTIFY_URL, headers=REQUEST_HEADERS, data=JSON.StringFromObject(request) )
	identity.load()
	request['uuid'] = JSON.ObjectFromString( identity.content )['uuid']
	Log.Debug('exiting')
	return request

def debug(d, indent=0):
 for key, value in d.iteritems():
		Log( '\t' * indent + str(key) )
		if isinstance(value, dict):
			debug(value, indent+1)
		else:
			Log( '\t' * (indent+1) + str(value) )
	
