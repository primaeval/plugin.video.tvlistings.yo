from xbmcswift2 import Plugin
import xbmc,xbmcaddon,xbmcvfs,xbmcgui
import re

import requests

from datetime import datetime
import time

import HTMLParser
import xbmcplugin


plugin = Plugin()

def log2(v):
    xbmc.log(repr(v))

def log(v):
    xbmc.log(re.sub(',',',\n',repr(v)))
    
def get_tvdb_id(name):
    tvdb_url = "http://thetvdb.com//api/GetSeries.php?seriesname=%s" % name
    r = requests.get(tvdb_url)
    tvdb_html = r.text
    tvdb_id = ''
    tvdb_match = re.search(r'<seriesid>(.*?)</seriesid>', tvdb_html, flags=(re.DOTALL | re.MULTILINE))
    if tvdb_match:
        tvdb_id = tvdb_match.group(1)
    return tvdb_id
  
@plugin.route('/play/<channel>/<title>/<season>/<episode>')
def play(channel,title,season,episode):
    channel_number = plugin.get_storage('channel_number')
    #channel_items = play_channel(channel_number[channel],channel)
    items = []
    tvdb_id = ''
    if int(season) > 0 and int(episode) > 0:
        tvdb_id = get_tvdb_id(title)
    if tvdb_id:
        if season and episode:
            meta_url = "plugin://plugin.video.meta/tv/play/%s/%s/%s/%s" % (tvdb_id,season,episode,'select')
            items.append({
            'label': '[COLOR orange][B]%s[/B][/COLOR] [COLOR red][B]S%sE%s[/B][/COLOR] [COLOR green][B]Meta episode[/B][/COLOR]' % (title,season,episode),
            'path': meta_url,
            'is_playable': True,
             })
        if season:
            meta_url = "plugin://plugin.video.meta/tv/tvdb/%s/%s" % (tvdb_id,season)
            items.append({
            'label': '[COLOR orange][B]%s[/B][/COLOR] [COLOR red][B]S%s[/B][/COLOR] [COLOR green][B]Meta season[/B][/COLOR]' % (title,season),
            'path': meta_url,
            'is_playable': False,
             })         
        meta_url = "plugin://plugin.video.meta/tv/tvdb/%s" % (tvdb_id)
        items.append({
        'label': '[COLOR orange][B]%s[/B][/COLOR] [COLOR green][B]Meta[/B][/COLOR]' % (title),
        'path': meta_url,
        'is_playable': False,
         })
        try:
            addon = xbmcaddon.Addon('plugin.video.sickrage')
            if addon:
                items.append({
                'label':'[COLOR orange][B]%s[/B][/COLOR] [COLOR green][B]SickRage[/B][/COLOR]' % (title), 
                'path':"plugin://plugin.video.sickrage?action=addshow&&show_name=%s" % (title),
                })
        except:
            pass
    else:
        match = re.search(r'(.*?)\(([0-9]*)\)$',title)
        if match:
            movie = match.group(1)
            year =  match.group(2) #TODO: Meta doesn't support year yet
            meta_url = "plugin://plugin.video.meta/movies/search_term/%s/1" % (movie)
            items.append({
            'label': '[COLOR orange][B]%s[/B][/COLOR] [COLOR green][B]Meta[/B][/COLOR]' % (title),
            'path': meta_url,
            'is_playable': False,
             }) 
            try:
                addon = xbmcaddon.Addon('plugin.video.couchpotato_manager')
                if addon:
                    items.append({
                    'label':'[COLOR orange][B]%s[/B][/COLOR] [COLOR green][B]CouchPotato[/B][/COLOR]' % (title), 
                    'path':"plugin://plugin.video.couchpotato_manager/movies/add/?title=%s" % (title)
                    })
            except:
                pass
        else:
            meta_url = "plugin://plugin.video.meta/tv/search_term/%s/1" % (title)
            items.append({
            'label': '[COLOR orange][B]%s[/B][/COLOR] [COLOR green][B]Meta search[/B][/COLOR]' % (title),
            'path': meta_url,
            'is_playable': False,
             }) 
            try:
                addon = xbmcaddon.Addon('plugin.video.sickrage')
                if addon:
                    items.append({
                    'label':'[COLOR orange][B]%s[/B][/COLOR] [COLOR green][B]SickRage[/B][/COLOR]' % (title), 
                    'path':"plugin://plugin.video.sickrage?action=addshow&&show_name=%s" % (title),
                    })
            except:
                pass
   
    #items.extend(channel_items)
    return items

    
@plugin.route('/channel/<id>/<name>/<number>')
def channel(id,name,number):
    if plugin.get_setting('ini_reload') == 'true':
        store_channels()
        plugin.set_setting('ini_reload','false')
    
    addons = plugin.get_storage('addons')
    items = []
    for addon in addons:
        channels = plugin.get_storage(addon)
        if not name in channels:
            continue
        path = channels[name]
        try:
            addon = xbmcaddon.Addon(addon)
            if addon:
                item = {
                'label': '[COLOR yellow][B]%s[/B][/COLOR] [COLOR green][B]%s[/B][/COLOR]' % (name,addon.getAddonInfo('name')),
                'path': path,
                'is_playable': True,
                }
                items.append(item)
        except:
            pass

    url = 'http://%s.yo.tv/tv_guide/channel/%s/%s' % (id,number,name)
        
    item = {
    'label': '[COLOR yellow][B]%s[/B][/COLOR] [COLOR red][B]Listing[/B][/COLOR]' % (re.sub('_',' ',name)),
    'path': plugin.url_for('listing', name=name,number=number,url=url),
    'is_playable': False,
    }
    items.append(item)
        
    return items

def utc2local (utc):
    epoch = time.mktime(utc.timetuple())
    offset = datetime.fromtimestamp (epoch) - datetime.utcfromtimestamp (epoch)
    return utc + offset
    
    
def local_time(ttime,year,month,day):
    match = re.search(r'(.{1,2}):(.{2}) {0,1}(.{2})',ttime)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        ampm = match.group(3)
        if ampm == "pm":
            if hour < 12:
                hour = hour + 12
                hour = hour % 24
        else:
            if hour == 12:
                hour = 0

        utc_dt = datetime(int(year),int(month),int(day),hour,minute,0)
        loc_dt = utc2local(utc_dt)
        ttime = "%02d:%02d" % (loc_dt.hour,loc_dt.minute)
    return ttime

@plugin.route('/listing/<name>/<number>/<url>')
def listing(name,number,url):
    html = get_url(url)

    items = []
    month = ""
    day = ""
    year = ""

    tables = html.split('<a data-ajax="false"')

    for table in tables:

        thumb = ''
        season = '0'
        episode = '0'
        episode_title = ''
        genre = ''
        plot = ''
        
        match = re.search(r'<span class="episode">Season (.*?) Episode (.*?)<span>(.*?)</span>.*?</span>(.*?)<',table,flags=(re.DOTALL | re.MULTILINE))
        if match:
            season = match.group(1).strip('\n\r\t ')
            episode = match.group(2).strip('\n\r\t ')
            episode_title = match.group(3).strip('\n\r\t ')
            plot = match.group(4).strip('\n\r\t ')
        else:
            match = re.search(r'<div class="desc">(.*?)<',table,flags=(re.DOTALL | re.MULTILINE))
            if match:
                plot = match.group(1).strip()
            
        
        ttime = ''
        match = re.search(r'<span class="time">(.*?)</span>',table)
        if match:
            ttime = local_time(match.group(1),year,month,day)
            
        title = ''
        match = re.search(r'<h2> (.*?) </h2>',table)
        if match:
            title = match.group(1)

        path = plugin.url_for('play', channel=number,title=title.encode("utf8"),season=season,episode=episode)
        
        if title:
            nice_name = re.sub('_',' ',name)
            if  plugin.get_setting('channel_name') == 'true':
                if plugin.get_setting('show_plot') == 'true':
                    label = "[COLOR yellow][B]%s[/B][/COLOR] %s [COLOR orange][B]%s[/B][/COLOR] %s" % (nice_name,ttime,title,plot)
                else:
                    label = "[COLOR yellow][B]%s[/B][/COLOR] %s [COLOR orange][B]%s[/B][/COLOR]" % (nice_name,ttime,title)
            else:
                if plugin.get_setting('show_plot') == 'true':
                    label = "%s [COLOR orange][B]%s[/B][/COLOR] %s" % (ttime,title,plot)
                else:
                    label = "%s [COLOR orange][B]%s[/B][/COLOR]" % (ttime,title)
            item = {'label': label,  'thumbnail': thumb, 'info': {'plot':plot, 'season':season, 'episode':episode, 'genre':genre}}
            if path:
                item['path'] = path
            else:
                item['is_playable'] = False
            items.append(item)
        else:
            pass
            
        match = re.search(r'<li class="dt">(.*?)</li>',table)
        if match:
            date_str = match.group(1)
            label = "[COLOR red][B]%s[/B][/COLOR]" % (date_str)
            items.append({'label':label,'is_playable':True,'path':plugin.url_for('listing', name=name,number=number,url=url)})
            match = re.search(r'(.*?), (.*?) (.*?), (.*)',date_str)
            if match:
                weekday = match.group(1)
                Month = match.group(2)
                months={"January":"1","February":"2","March":"3","April":"4","May":"5","June":"6","July":"7","August":"8","September":"9","October":"10","November":"11","December":"12"}
                month = months[Month]
                day = match.group(3)
                year = match.group(4)

    plugin.set_content('episodes')    
    plugin.set_view_mode(51)
    return items
    

 
def get_url(url):
    headers = {'user-agent': 'Mozilla/5.0 (BB10; Touch) AppleWebKit/537.10+ (KHTML, like Gecko) Version/10.0.9.2372 Mobile Safari/537.10+'}
    try:
        r = requests.get(url,headers=headers)
        html = HTMLParser.HTMLParser().unescape(r.content.decode('utf-8'))
        return html
    except:
        return ''
  
def load_channels():
    pass

def store_channels():
    if plugin.get_setting('ini_reload') == 'true':
        plugin.set_setting('ini_reload','false')
    else:
        return
        
    addons = plugin.get_storage('addons')
    items = []
    for addon in addons:
        channels = plugin.get_storage(addon)
        channels.clear()
    addons.clear()

    ini_files = [plugin.get_setting('ini_file1'),plugin.get_setting('ini_file2')]
    
    for ini in ini_files:
        try:
            f = xbmcvfs.File(ini)
            items = f.read().splitlines()
            f.close()
            addon = 'nothing'
            for item in items:
                if item.startswith('['):
                    addon = item.strip('[] \t')
                elif item.startswith('#'):
                    pass
                else:
                    name_url = item.split('=',1)
                    if len(name_url) == 2:
                        name = name_url[0]
                        url = name_url[1]
                        if url:
                            channels = plugin.get_storage(addon)
                            channels[name] = url
                            addons = plugin.get_storage('addons')
                            addons[addon] = addon
        except:
            pass
    
   
def make_templates():
    if plugin.get_setting('make_templates') == 'true':
        plugin.set_setting('make_templates','false')
        
        xbmcvfs.mkdir('special://userdata/addon_data/plugin.video.tvlistings.yo')
        if not xbmcvfs.exists('special://userdata/addon_data/plugin.video.tvlistings.yo/myaddons.ini'):
            f = xbmcvfs.File('special://userdata/addon_data/plugin.video.tvlistings.yo/myaddons.ini','w')
            f.close()
        
        xbmcvfs.mkdir('special://userdata/addon_data/plugin.video.tvlistings.yo/templates')
        html = get_url("http://www.yo.tv")
        items = []
        list_items = re.findall(r'<li><a href="http://(.*?)\.yo\.tv"  >(.*?)</a></li>',html,flags=(re.DOTALL | re.MULTILINE))
        for (id,name) in list_items:          
            file_name = 'special://userdata/addon_data/plugin.video.tvlistings.yo/templates/%s.ini' % id
            f = xbmcvfs.File(file_name,'w')
            str = "# WARNING Make a copy of this file.\n# It will be overwritten on the next channel reload.\n\n# %s.ini - %s \n\n[plugin.video.all]\n" % (id,name)
            f.write(str.encode("utf8"))
            
            html = get_url('http://%s.yo.tv/' % id)
            channels = html.split('<li><a data-ajax="false"')
            unique_channels = {}
            for channel in channels:
                name_match = re.search(r'href="/tv_guide/channel/(.*?)/(.*?)"', channel)
                if name_match:
                    number = name_match.group(1)
                    name = name_match.group(2)
                    unique_channels[name] = number
                    
            for name in sorted(unique_channels):
                str = "%s=\n" % (name)
                f.write(str.encode("utf8"))
            
            f.close()

        
        
@plugin.route('/listings/<id>/<name>')
def listings(id,name):
    html = get_url('http://%s.yo.tv/' % id)
    
    channels = html.split('<li><a data-ajax="false"')
    videos = []
    favourite_channels = plugin.get_storage('favourite_channels')
    items = []
    for channel in channels:
        img_url = ''

        img_match = re.search(r'<img class="lazy" src="/Content/images/yo/program_logo.gif" data-original="(.*?)"', channel)
        if img_match:
            img_url = img_match.group(1)

        name = ''
        number = ''
        name_match = re.search(r'href="/tv_guide/channel/(.*?)/(.*?)"', channel)
        if name_match:
            number = name_match.group(1)
            name = name_match.group(2)
            #name = re.sub('_',' ',name)
        else:
            continue
        channel_number = number

        url = 'http://%s.yo.tv/tv_guide/channel/%s/%s' % (id,number,name)

        label = "[COLOR yellow][B]%s[/B][/COLOR]" % (re.sub('_',' ',name))
            
        item = {'label':label,'icon':img_url,'thumbnail':img_url}
        item['path'] = plugin.url_for('listing', name=name, number=number, url=url)
        
        #if favourites == 'true':
        #    if channel_number in favourite_channels:
        #        items.append(item)
        #else:
        items.append(item)

    #
    plugin.set_content('episodes')    
    #TODO
    plugin.add_sort_method(xbmcplugin.SORT_METHOD_TITLE)
    plugin.add_sort_method(xbmcplugin.SORT_METHOD_UNSORTED)
    #plugin.set_view_mode(51)
    return items 

@plugin.route('/channels/<id>/<name>')
def channels(id,name):
    html = get_url('http://%s.yo.tv/' % id)
    
    channels = html.split('<li><a data-ajax="false"')
    videos = []
    favourite_channels = plugin.get_storage('favourite_channels')
    items = []
    for channel in channels:
        img_url = ''

        img_match = re.search(r'<img class="lazy" src="/Content/images/yo/program_logo.gif" data-original="(.*?)"', channel)
        if img_match:
            img_url = img_match.group(1)

        name = ''
        number = ''
        name_match = re.search(r'href="/tv_guide/channel/(.*?)/(.*?)"', channel)
        if name_match:
            number = name_match.group(1)
            name = name_match.group(2)
        else:
            continue
        channel_number = number

        url = 'http://%s.yo.tv/tv_guide/channel/%s/%s' % (id,number,name)

        label = "[COLOR yellow][B]%s[/B][/COLOR]" % (re.sub('_',' ',name))
            
        item = {'label':label,'icon':img_url,'thumbnail':img_url}
        item['path'] = plugin.url_for('channel', id=id, name=name, number=number)
        
        items.append(item)

    plugin.add_sort_method(xbmcplugin.SORT_METHOD_TITLE)
    plugin.set_view_mode(51)
    return items    
    
@plugin.route('/now_nextdk/<id>/<name>')
def now_next(id,name):
    channel_name = name
    html = get_url('http://%s.yo.tv/' % id)

    
    channels = html.split('<li><a data-ajax="false"')
    videos = []
    favourite_channels = plugin.get_storage('favourite_channels')
    items = []
    for channel in channels:
        img_url = ''

        img_match = re.search(r'<img class="lazy" src="/Content/images/yo/program_logo.gif" data-original="(.*?)"', channel)
        if img_match:
            img_url = img_match.group(1)

        name = ''
        number = ''
        name_match = re.search(r'href="/tv_guide/channel/(.*?)/(.*?)"', channel)
        if name_match:
            number = name_match.group(1)
            name = name_match.group(2)
        else:
            continue
           
        channel_number = '0'

        start = ''
        program = ''
        next_start = ''
        next_program = ''
        after_start = ''
        after_program = ''
        match = re.search(r'<li><span class="pt">(.*?)</span>.*?<span class="pn">(.*?)</span>.*?</li>.*?<li><span class="pt">(.*?)</span>.*?<span class="pn">(.*?)</span>.*?</li>.*?<li><span class="pt">(.*?)</span>.*?<span class="pn">(.*?)</span>.*?</li>', channel,flags=(re.DOTALL | re.MULTILINE))
        if match:
            now = datetime.now()
            year = now.year
            month = now.month
            day = now.day
            start = local_time(match.group(1),year,month,day)
            program = match.group(2)
            next_start = local_time(match.group(3),year,month,day)
            next_program = match.group(4)
            after_start = local_time(match.group(5),year,month,day)
            after_program = match.group(6)            

        else:
            pass

        channel_name = plugin.get_setting('channel_name')
        if  channel_name == 'true':
            label = "[COLOR yellow][B]%s[/B][/COLOR] %s [COLOR orange][B]%s[/B][/COLOR] %s [COLOR white][B]%s[/B][/COLOR] %s [COLOR grey][B]%s[/B][/COLOR]" % (re.sub('_',' ',name),start,program,next_start,next_program,after_start,after_program)
        else:
            label = "%s [COLOR orange][B]%s[/B][/COLOR] %s [COLOR white][B]%s[/B][/COLOR] %s [COLOR grey][B]%s[/B][/COLOR]" % (start,program,next_start,next_program,after_start,after_program)
            
        item = {'label':label,'icon':img_url,'thumbnail':img_url}
        item['path'] = plugin.url_for('channel', id=id, name=name, number=number)
        
        items.append(item)

    plugin.set_view_mode(51)
    return items

   
   
@plugin.route('/all_favourites')
def all_favourites():
    favourite_channels = plugin.get_storage('favourite_channels')
    channel_number = plugin.get_storage('channel_number')
    for channel in channel_number:
        favourite_channels[channel] = channel_number[channel]
    
@plugin.route('/no_favourites')
def no_favourites():
    favourite_channels = plugin.get_storage('favourite_channels')
    favourite_channels.clear()
    
@plugin.route('/add_favourite/<name>/<number>')
def add_favourite(name,number):
    favourite_channels = plugin.get_storage('favourite_channels')
    favourite_channels[number] = name

@plugin.route('/remove_favourite/<name>/<number>')
def remove_favourite(name,number):
    favourite_channels = plugin.get_storage('favourite_channels')
    favourite_channels.pop(number)
  
@plugin.route('/set_favourites')
def set_favourites():
    top_items = []
    top_items.append({'label': '[COLOR green][B]ALL[/B][/COLOR]','path': plugin.url_for('all_favourites')})
    top_items.append({'label': '[COLOR red][B]NONE[/B][/COLOR]','path': plugin.url_for('no_favourites')})
    
    channel_number = plugin.get_storage('channel_number')
    favourite_channels = plugin.get_storage('favourite_channels')
    items = []
    selected =  plugin.get_setting('selected')
    for channel in channel_number:
        number = channel
        name = channel_number[number]
        if channel in favourite_channels:
            label = '[COLOR yellow][B]%s[/B][/COLOR]' % name
            path = plugin.url_for('remove_favourite', name=name.encode("utf8"), number=number)
        else:
            label = '%s' % name
            path = plugin.url_for('add_favourite', name=name.encode("utf8"), number=number)

        item = {'label':label}
        item['path'] = path 
        item['thumbnail'] = "http://my.tvguide.co.uk/channel_logos/60x35/%s.png" % number
        items.append(item)
    plugin.set_view_mode(51)    
    sorted_items = sorted(items, key=lambda item: re.sub('\[.*?\]','',item['label']))
    top_items.extend(sorted_items)
    return top_items
    
@plugin.route('/store_channels')
def store_channels():
    addons = plugin.get_storage('addons')
    items = []
    for addon in addons:
        channels = plugin.get_storage(addon)
        channels.clear()
    addons.clear()

    ini_files = [plugin.get_setting('ini_file1'),plugin.get_setting('ini_file2')]
    
    for ini in ini_files:
        try:
            f = xbmcvfs.File(ini)
            items = f.read().splitlines()
            f.close()
            addon = 'nothing'
            for item in items:
                if item.startswith('['):
                    addon = item.strip('[] \t')
                elif item.startswith('#'):
                    pass
                else:
                    name_url = item.split('=',1)
                    if len(name_url) == 2:
                        name = name_url[0]
                        url = name_url[1]
                        if url:
                            channels = plugin.get_storage(addon)
                            channels[name] = url
                            addons = plugin.get_storage('addons')
                            addons[addon] = addon
        except:
            pass

@plugin.route('/country/<id>/<name>')
def country(id,name):
    items = [  
    {
        'label': '[COLOR red][B]%s[/B][/COLOR]: [COLOR green]Now Next After[/COLOR]' % name,
        'path': plugin.url_for('now_next', id=id, name=name)

    },
    {
        'label': '[COLOR red][B]%s[/B][/COLOR]: [COLOR yellow]Channels[/COLOR]' % name,
        'path': plugin.url_for('channels', id=id, name=name)

    },     
    {
        'label': '[COLOR red][B]%s[/B][/COLOR]: [COLOR red]Listings[/COLOR]' % name,
        'path': plugin.url_for('listings', id=id, name=name)

    },
    ]
    return items
            
@plugin.route('/counties')
def countries():
    html = get_url("http://www.yo.tv")

    items = []

    
    list_items = re.findall(r'<li><a href="http://(.*?)\.yo\.tv"  >(.*?)</a></li>',html,flags=(re.DOTALL | re.MULTILINE))
    
    for (id,name) in list_items:
        name = name.encode("utf8")
        items.append({'label': '[COLOR red][B]%s[/B][/COLOR]' % name,'path': plugin.url_for('country', id=id, name=name)})

    plugin.set_content('episodes')    
    plugin.set_view_mode(51)
    return items
    
    
@plugin.route('/')
def index():
    make_templates()
    store_channels()
    load_channels()
    items = [  
    {
        'label': '[COLOR red][B]Countries[/B][/COLOR]',
        'path': plugin.url_for('countries'),

    },    
    ]
    return items
    
if __name__ == '__main__':
    plugin.run()
    