from flask import Flask, request
app = Flask(__name__, static_url_path='')

@app.route('/')
def root():
	return app.send_static_file('monitor.html')

app.run()