from flask import Flask, g, session, redirect
import subprocess

app = Flask(__name__)
app.secret_key = 'BAD_SECRET_KEY'
print("Setting to false")


@app.route('/')
def hello_world():
    global process
    process = None
    session["building"] = False
    session["pushable"] = False
    session["pushing"] = False
    return 'This is the main page. Check status: <a href="/live">Status<//a>'


@app.route("/status")
def status():
    global process
    if "building" not in session:
        session["building"] = False
    if session["building"]:
        if process is None:
            return "No Process found. How did we get here?"
        elif process.poll() is None:
            return 'building'
        else:
            if process.poll() != 0:
                session["building"] = False
                session["pushable"] = False
                return "error"
            else:
                session["building"] = False
                session["pushable"] = True
            return "Done"
    if session["pushing"]:
        if process is None:
            return "No Process found during push check?"
        elif process.poll() is None:
            return 'pushing'
        else:
            if process.poll() != 0:
                session["pushing"] = False
                session["pushable"] = False
                return "error"
            else:
                session["pushing"] = False
                session["pushable"] = False
                return "Done"
    return "idle"


@app.route("/build")
def build():
    global process
    if "building" not in session:
        session["building"] = False
    if session['building']:
        return "Already building, come back later"
    else:
        session["building"] = True
        session["pushable"] = False
        # proc = subprocess.Popen(
        #     ["python", "-c", "import time; time.sleep(5), print('temp')"])
        proc = subprocess.Popen(["bash", "full_build.sh"])
        if process is None:
            process = proc
        return redirect("/live", 302)


@app.route("/push")
def push():
    global process
    if not session["pushable"]:
        return "Can't push yet."
    else:
        session["pushable"] = False
        session["pushing"] = True
        process = subprocess.Popen(["python", "ftp_stuff.py"], cwd="backend")
        return redirect("/live", 302)


@app.route("/send")
def send():
    if session["ready_to_send"]:
        return "Prepping live send output. "
    else:
        return "Not ready."


@app.route("/live")
def live():
    return '<html>' \
           '<style>' \
           '#status {' \
           '    animation: flashAnimation 2s;' \
           '}' \
           '@keyframes flashAnimation {' \
           '    0% { background-color: inherit; }' \
           '    50% { background-color: green; }' \
           '    100% { background-color: inherit; }' \
           '}' \
           '</style>' \
           '' \
           '' \
           '' \
           '' \
           'The current status is <div ' \
           'style="display:inline;" ' \
           'id="status">loading</div>.<script>' \
           'function update() {' \
           'fetch("/status").then(function(response) { ' \
           '    return response.text();' \
           '}).then(function(data) {  ' \
           '    console.log(data);' \
           '    document.getElementById("status").innerHTML = data;' \
           '    setTimeout(()=>{requestAnimationFrame(update)}, 5000);' \
           '}).catch(function(err) {  ' \
           '    console.log("Fetch Error :-S", err);' \
           '});' \
           '' \
           '' \
           '}' \
           'update();' \
           '</script><br \\><a href="/build">Build!</a>  <a ' \
           'href="/push">Push!</a></html>'


if __name__ == '__main__':
    process = None
    app.run(host="0.0.0.0", port=8000, debug=True)
