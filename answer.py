import sqlite3
from sqlite3 import Error
from transformers.pipelines import pipeline
from flask import Flask
from flask import request
from flask import json
from flask import jsonify
import time
import os

def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


# if __name__ == '__main__':
#    create_connection(r"Assignment2.db")
# print "Opened database successfully";


create_connection(r"Assignment1.db")

cnx = sqlite3.connect('Assignment1.db')
cursor = cnx.cursor()
cnx.execute('''CREATE TABLE if not exists models
          (name varchar(100),model varchar(100), tokenizer varchar(100));''')
cnx.execute('''
            INSERT INTO models (name, model, tokenizer)
            SELECT "distilled-bert","distilbert-base-uncased-distilled-squad","distilbert-base-uncased-distilled-squad"
            WHERE NOT EXISTS (SELECT * FROM models)
            ''')
cnx.execute('''CREATE TABLE if not exists answers
          (timestamp float, model varchar(100), answer varchar(100), question varchar(100), context varchar(100));''')


cnx.commit()
cnx.close()


# Create my flask app
app = Flask(__name__)

# cnx = sqlite3.connect('Assignment2.db')
#
# #Create a table
# cnx.execute('''CREATE TABLE models
#          (name varchar(100),model varchar(100), tokenizer varchar(100));''')
#
# cnx.execute('''INSERT INTO models (name, model, tokenizer) \
#             values ("distilled-bert","distilbert-base-uncased-distilled-squad","distilbert-base-uncased-distilled-squad")''')
# cnx.execute('''INSERT INTO models (name, model, tokenizer) \
#             values ("deepset-roberta","deepset/roberta-base-squad2","deepset/roberta-base-squad2")''')
# cnx.commit()
# cnx.close()


@app.route("/models", methods=['GET', 'PUT', 'DELETE'])
def models():
    if request.method == 'GET':
        cnx = sqlite3.connect('Assignment1.db')

        sql_select_query = "select * from models"
        cursor = cnx.cursor()
        cursor.execute(sql_select_query)
        records = cursor.fetchall()
        list1 = []

        for record in records:
            out = {
                "name": record[0],
                "tokenizer": record[1],
                "model": record[2]
            }
            list1.append(out)
        return json.jsonify(list1)
    elif request.method == 'PUT':

        data = request.json
        cnx = sqlite3.connect('Assignment1.db')

        cursor = cnx.cursor()
        name = data['name']
        model = data['model']
        tokenizer = data['tokenizer']

        cursor.execute("INSERT INTO models VALUES (?, ?, ?)", (name, model, tokenizer))

        cnx.commit()

        sql_select_query = "select * from models"
        cursor = cnx.cursor()
        cursor.execute(sql_select_query)
        records = cursor.fetchall()
        list2 = []

        for record in records:
            out = {
                "name": record[0],
                "tokenizer": record[1],
                "model": record[2]
            }
            list2.append(out)
        return json.jsonify(list2)
    elif request.method == 'DELETE':
        model_name = request.args.get("model")

        cnx = sqlite3.connect('Assignment1.db')
        cursor = cnx.cursor()
        cursor.execute("DELETE FROM models where name = ?", (model_name,))

        cnx.commit()

        sql_select_query = "select * from models"
        cursor = cnx.cursor()
        cursor.execute(sql_select_query)
        records = cursor.fetchall()
        list2 = []

        for record in records:
            out = {
                "name": record[0],
                "tokenizer": record[1],
                "model": record[2]
            }
            list2.append(out)
        return json.jsonify(list2)






# Define a handler for the / path, which
# returns "Hello World"
@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


# Define a handler for the /answer path, which
# processes a JSON payload with a question and
# context and returns an answer using a Hugging
# Face model.
@app.route("/answer", methods=['POST'])
def answer():
    # Get the request body data
    data = request.json
    model_nam = request.args.get("model")

    cnx = sqlite3.connect('Assignment1.db')
    cursor = cnx.cursor()
    cursor.execute("Select model, tokenizer FROM models where name = ?", (model_nam,))
    if model_nam == '':
        mod = "distilbert-base-uncased-distilled-squad"
        tok = "distilbert-base-uncased-distilled-squad"
    else:
        fetch = cursor.fetchall()
        mod = fetch[0][0]
        tok = fetch[0][1]


    # Import model
    hg_comp = pipeline('question-answering', model=mod,
                       tokenizer=tok)

    # Answer the answer
    ans = hg_comp({'question': data['question'], 'context': data['context']})['answer']

    # Get the score
    #score = hg_comp({'question': data['question'], 'context': data['context']})['score']

    # Get the timestamp
    timestamp = time.time()

    #Update answers
    cursor.execute("INSERT INTO answers VALUES (?, ?, ?, ?, ?)", (timestamp, mod, ans, data['question'], data['context']))
    cnx.commit()

    # Create the response body.
    out = {
        "timestamp": timestamp,
        "model": mod,
        "answer": ans,
        "question": data['question'],
        "context": data['context'],
    }


    return jsonify(out)


# Run if running "python answer.py"
if __name__ == '__main__':
    # Run our Flask app and start listening for requests!
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",8000)), threaded=True)

