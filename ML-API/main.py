import re
from CaptionDataset import Vocabulary
from model import *
from flask import Flask, jsonify, request
import cv2
import numpy as np
import torchvision.transforms as transforms
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
from AttModel import *
from config import *
import pickle
import torch.nn.functional as F
from mysql.connector import connect
from mysql.connector import Error
import PIL.Image as Image
import io
from base64 import encodebytes
import datetime
import sqlalchemy as db
import tensorflow as tf
from tensorflow import keras
import os
import pandas as pd
import random
from urllib.parse import quote_plus

app = Flask(__name__)

prev_model = None
encoder, decoder = None, None
vocab = None
sim_model = SentenceTransformer("stsb-roberta-large")
keyword_model = sim_model
word2idx = None
idx2word = None


users = dict()
newData = {}

starttime = datetime.datetime.now()
'''
Task: caption-image
Description: captions a minecraft image, returns the feedback, score, and generated caption
'''
@app.route('/caption-image', methods=["POST"])
def caption_image():
    # Body info from request
    imgData = request.files['image'].read()
    userCaption = request.form['user-caption']

    versionNum = 2
    try:
        versionNum = int(request.form['version'])
    except:
        versionNum = 2
    print(versionNum)

    numData = np.fromstring(imgData, np.uint8)
    image = cv2.imdecode(numData, cv2.IMREAD_COLOR)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Caption Image
    image = tranformImage(image)
    if versionNum == 2:
        caption = caption_image_beam_search(encoder, decoder, image, word2idx)
        caption = " ".join(caption[1: len(caption) - 1])
    if versionNum == 1:
        caption = caption_no_attention(image)

    # Score caption
    allObservations = [userCaption, caption]
    embed = sim_model.encode(allObservations)
    sim = cosine_similarity([embed[len(allObservations)-1]], embed[:len(allObservations)-1])
    score = sim[0][0]

    # TODO: Store image (byte-data), caption, user, score
    user = None
    try:
        user = request.form['user']
    except:
        print("No user provided")

    # Return feedback
    n_gram_range = (1, 1)
    count = CountVectorizer(ngram_range=n_gram_range, stop_words="english").fit([caption])
    candidates = count.get_feature_names()
    doc_embedding = keyword_model.encode([caption])
    candidate_embeddings = keyword_model.encode(candidates)
    distances = cosine_similarity(doc_embedding, candidate_embeddings)
    keywords = [candidates[index] for index in distances.argsort()[0][-NUM_KEYWORDS:]]

    if versionNum == 2:
        if score >= SCORE_THRESHOLD:
            feedback = "Great job! You noticed the " + keywords[0] + "."
        else:
            feedback = "Try again! Did you notice the " + keywords[0] + "."
    if versionNum == 1:
        if score >= SCORE_THRESHOLD:
            feedback = "Great job!"
        else:
            feedback = "Try again!"

    storeInfo(imgData,userCaption, caption, score, user, feedback)  
    
    return jsonify({"user":user,"user caption":userCaption, "generated caption": caption, "score": float(score), "feedback": feedback})


@app.route("/all-users", methods=["GET"])
def get_users():
    ## TODO: Call the DB and get all users
    return jsonify({"users": []})

@app.route("/create-feedback", methods=["POST"])
def create_feedback():
    #Collect Data
    user_caption = request.form["user-caption"]
    generated = request.form["generated-caption"]
    version = int(request.form["version"])

    # Score caption
    allObservations = [user_caption, generated]
    embed = sim_model.encode(allObservations)
    sim = cosine_similarity([embed[len(allObservations)-1]], embed[:len(allObservations)-1])
    score = sim[0][0]

    # Return feedback
    n_gram_range = (1, 1)
    count = CountVectorizer(ngram_range=n_gram_range, stop_words="english").fit([generated])
    candidates = count.get_feature_names()
    doc_embedding = keyword_model.encode([generated])
    candidate_embeddings = keyword_model.encode(candidates)
    distances = cosine_similarity(doc_embedding, candidate_embeddings)
    keywords = [candidates[index] for index in distances.argsort()[0][-NUM_KEYWORDS:]]

    if version == 2:
        if score >= SCORE_THRESHOLD:
            feedback = "Great job! You noticed the " + keywords[0] + "."
        else:
            feedback = "Nice Job but did you notice the " + keywords[0] + "." 
    
    if version == 1:
        if score >= SCORE_THRESHOLD:
            feedback = "Good Job!"
        else:
            feedback = "Try Again!"
            
    return jsonify({"feedback": feedback})


def storeInfo(image, usercaption,caption, score, user,feedback):
    global newData
    userdata = dict()
    userdata['user'] = user
    encoded = encodebytes(image).decode("ascii")
    userdata['image'] = encoded
    userdata["usercaption"] = usercaption
    userdata["caption"] = caption
    userdata["score"] = str(score)
    userdata["feedback"] = feedback

    if (user not in users.keys() or users[user] != userdata): 
        newData = userdata.copy()
        users[user] = userdata
    else:
        newData = {}

@app.route("/getData", methods=["GET"])
def getData():
    global starttime
    if (datetime.datetime.now() > starttime + datetime.timedelta(hours=20)):
        print("Deleting all user data")
        starttime = datetime.datetime.now()
    global newData
    userdata = newData.copy()
    newData = {}
    return jsonify({"userdata": userdata})

def caption_image_beam_search(encoder, decoder, image, word_map, beam_size=3):
    """
    Reads an image and captions it with beam search.
    :param encoder: encoder model
    :param decoder: decoder model
    :param image: the image
    :param word_map: word map
    :param beam_size: number of sequences to consider at each decode-step
    :return: caption, weights for visualization
    """

    k = beam_size
    vocab_size = len(word_map)

    # Encode
    image = image.unsqueeze(0)  # (1, 3, 256, 256)
    encoder_out = encoder(image)  # (1, enc_image_size, enc_image_size, encoder_dim)
    enc_image_size = encoder_out.size(1)
    encoder_dim = encoder_out.size(3)

    # Flatten encoding
    encoder_out = encoder_out.view(1, -1, encoder_dim)  # (1, num_pixels, encoder_dim)
    num_pixels = encoder_out.size(1)

    # We'll treat the problem as having a batch size of k
    encoder_out = encoder_out.expand(k, num_pixels, encoder_dim)  # (k, num_pixels, encoder_dim)

    # Tensor to store top k previous words at each step; now they're just <start>
    k_prev_words = torch.LongTensor([[word_map['<start>']]] * k) # (k, 1)

    # Tensor to store top k sequences; now they're just <start>
    seqs = k_prev_words  # (k, 1)

    # Tensor to store top k sequences' scores; now they're just 0
    top_k_scores = torch.zeros(k, 1)  # (k, 1)

    # Tensor to store top k sequences' alphas; now they're just 1s
    seqs_alpha = torch.ones(k, 1, enc_image_size, enc_image_size) # (k, 1, enc_image_size, enc_image_size)

    # Lists to store completed sequences, their alphas and scores
    complete_seqs = list()
    complete_seqs_alpha = list()
    complete_seqs_scores = list()

    # Start decoding
    step = 1
    h, c = decoder.init_hidden_state(encoder_out)

    # s is a number less than or equal to k, because sequences are removed from this process once they hit <end>
    while True:

        embeddings = decoder.embedding(k_prev_words).squeeze(1)  # (s, embed_dim)

        awe, alpha = decoder.attention(encoder_out, h)  # (s, encoder_dim), (s, num_pixels)

        alpha = alpha.view(-1, enc_image_size, enc_image_size)  # (s, enc_image_size, enc_image_size)

        gate = decoder.sigmoid(decoder.f_beta(h))  # gating scalar, (s, encoder_dim)
        awe = gate * awe

        h, c = decoder.decode_step(torch.cat([embeddings, awe], dim=1), (h, c))  # (s, decoder_dim)

        scores = decoder.fc(h)  # (s, vocab_size)
        scores = F.log_softmax(scores, dim=1)

        # Add
        scores = top_k_scores.expand_as(scores) + scores  # (s, vocab_size)

        # For the first step, all k points will have the same scores (since same k previous words, h, c)
        if step == 1:
            top_k_scores, top_k_words = scores[0].topk(k, 0, True, True)  # (s)
        else:
            # Unroll and find top scores, and their unrolled indices
            top_k_scores, top_k_words = scores.view(-1).topk(k, 0, True, True)  # (s)

        # Convert unrolled indices to actual indices of scores
        prev_word_inds = top_k_words // vocab_size  # (s)
        next_word_inds = top_k_words % vocab_size  # (s)

        # Add new words to sequences, alphas
        seqs = torch.cat([seqs[prev_word_inds], next_word_inds.unsqueeze(1)], dim=1)  # (s, step+1)
        seqs_alpha = torch.cat([seqs_alpha[prev_word_inds], alpha[prev_word_inds].unsqueeze(1)],
                               dim=1)  # (s, step+1, enc_image_size, enc_image_size)

        # Which sequences are incomplete (didn't reach <end>)?
        incomplete_inds = [ind for ind, next_word in enumerate(next_word_inds) if
                           next_word != word_map['<end>']]
        complete_inds = list(set(range(len(next_word_inds))) - set(incomplete_inds))

        # Set aside complete sequences
        if len(complete_inds) > 0:
            complete_seqs.extend(seqs[complete_inds].tolist())
            complete_seqs_alpha.extend(seqs_alpha[complete_inds].tolist())
            complete_seqs_scores.extend(top_k_scores[complete_inds])
        k -= len(complete_inds)  # reduce beam length accordingly

        # Proceed with incomplete sequences
        if k == 0:
            break
        seqs = seqs[incomplete_inds]
        seqs_alpha = seqs_alpha[incomplete_inds]
        h = h[prev_word_inds[incomplete_inds]]
        c = c[prev_word_inds[incomplete_inds]]
        encoder_out = encoder_out[prev_word_inds[incomplete_inds]]
        top_k_scores = top_k_scores[incomplete_inds].unsqueeze(1)
        k_prev_words = next_word_inds[incomplete_inds].unsqueeze(1)

        # Break if things have been going on too long
        if step > 50:
            break
        step += 1

    i = complete_seqs_scores.index(max(complete_seqs_scores))
    seq = complete_seqs[i]
    alphas = complete_seqs_alpha[i]

    words = [idx2word[s] for s in seq]
    return words


def caption_no_attention(image):
    i = image.unsqueeze(0)
    caption = prev_model.caption_image(i, vocab)
    caption = " ".join(caption[1:len(caption) - 1])
    return caption

def tranformImage(image):
    preprocess = transforms.Compose([
        transforms.ToTensor(),
        transforms.CenterCrop(256 * 5),
        transforms.Resize((256, 256))
    ])
    image = preprocess(image)
    return image

def run_habitat_models(world, users):
    username = 'research'
    password = 'Cr@ft!ng_188P'
    if "@" in password:
        password = quote_plus(password)
    host = '192.17.80.98'
    port = '3306'
    #database = 'db?useSSL=false'
    database = 'researchdb'
    engine = None
    #Connector to db
    if "?useSSL=false" in database:
        database = database.split('?')[0]
        engine = db.create_engine('mysql+mysqlconnector://' + username + ':' + password+'@' + host + ':' + port + '/' + database, connect_args={'ssl_disabled': 'True'})
    else:
        engine = db.create_engine('mysql+pymysql://' + username + ':' + password+'@' + host + ':' + port + '/' + database)
    meta = db.MetaData()
    db.MetaData.reflect(meta, bind=engine)
    worlds = meta.tables['co_world']
    query_worlds = db.select(
    worlds.c.id
    ).where((worlds.c.world == world))
    wid_result = None
    with engine.connect() as conn:
        wid_result = conn.execute(query_worlds).fetchall()
    #users = request.form['teammates']
    #print(wid_result)
    #print(users)
    #Get mapping user id to user name
    user_map = meta.tables['co_user']
    user_result = []
    for i in range(len(users)):
        user_query = db.select(
        user_map.c.rowid
        ).where((user_map.c.user == users[i]))
        with engine.connect() as conn:
            user_result.append(conn.execute(user_query).fetchall())
    #print(user_result)   
    #Get blocks from worlds of interest
    blocks = meta.tables['co_block']
    block_result = []
    for i in range(len(user_result)):
        query_blocks = db.select(
        blocks.c.type,
        ).where((blocks.c.wid == wid_result[0][0]) & (blocks.c.user == user_result[i][0][0]))
        with engine.connect() as conn:
            block_result.append(conn.execute(query_blocks).fetchall())

    #Get mapping of block type id to block name
    material_map = meta.tables['co_material_map']
    material_query = db.select(
        material_map.c.id,
        material_map.c.material,
    )
    material_result = None
    with engine.connect() as conn:
        material_result = conn.execute(material_query).fetchall()
    materials = []
    for i in range(len(block_result)):
        for j in range(len(block_result[i])):
            block_id = block_result[i][j]
            material = material_result[block_id[0] - 1]
            materials.append(material)
    df = pd.DataFrame(materials, columns = ['Block_id', 'Block_Type'])
    blocks = df.Block_Type.unique()
    counts = df.Block_Type.value_counts()
    block_counts = pd.DataFrame(columns = blocks)
    #print(block_counts)
    for i, v in counts.items():
        block_counts.at[0,i] = v
    block_dataset = pd.read_csv("block_counts.csv", index_col = 'id')
    block_dataset = block_dataset.dropna(axis=1, how='all')
    block_dataset = block_dataset.fillna(0)
    block_counts = block_counts.reindex(block_dataset.columns,axis=1)
    block_counts = block_counts.fillna(0)
    
    # Normalize block counts to the training distribution of each column
    normalized_counts = block_counts.copy()

    # Use the exact training columns and avoid iteritems() (removed in pandas 2)
    for name in block_dataset.columns:
        col_min = block_dataset[name].min()
        col_max = block_dataset[name].max()
        denom = (col_max - col_min)
        if denom == 0 or pd.isna(denom):
            # If a column was constant in training, set to 0.0 (or whatever your model expects)
            normalized_counts[name] = 0.0
        else:
            normalized_counts[name] = (normalized_counts[name] - col_min) / denom

    directory = "models"
    results = {}
    # Convert once to the dtype Keras expects
    x = normalized_counts.to_numpy(dtype=np.float32)  # shape (1, num_features)
    for file in os.listdir(directory):
        model = tf.keras.models.load_model(os.path.join(directory, file), compile=False)
        pred = model.predict(x, verbose=0)
        results[file] = int(np.argmax(pred, axis=1)[0])
    return results
#chatgpt told me to put this here --Jeff
@app.get("/healthz")
def healthz():
    return {"status": "ok"}
'''
Task: Assess habitat
Description: Gets base info to call db and retrieve blocks, returns randomized highest and lowest categories for feedback
'''
@app.route('/assess-habitat', methods=["POST"])
def assess_habitat():
    interaction_id = request.form['id']
    user = request.form['user']
    world = request.form['world']
    teammates = request.form['teammates']
    users = teammates.split(",")
    results = run_habitat_models(world, users)
    print(results)
    min_val = list(results.values())[0]
    max_val = list(results.values())[0]
    min_indices = []
    max_indices = []
    for i in range(len(list(results))):
        curr = list(results.values())[i]
        if curr < min_val:
            min_val = curr
            min_indices = [i]
        elif curr == min_val:
            min_indices.append(i)
        if curr > max_val:
            max_val = curr
            max_indices = [i]
        elif curr == max_val:
            max_indices.append(i)
    random_lowest_index = min_indices[random.randint(0, len(min_indices)-1)]
    low_category = list(results)[random_lowest_index]
    lowest_category = low_category.replace('.h5', '')
    
    random_highest_index = max_indices[random.randint(0, len(max_indices)-1)]
    high_category = list(results)[random_highest_index]
    highest_category = high_category.replace('.h5', '')
    
    area = int(results["area.h5"])
    communications_facilities = int(results["communications_facilities.h5"])
    food = int(results["food.h5"])
    gravity = int(results["gravity.h5"])
    health = int(results["health.h5"])
    oxygen_regulation = int(results["oxygen_regulation.h5"])
    power_generation = int(results["power_generation.h5"])
    radiation_protection = int(results["radiation_protection.h5"])
    supplies = int(results["supplies.h5"])
    shape = int(results["shape.h5"])
    transportation = int(results["transportation.h5"])
    return jsonify({"id": interaction_id, "user": user,"lowestcategory": lowest_category,"highestcategory": highest_category,
                    "area": area, "communicationsfacilities": communications_facilities, "food": food, "gravity": gravity,
                    "health": health, "oxygenregulation": oxygen_regulation, "powergeneration": power_generation, "radiationprotection": radiation_protection,
                    "supplies": supplies, "shape": shape, "transportation": transportation})

if __name__ == "__main__":
    vocab = Vocabulary(1)
    vocab.loadVocabList(ITOS_PATH, STOI_PATH)
    prev_model = CNNtoRNN(512, 512, len(vocab), 1)
    prev_model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device('cpu')))
    prev_model.eval()

    with open("saved_vocab.pkl", "rb") as f:
        word2idx = pickle.load(f)
    
    idx2word = {v: k for k, v in word2idx.items()}
    encoder = Encoder()
    decoder = DecoderWithAttention(512, 512, 512, len(word2idx))

    encoder.load_state_dict(torch.load("Encoder.pth", map_location=torch.device("cpu")))
    decoder.load_state_dict(torch.load("Decoder.pth", map_location=torch.device("cpu")))

    encoder.eval()
    decoder.eval()


    app.run(HOST, port=PORT)
