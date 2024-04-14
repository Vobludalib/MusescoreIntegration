from flask import Flask, request

app = Flask(__name__)

@app.route('/plugin', methods=['POST', 'GET'])
def receive_path():
    if request.method == 'GET':
        return "CONNECTED!"
    if request.method == 'POST':
        print("RECEIVED CORRECT REQUEST!")
        print(request.data)
        return


@app.route('/', methods=['GET'])
def default():
    return "WRONG PAGE!"


if __name__ == '__main__':
    app.run(host="localhost")
