"""Hello World web app using Flask."""
import os
import platform

from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello():
    return f"""<!doctype html>
<html>
  <head><title>Python Hello World</title></head>
  <body style="font-family: system-ui, sans-serif; text-align: center; padding: 60px;">
    <h1>Hello World from Python (Flask)!</h1>
    <p>Running inside a Docker container.</p>
    <p>Python version: {platform.python_version()}</p>
  </body>
</html>"""


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    # host="0.0.0.0" is mandatory inside a container. The default 127.0.0.1
    # would only accept connections from inside the container itself, so
    # `docker run -p 5000:5000` would appear to do nothing.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
