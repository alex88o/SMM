
# -*- coding: utf-8 -*-
#!/usr/bin/env python
#title:		image_crawler.py
#description:	Download the last public images from Flickr with associated information
#author:		Alessandro Ortis
#date:		20170928
#version:		0.1
#usage:		python image_crawler.py <seqday>
#notes:         if there are images in the DB, update daily information
#==============================================================================


import flickrapi
import json
import pickle
import urllib, urllib2
import csv
import sys, os, os.path
reload(sys)
sys.setdefaultencoding('utf8')
import time
#from skimage.measure import structural_similarity as ssim
from skimage.measure import compare_ssim as ssim
import cv2
import numpy as np
#import matplotlib.pyplot as plt
from sys import argv
from shutil import copyfile
import time, datetime, calendar
import ftfy

 
 
def find_by_size(size,path):
    result = []
    for root, dirs, files in os.walk(path):
        for f in files:
            path_name = os.path.join(root,f)
            if os.stat(path_name).st_size > size:
                result.append(f)
    return result

"""
def downloadImage(url, file_name):
    
    u = urllib2.urlopen(url)
    f = open(file_name, 'wb')
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    print "\nDownloading: %s Bytes: %s" % (file_name, file_size)
    
    file_size_dl = 0
    block_sz = 8192
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break
    
        file_size_dl += len(buffer)
        f.write(buffer)
        status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
        status = status + chr(8)*(len(status)+1)
        print "\n"+status,
    
    f.close()
"""    

def mse(A,B):
    err = np.sum((A.astype("float") - B.astype("float")) ** 2)
    err /= float((A.shape[0]) * (A.shape[1]))
    return err
    
def isMissing(imagePath):
    for referenceImage in nullImages:
        refImgPath = "data/" + referenceImage
        refImg = cv2.imread(refImgPath)
        curImg = cv2.imread(imagePath)
        
            
        refImg = cv2.cvtColor(refImg, cv2.COLOR_BGR2GRAY)
        curImg = cv2.cvtColor(curImg, cv2.COLOR_BGR2GRAY)
        
        curImg = cv2.resize(curImg,(refImg.shape[1], refImg.shape[0]))
        
        
        s = ssim(refImg,curImg)
        print "SSIM with null picture:\t"+str(s)
        if s>0.99:
            return True
    return False
    

def sanitize_text(s):
    s = unicode(s)
    s = s.replace("&#39;"," ")
    s = s.replace("'"," ")
    s = s.replace("’"," ")
    s = s.replace("\""," ")
    s = s.replace("\n"," ")
    s = ftfy.fix_text(s)
    return s
        
def photo_crawling(photo_id,):
    
    try:
   
	check = False
        print "\nProcessing photo with FlickrId:\t" +photo_id

        print "Getting photo info..."
        response = flickr.photos.getInfo(api_key = api_key, photo_id=photo_id)            
        print "request result:\t"+response['stat']
        photo_info = response['photo']
        ext = 'jpg'
        photo_url = 'https://farm'+str(photo_info['farm'])+'.staticflickr.com/'+str(photo_info['server'])+'/'+photo_id+'_'+str(photo_info['secret'])+'_b.'+ext
        user_id = photo_info['owner']['nsid']
        dt = datetime.datetime.utcnow()
        date_download = calendar.timegm(dt.utctimetuple())
             
	date_posted = photo_info['dates']['posted']
	date_taken = photo_info['dates']['posted']
	photo_title = ''
	photo_title = photo_info['title']['_content']
	#          print "Original Title: " + photo_title
	photo_title = photo_title.replace("&#39;"," ")
	photo_title = photo_title.replace("'"," ")
	photo_title = photo_title.replace("’"," ")
	photo_title = photo_title.replace("\""," ")
	photo_title = photo_title.replace("\n"," ")
	photo_title = ftfy.fix_text(unicode(photo_title))
   #         print "Title: " + photo_title

	#TODO: use the function sanitize_text
	photo_description = ''
	photo_description = photo_info['description']['_content']
	photo_description = photo_description.replace("&#39;"," ")
	photo_description = photo_description.replace("'"," ")
	photo_description = photo_description.replace("’"," ")
	photo_description = photo_description.replace("\""," ")
	photo_description = photo_description.replace("\n"," ")
	photo_description = ftfy.fix_text(unicode(photo_description))
	#        print "Description: " + photo_description

	photo_tags_num = len(photo_info['tags']['tag'])
	photo_tags = [sanitize_text(str(t['_content'])) for t in photo_info['tags']['tag']]
	#        print "# of tags:\t" + str(photo_tags_num)
	#           print photo_tags

	lat = ""
	lon = ""
	country = ""
	if 'location' in photo_info:
		lat = photo_info['location']['latitude']
		lon = photo_info['location']['longitude']
		if 'country' in photo_info['location']:
		    country = photo_info['location']['country']['_content']


	print "Getting photo sizes..."
	response = flickr.photos.getSizes(api_key = api_key, photo_id=photo_id)            
	print "request result:\t"+response['stat']
	photo_size = 0
	for sz in response['sizes']['size']:
		if sz['label'] == 'Original':
		    print "Original size:\t("+ sz['height'] +" X " + sz['width'] +")"
		    break

	# Download the photo and check if still available
	img_path = "images/"+photo_id   
	httpRes = urllib.urlretrieve(photo_url, img_path)
	# Questa funzione usa urllib2     
	#downloadImage(photo_url,img_path)    
	abs_path = os.path.abspath(img_path)
		
	check = isMissing(img_path)
	print "Is missing:\t" + str(check)
	if check:
		copyfile(abs_path, "missing/"+photo_id)
		os.remove(abs_path)
		abs_path = os.path.abspath("missing/"+photo_id)            
	elif os.stat(abs_path).st_size < 10000:
	# Discard images with size lower than 10Mb
		copyfile(abs_path, "missing/"+photo_id)
		os.remove(abs_path)
		abs_path = os.path.abspath("missing/"+photo_id)            
		check = True
	print "Photo discarded due to image file size"

	print "Getting photo contexts..." 
	response = flickr.photos.getAllContexts(api_key = api_key, photo_id=photo_id)            
	print "request result:\t"+response['stat']
	photo_sets = 0
	photo_groups = 0
	avg_group_memb =0
	avg_group_photos = 0
	photo_groups_ids =[]
	groups_members =[]
	groups_photos = []
	if 'set' in response:
		photo_sets = len(response['set'])
	if 'pool' in response:
		photo_groups = len(response['pool'])
		photo_groups_ids = [g['id'] for g in response['pool']]
		groups_members = [int(g['members']) for g in response['pool']]
		groups_photos = [int(g['pool_count']) for g in response['pool']]
		avg_group_memb = 0 if len(groups_members)==0 else np.mean(groups_members)
		avg_group_photos = 0 if len(groups_photos)==0 else np.mean(groups_photos)
	#    if photo_groups > 0:
	#    print json.dumps(photo_groups_ids)
	print "The photo is shared through\t" +str(photo_sets)+"\talbums and\t"+str(photo_groups)+"\tgroups."


	print "Getting user info..."
	response = flickr.people.getInfo(api_key = api_key, user_id=user_id)            
	print "request result:\t"+response['stat']
	ispro = int(response['person']['ispro'])
	has_stats = int(response['person']['has_stats']) 
	username = response['person']['username']['_content']
	username = sanitize_text(username)
	#            if 'location' in response['person']:
	#               location = response['person']['location']['_content']        

	user_photos = int(response['person']['photos']['count']['_content'])        

	print "Getting user contacts..."
	response = flickr.contacts.getPublicList(api_key = api_key, user_id=user_id)            
	print "request result:\t"+response['stat']
	contacts = int(response['contacts']['total'])


	 
	# Notes: the API allows only 500 photos per call. If the user has 
	# a huge amount of pictures, consider only the views of the 10.000 oldest photos (i.e., 20 pages).
	print "Getting photos stats..."
	user_photo_views = []
	page_n = 1
	while len(user_photo_views)< user_photos:
	    if page_n == 10:
		print "Waiting 1 sec..."
		time.sleep(1)
		
	    response = flickr.people.getPublicPhotos(api_key = api_key, user_id=user_id, extras='views', page=page_n, per_page=500)            
	    print "request result:\t"+response['stat']
	    page_elements = [int(p['views']) for p in response['photos']['photo']]
	    user_photo_views.extend(page_elements)
	    page_n += 1
	    #Integrity check and upper bound                
	    if len(page_elements)<500 or page_n >20:
		break

	user_mean_views = 0 if len(user_photo_views)==0 else np.mean(user_photo_views)
	print "The user's photos have a mean view rate of\t"+str(user_mean_views)+"\tcomputed on\t"+str(len(user_photo_views))+"\tphotos."

	print "Getting user groups info..."
	response = flickr.people.getPublicGroups(api_key = api_key, user_id=user_id)            
	print "request result:\t"+response['stat']
	user_groups_membs = [int(g['members']) for g in response['groups']['group']]
	user_groups_photos = [int(g['pool_count']) for g in response['groups']['group']]
	user_groups = len(user_groups_photos)
	avg_user_gmemb = 0 if len(user_groups_membs)==0 else np.mean(user_groups_membs)
	avg_user_gphotos = 0 if len(user_groups_photos)==0 else np.mean(user_groups_photos)
	print "The user has\t"+str(contacts)+"\tcontacts and is enrolled in\t" +str(user_groups)+"\tgroups with\t"+str(avg_user_gmemb)+"\tmean members and\t"+str(avg_user_gphotos)+"\tmean photos."




	# Single quote escape
	tags = json.dumps(photo_tags).replace("'","''")
	print tags
	
	
        photo_views = int(photo_info['views'])
        photo_comments = int(photo_info['comments']['_content'])        

        print "Getting photo favorites..."
        response = flickr.photos.getFavorites(api_key = api_key, photo_id=photo_id)            
        print "request result:\t"+response['stat']
        photo_favorites = int(response['photo']['total'])
     
        print photo_url,'\n','views:\t',photo_views,'\tcomments:\t',photo_comments

        return True	# The only one "True" return value
        
    except Exception, e:
        print "ERROR with Photo\t"+photo_id+":"
        print str(e)
        return False
    

def photos_analysis(images_list):

	err_list = []

	print "\n\nSTART\n************\tUTC\t"+str(datetime.datetime.utcnow())+"\t************"
	print "Analysing\t"+str(len(images_list))+"\t photos"

	for photo_id in images_list:
	   try:
	       res = photo_crawling(photo_id) 
	       if res:
		    print "Image\t"+photo_id+"\tanalyzed."
	       else:
		    print "Image\t"+photo_id+"\terror occurred."
		    err_list.append(photo_id)
	   except Exception, e:
		print "ERROR (external loop):"
		print "FlickrId:\t"+str(photo_id)
		err_list.append(photo_id)
		print str(e)
		
	print "Error images list:"
	print err_list
	print "Images with errors:"
	print len(err_list)

	print "\n\nEND\n************\tUTC\t"+str(datetime.datetime.utcnow())+"\t************"


# Null image name
nullImages= ["flickrMissing", "flickrNotFound"]

# Credenziali The Social Picture
api_key = u'c3388aa658417c77dcc98d5f9dc3ac91'
api_secret = u'9f3693a3ab57bfc1'

# Credenziali iplabsocial (alessandro.ortis)
#api_key= u'394b14cc54cd9cba5aa0d68b1d5f7eb9'
#api_secret = u'9bda221d1de625a9'

# Le seguenti due righe sono state eseguite una volta sola per generare il token di autorizzazione    
#flickr = flickrapi.FlickrAPI(api_key, api_secret)
#flickr.authenticate_via_browser(perms='read')
oauth_token=u'72157675663685032-6052b3ccbdc594e8'
oauth_verifier=u'1103dab7cc7d9c5e'

flickr = flickrapi.FlickrAPI(api_key, api_secret, format='parsed-json')
""" END SETTINGS """	

photos_analysis([u'36717094514',u'36783353383', u'23601757988', u'36783729883', u'36783687273'])
