#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import shutil
import json
import types
import tweepy
import os
import sys
import re
import datetime
import numpy as np
import cv2
import time
import csv
from requests_oauthlib import  OAuth1Session
from PIL import Image

#twitterのAPIとか
consumer_key = "xxxxxxxxxxxxxxxxxxxxxxxxx"
consumer_secret = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
access_token = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
access_secret = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

url = "https://api.twitter.com/1.1/statuses/home_timeline.json"
params = {'count': 200}
sess = OAuth1Session(consumer_key,consumer_secret,access_token,access_secret)

#apiを取得
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth)

def create_canny_img(gray_img_src):
	ave_square = (5, 5)
	# x軸方向の標準偏差
	sigma_x = 1
	if type(img_src[0][0]) == np.ndarray:
		gray_img_src = cv2.cvtColor(gray_img_src, cv2.COLOR_BGR2GRAY)
	can_img = cv2.Canny(gray_img_src, 100, 200)

	gau_img = cv2.GaussianBlur(gray_img_src, ave_square, sigma_x)
	gau_can_img = cv2.Canny(gau_img, 100, 200)

	med_img = cv2.medianBlur(gray_img_src, ksize=5)
	med_can_img = cv2.Canny(med_img, 100, 200)

	return can_img, gau_can_img, med_can_img

def get_color(img_src):
	same_colors = {}
	if type(img_src[0][0]) == np.ndarray:
		for row in img_src:
			for at in row:
				at = tuple(at)
				if at in same_colors:
					same_colors[at] += 1
				else:
					same_colors[at] = 0
	else:
		for row in img_src:
			for at in row:
				if at in same_colors:
					same_colors[at] += 1
				else:
					same_colors[at] = 0

	result = max(same_colors.values()) / len(img_src)
	return result

def cal_diff(mat, c_mat):
	sum_mat = 0
	for m in mat:
		for n in m:
			sum_mat += n
	sum_mat /= 255
	diff = mat - c_mat
	sum_diff = 0
	for d in diff:
		for n in d:
			sum_diff += n
	sum_diff /= 255
	result = sum_diff / sum_mat

	return result

def cal_score(gau_result, med_result, color_result):
	result1 = gau_result + med_result
	return ((1 / result1) * 0.8 + (color_result / 100) * 0.2) * 0.625

def resize_img(img_name):
	img_src = cv2.imread(img_name, cv2.IMREAD_UNCHANGED)

	if len(img_src) > 2000 or len(img_src[0]) > 2000:
		img_src = cv2.resize(img_src,(len(img_src) // 2, len(img_src[0]) // 2))

	return img_src

def identifies_img(img_src,img_url):
	can_img, gau_can_img, med_can_img = create_canny_img(img_src)
	gau_result = cal_diff(can_img, gau_can_img)
	med_result = cal_diff(can_img, med_can_img)
	color_result = get_color(img_src)
	score = cal_score(gau_result, med_result, color_result)
	print("score :", round(score, 3) ,end=" --> ")
	if score >= 0.545:
		save_url = file_url.replace('./tw_img/','./tw_img/illust/')
		shutil.move(file_url,save_url)
		return "illust"
	elif score <= 0.4:
		save_url = file_url.replace('./tw_img/','./tw_img/photo/')
		shutil.move(file_url,save_url)
		return "photo"
	else:
		save_url = file_url.replace('./tw_img/','./tw_img/unknown/')
		shutil.move(file_url,save_url)
		return "unknown"

def dl_img(img_url):
	r = requests.get(img_url, stream=True)
	file_name = img_url.replace('http://pbs.twimg.com/media/','./tw_img/')
	path = file_name.replace('./tw_img/','')
	if os.path.exists('./tw_img/illust/'+path) or os.path.exists('./tw_img/photo/'+path) or os.path.exists('./tw_img/unknown/'+path):
		return 'already'
	#print (file_name)
	print(path,end=" | ")
	if r.status_code == 200:
		with open(file_name, 'wb') as f:
			r.raw.decode_content = True
			shutil.copyfileobj(r.raw, f)
		return file_name

def get_timeline():
	req = sess.get(url, params = params)
	timeline = json.loads(req.text)
	#print (dir(timeline[0]))

	for tweet in timeline:
		#print (tweet)
		if 'RT' in tweet['text']:
			continue
		elif 'Twitter Web Client' in tweet['source']:
			if 'extended_entities' in tweet:
				if tweet['extended_entities']['media']:
					#print ("--------------------------------")
					#print (tweet['text'])
					#print(tweet['user']['screen_name'])
					#print (tweet['id'])
					for k in tweet['extended_entities']['media']:
						for i in k:
							if i == 'media_url':
								#print (k['media_url'])
								global img_src
								global file_url
								img_url = k['media_url']
								if 'video' in img_url:
									break
								file_url = dl_img(img_url)
								if file_url == "already":
									break
								img_src = resize_img(file_url)
								result = identifies_img(img_src,img_url)
								
								print (result)
								break

if __name__ == "__main__":
	try:
		get_timeline()		
	except Exception as e:
		print(e)
