from flask import Flask, request, jsonify, send_from_directory
import subprocess, os, re, json

app = Flask(__name__)

SCRIPTS_FOLDER = "scripts"

# ---- Parsowanie Python ----
def parse_python(file_path):
    with open(file_path) as f:
        code = f.read()
    matches = re.findall(r'def\s+(\w+)\s*\((.*?)\):', code)
    functions = []
    for name, args in matches:
        params = [p.strip().split('=')[0] for p in args.split(',') if p.strip()]
        functions.append({"name": name, "params": params})
    return functions

# ---- Parsowanie Bash ----
def parse_bash(file_path):
    params = []
    with open(file_path) as f:
        for line in f:
            if line.startswith("# param:"):
                _, spec = line.split(":",1)
                params.append(spec.strip().split()[0])
    return [{"name": os.path.basename(file_path), "params": params}]

# ---- Skanowanie katalogu ----
def scan_scripts():
    scripts = []
    for fname in os.listdir(SCRIPTS_FOLDER):
        path = os.path.join(SCRIPTS_FOLDER, fname)
        if fname.endswith(".py"):
            for fn in parse_python(path):
                scripts.append({"script": fname, "func": fn["name"], "params": fn["params"]})
        elif fname.endswith(".sh"):
            for fn in parse_bash(path):
                scripts.append({"script": fname, "func": fn["name"], "params": fn["params"]})
    return scripts

@app.route("/scripts.json")
def scripts_json():
    return jsonify(scan_scripts())

# ---- Uruchamianie skryptu ----
@app.route("/run-script", methods=["POST"])
def run_script():
    data = request.json
    script = data["script"]
    func = data.get("func")
    args = data.get("args", [])

    script_path = os.path.join(SCRIPTS_FOLDER, script)
    if not os.path.exists(script_path):
        return jsonify({"error": "Script not found"}), 404

    try:
        if script.endswith(".py"):
            cmd = ["python3", script_path] + [str(a) for a in args]
        else:
            cmd = ["bash", script_path] + [str(a) for a in args]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return jsonify({"stdout": result.stdout, "stderr": result.stderr, "code": result.returncode})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---- Serwowanie frontendu ----
@app.route("/")
def index():
    return send_from_directory("ide", "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory("ide", path)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5005)
