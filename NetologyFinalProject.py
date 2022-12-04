import requests
from datetime import datetime
import json
from tqdm import tqdm


class VK:

    def __init__(self, access_token, user_id, version='5.131'):
        self.token = access_token
        self.id = user_id
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

    def users_info(self):
        url = 'https://api.vk.com/method/users.get'
        params = {'user_ids': self.id}
        response = requests.get(url, params={**self.params, **params})
        return response.json()

    def get_photos(self, numb_of_img=5):
        url = 'https://api.vk.com/method/photos.get'
        params = {'owner_id': self.id, 'album_id': 'profile', 'extended': '1', 'photo_sizes': '1'}
        response = requests.get(url, params={**self.params, **params}).json()
        photos_dict = {}
        count = 0
        for each_photo in response['response']['items']:
            if str(each_photo['likes']['count']) not in photos_dict.keys():
                photos_dict[str(each_photo['likes']['count'])] = each_photo['sizes']
            else:
                photos_dict[str(each_photo['likes']['count']) + ' ' + datetime.utcfromtimestamp(each_photo['date']).strftime('%d.%m.%Y')] = each_photo['sizes']
            count += 1
            if count == numb_of_img:
                break
        return photos_dict

    def sort_photos(self):
        photos_dict = self.get_photos()
        for each_photo_name in tqdm(photos_dict, desc='Getting and sorting images from vk.com', bar_format='{desc} {bar} {percentage}%'):
            size_dict = {}
            for size in photos_dict[each_photo_name]:
                size_dict[size['height']] = [size['type'], size['url']]
            biggest_size = sorted(size_dict.items())[-1][1]
            photos_dict[each_photo_name] = biggest_size
        return photos_dict


class Yandex:

    def __init__(self, ya_token):
        self.ya_token = ya_token
        self.url = 'https://cloud-api.yandex.net/v1/disk/resources'
        self.headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'OAuth {self.ya_token}'}

    def create_folder(self):
        res = requests.put(f'{self.url}?path="ФотоРезерв"', headers=self.headers)
        if res.status_code != 201 and res.status_code != 409:
            print(res.json()['message'])

    def upload_image(self, file_name, file_url, replace=True):
        res = requests.get(f'{self.url}/upload?path="ФотоРезерв"/{file_name}.jpg&overwrite={replace}', headers=self.headers).json()
        img = requests.get(file_url).content
        download_link = res['href']
        try:
            requests.put(download_link, files={'file': img})
        except KeyError:
            print(res)

    def upload_images(self, files):
        self.create_folder()
        uploaded_files = []
        for each_file in tqdm(files, desc='Uploading images to YandexDisk', bar_format='{desc} {bar} {percentage}% | {n_fmt}/{total_fmt} images uploaded'):
            self.upload_image(each_file, files[each_file][1])
            size = files[each_file][0]
            uploaded_files += [{"file_name": f'{each_file}.jpg', "size": f'{size}'}]
        with open('uploaded_files.json', 'w') as json_file:
            json.dump(uploaded_files, json_file, indent=4)


vk_access_token = input('Введите токен ВК: ')
ya_token = input('Введите токен с Яндекс Полигона: ')
user_id = input('Введите ID пользователя ВК: ')

vk_user = VK(vk_access_token, user_id)
ya_user = Yandex(ya_token)
ya_user.upload_images(vk_user.sort_photos())
