#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os
import sys
import xbmc
import xbmcvfs
import xbmcaddon
import json
import datetime
import time
import dateutil.parser
import dateutil.tz
import urllib.request
import socket

from urllib.error import URLError, HTTPError


# Add the /lib folder to sys TOUFIX TOUCHECK needed ?
sys.path.append(xbmcvfs.translatePath(os.path.join(xbmcaddon.Addon("plugin.video.auvio").getAddonInfo("path"), "lib")))

# Plugin modules
from . import common
from . import api

def parse_dict_args(x, y):
    # https://stackoverflow.com/a/26853961/782013

    # python 3.5: z = {**x, **y}

    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z

def request_url(url, params={}, headers={}, data=None):

    #URL parameters
    if params:
        params_str = urllib.parse.urlencode(params)
        url = url + '?' + params_str

    #request headers
    headers_defaults = {
        'Referer':      'https://www.rtbf.be',
        'User-Agent':   'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
    }

    headers = parse_dict_args(headers_defaults,headers)

    common.plugin.log('request_url : %s' % url,xbmc.LOGINFO)
    common.plugin.log(headers,xbmc.LOGINFO)

    request = urllib.request.Request(url, data=data, headers=headers)

    try:
        response = urllib.request.urlopen(request)
        data = response.read().decode("utf-8")
        response.close()
        return data

    except HTTPError as e:
        common.plugin.log('request_url : unable to get %s' % url,xbmc.LOGERROR)
        common.plugin.log('HTTPError = ' + str(e.code),xbmc.LOGERROR)
        raise

    except URLError as e:
        common.plugin.log('request_url : unable to get %s' % url,xbmc.LOGERROR)
        common.plugin.log('URLError = ' + str(e.reason),xbmc.LOGERROR)
        raise

    except httplib.HTTPException as e:
        common.plugin.log('request_url : unable to get %s' % url,xbmc.LOGERROR)
        common.plugin.log('HTTPException',xbmc.LOGERROR)
        raise

    except Exception:
        import traceback
        common.plugin.log('request_url : unable to get %s' % url,xbmc.LOGERROR)
        common.plugin.log('generic exception: ' + traceback.format_exc(),xbmc.LOGERROR)
        raise

def now():
  return datetime.datetime.now(dateutil.tz.tzlocal())

def get_kodi_media_type(media):
    kodi_type = None
    media_type = media.get('type')

    if media_type == 'video':
        kodi_type = 'video'
    elif media_type == 'livevideo':
        kodi_type = 'video'
    elif media_type == 'audio':
        kodi_type = 'music'
    elif media_type == 'radio':
        kodi_type = 'music'

    return kodi_type

def get_kodi_media_duration(media):

    # return media duration in seconds

    media_type = media.get('type')
    duration = media.get('duration',0)

    # compute media duration from the start / end date
    if not duration and media_type == 'livevideo':

        start_date = media.get('start_date',None)
        end_date = media.get('end_date',None)

        if start_date and end_date:
            start_date = dateutil.parser.parse(start_date)
            end_date = dateutil.parser.parse(end_date)
            date_diff = end_date - start_date
            duration = date_diff.total_seconds()
            #for 24h-long streams (eg. for live radios), ignore duration
            if duration == 86340:
                return None

    return int(round(duration))

def media_is_streaming(media):

    start_date = media.get('start_date',None)
    end_date = media.get('end_date',None)

    if not start_date or not end_date:
        common.plugin.log('utils.media_is_streaming() : missing start_date or end_date',xbmc.LOGERROR)
        return

    now_datetime = now()
    start_date = dateutil.parser.parse(start_date)
    end_date = dateutil.parser.parse(end_date)

    return (start_date <= now_datetime <= end_date)

def get_stream_start_date_formatted(start_date):

    if start_date is None:
        common.plugin.log('utils.get_stream_start_date_formatted() : missing start_date',xbmc.LOGERROR)
        return None

    now_datetime = now()
    start_date = dateutil.parser.parse(start_date)

    formatted_date = start_date.strftime(xbmc.getRegion('dateshort'))
    formatted_time = start_date.strftime(xbmc.getRegion('time'))

    if now_datetime.date() != start_date.date():
        formatted_datetime = formatted_date + " - " + formatted_time
    else:
        formatted_datetime = formatted_time

    return formatted_datetime

def datetime_W3C_to_kodi(input = None):

    #CONVERT datetime (ISO9601) to kodi format (01.12.2008)

    if not input:
        return None

    date_obj = dateutil.parser.parse(input)
    return date_obj.strftime('%d.%m.%Y')
