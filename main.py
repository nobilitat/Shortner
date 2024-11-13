import uvicorn
import sqlite3
import asyncio
import hashlib
import json
import uuid
import random
import datetime
import re


connection = sqlite3.connect('shrtdatabase.db')
cursor = connection.cursor()


def write_to_db(url, short_url):
    query = f'insert into Url values ("{uuid.uuid4()}", "{url}", "{short_url}", "{datetime.datetime.now()}")'
    cursor.execute(query)
    connection.commit()


def get_url_from_db(short_url):
    query = f'select full_url from Url where short_url = "{short_url}"'
    cursor.execute(query)
    url = next(cursor, [None])[0]
    return url


def generate_hash(url):
    salt = str(random.getrandbits(128))
    hsh = hashlib.sha256((url + salt).encode())
    return hsh.hexdigest()[:6]


async def url_create_endpoint(scope, receive, send):

    data = await receive()
    body = json.loads(data["body"])
    url = body["url"]

    hased_url = generate_hash(url)

    short_url = f'http://127.0.0.1:5000/{hased_url}'

    write_to_db(url, hased_url)

    response_body = {
        "short_url": short_url
    }

    response = {
        'method': 'POST',
        'path': '/url/add/',
        'type': 'http.response.start',
        'status': 200,
        'headers': [
            [b'content-type', b'application/json'],
        ]
    }

    await send(response)

    reponse = {
        'type': 'http.response.body',
        'body': json.dumps(response_body).encode()
    }

    await send(reponse)


async def url_get_endpoint(scope, receive, send):
    url_hash = re.search(r'(?<=get\/).+', scope["path"])
    url = get_url_from_db(url_hash.group())

    await send({
        'type': 'http.response.start',
        'status': 200
    })
    await send({
        'type': 'http.response.body',
        'body': url.encode()
    })


async def error_endpoint(scope, receive, send):
    await send({
        'path': '/',
        'type': 'http.response.start',
        'status': 400
    })
    await send({
        'path': '/',
        'type': 'http.response.body',
        'body': b'Bad request'
    })


async def root_endpoint(scope, receive, send):
    await send({
        'path': '/',
        'type': 'http.response.start',
        'status': 200,
        'headers': [
            [b'content-type', b'text/plain'],
        ],
    })
    await send({
        'path': '/',
        'type': 'http.response.body',
        'body': b'Shortner Service. \
            \nUse {host}/url/create for create url. \
            \nUse {host}/url/get for get url.'
    })


async def app(scope, receive, send):
    assert scope['type'] == 'http'

    if scope['path'] == '/' and scope['method'] == 'GET':
        await root_endpoint(scope, receive, send)

    elif scope['path'] == '/url/create/' and scope['method'] == 'POST':
        await url_create_endpoint(scope, receive, send)

    elif '/url/get/' in scope['path'] and scope['method'] == 'GET':
        await url_get_endpoint(scope, receive, send)

    else:
        await error_endpoint(scope, receive, send)


async def main():
    config = uvicorn.Config(app, host="127.0.0.1", port=5000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":

    asyncio.run(main())
