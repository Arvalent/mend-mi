import tensorflow as tf
from einops import repeat
from transformers import BertTokenizer, TFBertModel
from image_description.predict import predict
from bs4 import BeautifulSoup
import subprocess
import requests
import shutil



tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
model = TFBertModel.from_pretrained("bert-base-uncased")

def embeddings_from_descriptions(descriptions):

    inputs = tokenizer(descriptions, return_tensors='tf', padding=True)
    outputs = model(inputs)
    last_hidden_states = outputs.last_hidden_state
    return .5 * (last_hidden_states[:, 0] + tf.math.reduce_mean(last_hidden_states[:, 1 : ], axis=1))


def descriptions_from_images(image_files):

    return [predict(im).replace('start ','').replace('end','') for im in image_files]


def embeddings_from_images(image_files):

    descriptions = descriptions_from_images(image_files)
    return embeddings_from_descriptions(descriptions)


def extract_image_from_url(url, image_code):

    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(f"temp_{image_code}.jpg", 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
        return True
    return False


def find_locations(image_files):
    pass


def image_query(tags, location, embeddings):

    image_codes = []
    files = []

    for k, tag in enumerate(tags):

        query = f"https://www.google.com/search?q={'+'.join(tag.split(' ') + location.split(' '))}&tbm=isch"
        html_page = requests.get(query)
        soup = BeautifulSoup(html_page.content, 'html.parser')
        image_tags = soup.find_all('img')[ : 5]

        for l, im in enumerate(image_tags):
            url_ext = im.attrs['src']
            full_url = query + url_ext
            image_code = '_'.join([str(k), str(l)])
            if extract_image_from_url(full_url, image_code):
                image_codes.append((k, l))
                files.append(f"temp_{image_code}.jpg")
        
        embeddings_search = embeddings_from_images(files)
        embeddings = repeat(embeddings, 'b c -> b n c', n=embeddings_search.shape[0])
        embeddings_search = repeat(embeddings_search, 'n c -> b n c', b=embeddings.shape[0])
        diff = tf.norm(embeddings - embeddings_search, axis=-1)
        best_locations = tf.argsort(diff, axis=1)[:10]
        proposed_locations = find_locations(files[best_locations])
        indices = image_codes[best_locations]
        tasks = [tags[k[0]] for k in indices]

        for f in files:
            subprocess.run(['rm', '-r', f])
        
        return proposed_locations, tags

