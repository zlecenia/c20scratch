from flask import Flask, request, jsonify, send_from_directory
import subprocess, os, re, json

app = Flask(__name__)

SCRIPTS_FOLDER = "scripts"
PROJECTS_FOLDER = "projects"
DEMOS_FOLDER = os.path.join(PROJECTS_FOLDER, "demo")
UPLOADS_FOLDER = "uploads"

# Ensure projects folder exists
os.makedirs(PROJECTS_FOLDER, exist_ok=True)
os.makedirs(UPLOADS_FOLDER, exist_ok=True)
os.makedirs(DEMOS_FOLDER, exist_ok=True)

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

ALLOWED_UPLOAD_EXT = {"xml", "svg"}

def _ext_ok(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_UPLOAD_EXT

@app.route("/uploads", methods=["GET"])
def list_uploads():
    items = os.listdir(UPLOADS_FOLDER)
    all_files = [f for f in items if os.path.isfile(os.path.join(UPLOADS_FOLDER, f))]
    svg = [os.path.splitext(f)[0] for f in all_files if f.lower().endswith(".svg")]
    xml = [os.path.splitext(f)[0] for f in all_files if f.lower().endswith(".xml")]
    return jsonify({"all": sorted(all_files), "svg": sorted(svg), "xml": sorted(xml)})

@app.route("/uploads/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "file field is required"}), 400
    f = request.files['file']
    if f.filename == '':
        return jsonify({"error": "empty filename"}), 400
    if not _ext_ok(f.filename):
        return jsonify({"error": "unsupported extension"}), 400
    # sanitize name
    name_no_ext, ext = os.path.splitext(f.filename)
    safe = _safe_name(name_no_ext) + ext.lower()
    path = os.path.join(UPLOADS_FOLDER, safe)
    f.save(path)
    return jsonify({"ok": True, "name": os.path.splitext(safe)[0], "filename": safe, "url": f"/uploads/{safe}"})

@app.route("/uploads/<path:filename>", methods=["GET"])
def serve_upload(filename):
    return send_from_directory(UPLOADS_FOLDER, filename)

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory("ide", path)

# ---- Projekty (zapis/odczyt) ----
def _safe_name(name: str) -> str:
    # allow only alnum, dash and underscore
    return re.sub(r"[^A-Za-z0-9_-]", "_", name or "project")

@app.route("/projects", methods=["GET"])
def list_projects():
    xmls = []
    htmls = []
    for fname in os.listdir(PROJECTS_FOLDER):
        if fname.endswith(".xml"):
            xmls.append(os.path.splitext(fname)[0])
        elif fname.endswith(".html"):
            htmls.append(os.path.splitext(fname)[0])
    return jsonify({"xml": sorted(xmls), "html": sorted(htmls)})

@app.route("/projects/demos", methods=["GET"])
def list_demo_projects():
    demos = []
    try:
        for fname in os.listdir(DEMOS_FOLDER):
            if fname.endswith(".xml"):
                demos.append(os.path.splitext(fname)[0])
    except FileNotFoundError:
        pass
    return jsonify({"xml": sorted(demos)})

@app.route("/projects/save", methods=["POST"])
def save_project():
    data = request.get_json(force=True, silent=True) or {}
    name = _safe_name(data.get("name", "project"))
    xml = data.get("xml", "")
    if not xml:
        return jsonify({"error": "xml is required"}), 400
    path = os.path.join(PROJECTS_FOLDER, f"{name}.xml")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(xml)
        return jsonify({"ok": True, "name": name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/projects/<name>", methods=["GET"])
def get_project(name):
    name = _safe_name(name)
    path = os.path.join(PROJECTS_FOLDER, f"{name}.xml")
    if not os.path.exists(path):
        return jsonify({"error": "not found"}), 404
    with open(path, "r", encoding="utf-8") as f:
        xml = f.read()
    return jsonify({"name": name, "xml": xml})

@app.route("/projects/demo/<name>", methods=["GET"])
def get_demo_project(name):
    name = _safe_name(name)
    path = os.path.join(DEMOS_FOLDER, f"{name}.xml")
    if not os.path.exists(path):
        return jsonify({"error": "not found"}), 404
    with open(path, "r", encoding="utf-8") as f:
        xml = f.read()
    return jsonify({"name": name, "xml": xml, "demo": True})

@app.route("/projects/save_html", methods=["POST"])
def save_project_html():
    data = request.get_json(force=True, silent=True) or {}
    name = _safe_name(data.get("name", "project"))
    html = data.get("html", "")
    if not html:
        return jsonify({"error": "html is required"}), 400
    path = os.path.join(PROJECTS_FOLDER, f"{name}.html")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        return jsonify({"ok": True, "name": name, "url": f"/projects/html/{name}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/projects/html/<name>", methods=["GET"])
def serve_project_html(name):
    name = _safe_name(name)
    filename = f"{name}.html"
    path = os.path.join(PROJECTS_FOLDER, filename)
    if not os.path.exists(path):
        return jsonify({"error": "not found"}), 404
    return send_from_directory(PROJECTS_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5005)
