from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '''
    <html>
        <body>
            <h1 style="color: blue;">Hello World</h1>
            <p>If you can see this, the Flask server is working!</p>
        </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(debug=True, port=3000)
