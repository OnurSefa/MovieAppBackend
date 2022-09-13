from flask import Flask, request, Response
from flask_cors import CORS
import os
import jsonpickle
import re
import requests

app = Flask(__name__)
CORS(app)


def parser(url):
    neu_response = {
        "original_name": "",
        "img_url": "",
        "imdb_url": url,
        "rating": "",
        "date": "",
        "minutes": "",
        "genres": []
    }

    try:
        response = requests.get(url)
        current_text = response.content.decode("utf-8")
    except:
        return neu_response

    try:
        prev_text = current_text
        pattern_content = "contentUrl"
        pattern_context = "@context"
        start_index = re.search(pattern_context, current_text).span()[0]
        end_index = re.search(pattern_content, current_text).span()[1]
        current_text = current_text[start_index:end_index]

        original_name_indices = re.search("\"name\":\".*?\"", current_text).span()
        original_name = current_text[original_name_indices[0] + 8: original_name_indices[1] - 1]
        rating_parser_indices = re.search("aggregateRating", current_text).span()
        rating_text_area = current_text[rating_parser_indices[0]:]
        rating_indices = re.search("ratingValue\":.*?}", rating_text_area).span()

        first_area = current_text[:rating_parser_indices[0]]
        rating = rating_text_area[rating_indices[0] + 13:rating_indices[1] - 1]
        genre_indices = re.search("genre.*?]", rating_text_area).span()
        genre_texts = rating_text_area[genre_indices[0] + 8: genre_indices[1] - 1]

        genres = re.findall("\".*?\"", genre_texts)
        for g in range(len(genres)):
            genres[g] = genres[g][1:-1]

        date_indices = re.search("datePublished\":\".*?\"", rating_text_area).span()
        date = rating_text_area[date_indices[0] + 16: date_indices[1] - 1]

        img_url_indices = re.search("image\":\".*?\"", first_area).span()
        img_url = first_area[img_url_indices[0] + 8: img_url_indices[1] - 1]

        minutes_parser_indices = re.search(">minutes<", prev_text).span()
        minutes_text = prev_text[minutes_parser_indices[0] - 90:minutes_parser_indices[1]]
        hour_indices = re.search(">[0-9]+<!", minutes_text).span()
        hour_text = minutes_text[hour_indices[0]:hour_indices[1]]
        hour = int(hour_text[1:-2])
        minutes_text = minutes_text[hour_indices[1]:]
        minutes_indices = re.search(">[0-9]+<", minutes_text).span()
        minutes = int(minutes_text[minutes_indices[0] + 1:minutes_indices[1] - 1])
        total_time = 60 * hour + minutes

        name_indices = re.search("name\":\".*?\"", rating_text_area).span()
        name = rating_text_area[name_indices[0] + 7: name_indices[1] - 1]
    except:
        return neu_response

    neu_response["original_name"] = original_name
    neu_response['rating'] = rating
    neu_response['img_url'] = img_url
    neu_response['minutes'] = total_time
    neu_response['date'] = date
    neu_response['genres'] = genres

    return neu_response


def write_to_db(movie_info):
    name = movie_info['original_name'].replace(" ", "_")
    if name != "":
        current_movies = os.listdir("database")
        if name not in current_movies:
            os.mkdir("database/"+name)
        lines = list()
        lines.append(movie_info['original_name'])
        lines.append(movie_info['img_url'])
        lines.append(movie_info['imdb_url'])
        lines.append(movie_info['minutes'])
        lines.append(movie_info['date'])
        genres = ""
        for genre in movie_info['genres']:
            genres += genre + "_"
        if len(genres) >= 2:
            genres = genres[:-1]
        lines.append(genres)
        with open("database/"+name+"/info.txt", 'w') as current_file:
            for line in lines:
                current_file.write(str(line)+"\n")
        return 1
    else:
        return -1


@app.route("/add_movie", methods=["POST"])
def add_movie():
    request_json = request.get_json()
    parsed_info = parser(request_json['url'])
    status = write_to_db(parsed_info)

    return parsed_info


@app.route("/take_movies", methods=["POST"])
def take_movies():
    movie_names = os.listdir("database")
    movies = []
    for movie_name in movie_names:

        with open("database/{}/info.txt".format(movie_name), 'r') as txt_file:
            lines = txt_file.readlines()

        neu_movie = {
            "original_name": lines[0][:-1],
            "image_url": lines[1][:-1],
            "imdb_url": lines[2][:-1],
            "minutes": lines[3][:-1],
            "date": lines[4][:-1],
            "genres": lines[5][:-1].split("_")
        }

        movies.append(neu_movie)

    pickled_response = jsonpickle.encode({"movies": movies})

    return Response(response=pickled_response, status=200, mimetype='application/json')


if __name__ == '__main__':
    try:
        os.mkdir("database")
    except:
        pass

    app.run(debug=True, host='0.0.0.0')
