import requests
import json
from urllib.parse import urlencode
import random
import configparser
import logging


def photos_to_backup (js,photo_count=5):
  logging.debug (f'загрузка {photo_count} фото')
  photos_name  = {}
  photos_list =  js.get('response', {}).get('items', [])
  for photo in photos_list [0:photo_count]:
    sizes = photo.get('sizes', [])
    if len(sizes) == 0:
      logging.warn(f'у фото с ид {photo.get('id',"")} не указаны размеры, пропускаем')
      continue
    sizes_sorted = sorted(sizes, key=lambda d: d['type'], reverse=True)
    needed_photo = sizes_sorted [0]
    photo_url = needed_photo.get('url', "")
    if photo_url == "":
      logging.warn(f'у фото с ид {photo.get('id',"")} нет урл, пропускаем')
      continue
    likes = photo.get('likes', {}).get('count', 0)
    load_date = photo.get('date',0)
    photo_name = f'{likes}.jpg'
    if photo_name in photos_name:
      photo_name = f'{likes}_{load_date}.jpg'
    if photo_name in photos_name:
      photo_name = f'{likes}_{load_date}_{random.randrange(1000)}.jpg'
    photos_name[photo_name] = {"photo_url":photo_url,"photo_type":needed_photo["type"] }
  logging.debug(f'фото для бэкапа {photos_name}')
  return photos_name

class Yandex:

  base_url = 'https://cloud-api.yandex.net'
 
  def __init__(self, token):
    self.headers = {'Authorization': 'OAuth ' + token}

  def create_folder(self, folder_name="Image"):
    self.url_create_folder = self.base_url + '/v1/disk/resources'
    self.folder_name = folder_name
    self.params = {
      'path': self.folder_name
    }
    response = requests.put(self.url_create_folder, params=self.params, headers=self.headers)
    return response
  
  def upload_photo(self, photo_name,photo_url):
    self.url_upload= self.base_url + '/v1/disk/resources/upload'
    self.params = {
      'path': f'{self.folder_name}/{photo_name}',
      'url':photo_url
    }

    response = requests.post(self.url_upload, params=self.params, headers=self.headers)
    return response
  
class Vkontakte:

  base_url = 'https://api.vk.ru/method'
 
  def __init__(self, token,id):
    self.params = {
      'access_token': token,
      'owner_id': id
    }
  
  def get_photos(self):
    self.url_get_photoes= self.base_url + '/photos.get'
    self.params["album_id"] = 'profile'
    self.params["extended"] = '1'
    self.params["photo_sizes"] = '1'
    self.params["v"] = '5.199'
    response = requests.get(self.url_get_photoes, params=self.params)
    return response  


if __name__ == '__main__':
  
  logging.basicConfig(level=logging.INFO, filename="py_log.log")
  logging.info ("start backuping!")
  config = configparser.ConfigParser()
  config.read("settings.ini")
  yd_conf = config["YD"]
  vk_conf = config["VK"]
  vk_obj = Vkontakte (vk_conf["TOKEN"],vk_conf["OWNER_ID"])
  response = vk_obj.get_photos()
  if 200<=response.status_code<300:
    logging.debug ("get photoes from vk")
    photos_load = photos_to_backup (response.json(),3)
    if len(photos_load)>0:
      ya_obj = Yandex (yd_conf["TOKEN"])
      resp = ya_obj.create_folder()
      if 200<=resp.status_code<300:
        logging.debug ("create yd folder")
        backuped_photos = []
        for photo_data in photos_load.items():
          resp = ya_obj.upload_photo(photo_data[0],photo_data[1]["photo_url"])
          if 200<=resp.status_code<300:
            backuped_photos.append ({"file_name": photo_data[0],"size": photo_data[1]["photo_type"]})
          else:
            logging.error(f'not uploaded photo {photo_data[0]} reason {resp.json()}')  
        if len (backuped_photos)>0:
          with open('backuped_photos.json',"w", encoding="utf-8") as f1:
            json.dump(backuped_photos,f1)
            logging.info ("finish backuping - good!")
        else:
          logging.error(f'no uploaded photoes')
      else:
        logging.error(f'not created folder {resp.json()}')
    else:
      logging.error ("no foto to backup!")
  else:
    logging.error (f'no get photos {response.json()}')    




  












