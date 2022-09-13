import requests
import re


if __name__ == '__main__':
    # image = cv2.imread("database/a_man_called_ove/image.jpg")
    # print('a')
    current_json = {
        "url": "https://www.imdb.com/title/tt3099498/"
    }
    response = requests.post("http://127.0.0.1:5000/add_movie", json=current_json).json()
    print(response)

