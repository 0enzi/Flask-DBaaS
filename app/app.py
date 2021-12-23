from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from pymongo import MongoClient
import bcrypt


# Init Flask and API
app = Flask(__name__)
api = Api(app)

# Init DB connection
client = MongoClient("mongodb://db:27017")

# create a new DB named as aNewDB
db = client.DocumentsDB                 
users = db['Users']

def verifyPw(username, password):
    hashed_pw = users.find({"Username": username})[0]["Password"]

    if bcrypt.checkpw(password.encode("utf-8"), hashed_pw):
        return True
    else:
        return False
    
def TokenBalance(username):
    tokens = users.find({
        "Username": username
    })[0]["Tokens"]
    return tokens


class Register(Resource):
    def post(self):

        postedData = request.get_json()

        ################################################################
        #@############# USER DATA VALIDATION GOES HERE #################
        # Valid username and pass wont be deploying it since its a Proof-of-concept
        ################################################################
        username = postedData['username']
        password = postedData['password'] # imagine just dumping password into db like this
        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        
        users.insert_one({
            "Username": username,
            "Password": hashed_pw,
            "Document": "",
            "Tokens":10
        })

        return jsonify({
            "status":200,
            "message": "You have been successfully signed up"
        })


class Store(Resource):
    def post(self):
        postedData = request.get_json()

        #get user
        username = postedData["username"]
        password = postedData["password"]
        document = postedData["document"]

        #auth user
        correct_pw = verifyPw(username, password)

        if not correct_pw:
            return jsonify({
                "status":302,
                "message": "Invalid combination of username and password."
            })

        #verify user tokens
        token_balance = TokenBalance(username)

        if token_balance<=0:
            return jsonify({
                'status':301,
                "message": "Insufficient tokens to complete the request."
            })

        #store document
        users.update_one({
            "Username":username
            },
            {"$set": {
                "Document": document,
                "Token": token_balance-1
            }
        })

        return jsonify({
            "status":200,
            "message": "Document saved successfully",
            "token": token_balance
        })


class User(Resource):     
    def post(self):
        postedData = request.get_json()
        username = postedData["username"]
        user = users.find({"Username": username})[0]
        return jsonify({
            "Username": user["Username"],
            # "Password": user["Password"].decode("utf-8") dunno why you would want to this
            "Token": user["Token"],
            "Document": user["Document"]
        })



class Data(Resource):
    def get(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]

        correct_pw = verifyPw(username, password)

        if not correct_pw:
            return jsonify({"status": 302, "message": "Invalid combination of username and password"})

        
        token_balance = TokenBalance(username)

        if token_balance<=0:
            return jsonify({
                'status':301,
                "message": "Insufficient tokens to complete the request."
            })

        users.update_one({
            "Username":username
            },
            {"$set": {
                "Token": token_balance-1 #charge user for retrieving
            }
        })

        document = users.find({"Username": username})[0]["Document"]

        return jsonify({"document": document, "token_balance": token_balance})

# @app.route("/user", methods=["POST"])
# def user():
#     postedData = request.get_json(force=True)
#     username = postedData["username"]

#     print(users.find())
#     return jsonify({"Username": "user"})



api.add_resource(Register, '/register')
api.add_resource(Store, '/store')
api.add_resource(User, '/user')
api.add_resource(Data, '/retrive')


app.run(host="0.0.0.0", port="3000", debug=True)
