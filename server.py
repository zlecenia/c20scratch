from flask import Flask, request, jsonify, send_from_directory
import subprocess, os, re, json
from flask_cors import CORS

app = Flask(__name__)
# In production, restrict origins/paths as needed.
CORS(app, resources={r"/*": {"origins": "*"}})

SCRIPTS_FOLDER = "scripts"
PROJECTS_FOLDER = "projects"
DEMOS_FOLDER = os.path.join(PROJECTS_FOLDER, "demo")
UPLOADS_FOLDER = "uploads"
MODULES_FOLDER = "modules"
PACKAGES_FOLDER = os.path.join(MODULES_FOLDER, "packages")

# Ensure folders exist
os.makedirs(PROJECTS_FOLDER, exist_ok=True)
os.makedirs(UPLOADS_FOLDER, exist_ok=True)
os.makedirs(DEMOS_FOLDER, exist_ok=True)
os.makedirs(MODULES_FOLDER, exist_ok=True)
os.makedirs(PACKAGES_FOLDER, exist_ok=True)

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

# ---- Example API endpoints ----
@app.route("/api/hello", methods=["GET"])
def api_hello():
    return jsonify({"msg": "Hello from backend", "ok": True})

@app.route("/api/users", methods=["GET"])
def api_users():
    limit = request.args.get('limit', 10, type=int)
    page = request.args.get('page', 1, type=int)
    users = [{"id": i, "name": f"User {i}", "email": f"user{i}@example.com"} 
             for i in range((page-1)*limit + 1, page*limit + 1)]
    return jsonify({"users": users, "page": page, "limit": limit, "total": 100})

@app.route("/api/users/<int:user_id>", methods=["GET"])
def api_get_user(user_id):
    return jsonify({"id": user_id, "name": f"User {user_id}", "email": f"user{user_id}@example.com"})

@app.route("/api/users", methods=["POST"])
def api_create_user():
    data = request.get_json() or {}
    name = data.get('name', 'Unknown')
    email = data.get('email', 'unknown@example.com')
    new_id = 101  # Simulated new ID
    return jsonify({"id": new_id, "name": name, "email": email, "created": True}), 201

@app.route("/api/users/<int:user_id>", methods=["PUT"])
def api_update_user(user_id):
    data = request.get_json() or {}
    name = data.get('name', f'User {user_id}')
    email = data.get('email', f'user{user_id}@example.com')
    return jsonify({"id": user_id, "name": name, "email": email, "updated": True})

# ---- Minimal OpenAPI (Swagger 2.0) spec for quick Blockly API generation ----
@app.route("/openapi.json", methods=["GET"])
def openapi_spec():
    # Derive current scheme and host dynamically
    url_root = request.url_root.rstrip("/")
    scheme = url_root.split("://")[0]
    host = request.host
    spec = {
        "swagger": "2.0",
        "info": {"title": "c20scratch API", "version": "1.0.0"},
        "schemes": [scheme],
        "host": host,
        "basePath": "/",
        "paths": {
            "/api/hello": {
                "get": {
                    "summary": "Hello",
                    "responses": {"200": {"description": "OK"}}
                }
            },
            "/api/users": {
                "get": {
                    "summary": "Get Users",
                    "parameters": [
                        {"name": "limit", "in": "query", "type": "integer", "default": 10, "description": "Number of users per page"},
                        {"name": "page", "in": "query", "type": "integer", "default": 1, "description": "Page number"}
                    ],
                    "responses": {"200": {"description": "List of users"}}
                },
                "post": {
                    "summary": "Create User",
                    "parameters": [
                        {"name": "body", "in": "body", "required": True, "schema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "User name"},
                                "email": {"type": "string", "description": "User email"}
                            }
                        }}
                    ],
                    "responses": {"201": {"description": "User created"}}
                }
            },
            "/api/users/{user_id}": {
                "get": {
                    "summary": "Get User by ID",
                    "parameters": [
                        {"name": "user_id", "in": "path", "type": "integer", "required": True, "description": "User ID"}
                    ],
                    "responses": {"200": {"description": "User details"}}
                },
                "put": {
                    "summary": "Update User",
                    "parameters": [
                        {"name": "user_id", "in": "path", "type": "integer", "required": True, "description": "User ID"},
                        {"name": "body", "in": "body", "required": True, "schema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "User name"},
                                "email": {"type": "string", "description": "User email"}
                            }
                        }}
                    ],
                    "responses": {"200": {"description": "User updated"}}
                }
            }
        }
    }
    return jsonify(spec)

# ---- Module/Package Management System ----
@app.route("/modules/list", methods=["GET"])
def list_modules():
    """List all available modules/packages"""
    modules = []
    try:
        # Core modules (built-in)
        core_modules = [
            {"id": "ui", "name": "UI Components", "type": "core", "description": "Basic UI building blocks"},
            {"id": "values", "name": "Values & Data", "type": "core", "description": "Text, numbers, JSON construction"},
            {"id": "api_local", "name": "Local API", "type": "core", "description": "Built-in API endpoints"}
        ]
        
        # Public API modules (configurable)
        public_apis = [
            {"id": "linkedin", "name": "LinkedIn API", "type": "public_api", "description": "LinkedIn profile and company data"},
            {"id": "openai", "name": "OpenAI API", "type": "public_api", "description": "AI text generation and analysis"},
            {"id": "mcp", "name": "MCP Protocol", "type": "public_api", "description": "Model Context Protocol integration"}
        ]
        
        # Custom packages (user-uploaded)
        custom_packages = []
        if os.path.exists(PACKAGES_FOLDER):
            for filename in os.listdir(PACKAGES_FOLDER):
                if filename.endswith('.xml'):
                    package_id = filename[:-4]
                    custom_packages.append({
                        "id": package_id,
                        "name": package_id.replace('_', ' ').title(),
                        "type": "custom",
                        "description": "Custom uploaded package"
                    })
        
        modules = core_modules + public_apis + custom_packages
        return jsonify({"modules": modules})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/modules/upload", methods=["POST"])
def upload_module():
    """Upload a custom module package"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not file.filename.endswith('.xml'):
            return jsonify({"error": "Only XML files are allowed"}), 400
        
        # Save to packages folder
        filename = os.path.join(PACKAGES_FOLDER, file.filename)
        file.save(filename)
        
        return jsonify({"message": "Module uploaded successfully", "filename": file.filename})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/modules/<module_id>/spec", methods=["GET"])
def get_module_spec(module_id):
    """Get the specification/blocks for a specific module"""
    try:
        # Handle built-in modules
        if module_id == "linkedin":
            return jsonify(get_linkedin_api_spec())
        elif module_id == "openai":
            return jsonify(get_openai_api_spec())
        elif module_id == "mcp":
            return jsonify(get_mcp_api_spec())
        elif module_id == "ui":
            return jsonify(get_ui_blocks_spec())
        elif module_id == "values":
            return jsonify(get_values_blocks_spec())
        else:
            # Check for custom package
            package_path = os.path.join(PACKAGES_FOLDER, f"{module_id}.xml")
            if os.path.exists(package_path):
                with open(package_path, 'r') as f:
                    return jsonify({"xml_content": f.read(), "type": "custom"})
            else:
                return jsonify({"error": "Module not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_linkedin_api_spec():
    """LinkedIn API specification"""
    return {
        "name": "LinkedIn API",
        "base_url": "https://api.linkedin.com/v2",
        "auth_required": True,
        "blocks": {
            "linkedin_profile": {
                "summary": "Get LinkedIn Profile",
                "method": "GET",
                "path": "/people/(id:{person-id})",
                "params": [
                    {"name": "person_id", "type": "string", "required": True}
                ]
            },
            "linkedin_company": {
                "summary": "Get Company Info",
                "method": "GET", 
                "path": "/companies/{id}",
                "params": [
                    {"name": "company_id", "type": "string", "required": True}
                ]
            }
        }
    }

def get_openai_api_spec():
    """OpenAI API specification"""
    return {
        "name": "OpenAI API",
        "base_url": "https://api.openai.com/v1",
        "auth_required": True,
        "blocks": {
            "openai_chat": {
                "summary": "Chat Completion",
                "method": "POST",
                "path": "/chat/completions",
                "params": [
                    {"name": "model", "type": "string", "default": "gpt-3.5-turbo"},
                    {"name": "messages", "type": "array", "required": True},
                    {"name": "max_tokens", "type": "number", "default": 100}
                ]
            },
            "openai_embeddings": {
                "summary": "Get Embeddings",
                "method": "POST",
                "path": "/embeddings",
                "params": [
                    {"name": "model", "type": "string", "default": "text-embedding-ada-002"},
                    {"name": "input", "type": "string", "required": True}
                ]
            }
        }
    }

def get_mcp_api_spec():
    """MCP Protocol specification"""
    return {
        "name": "MCP Protocol",
        "base_url": "http://localhost:3001",
        "auth_required": False,
        "blocks": {
            "mcp_list_tools": {
                "summary": "List Available Tools",
                "method": "GET",
                "path": "/tools"
            },
            "mcp_call_tool": {
                "summary": "Call MCP Tool",
                "method": "POST",
                "path": "/tools/{tool_name}/call",
                "params": [
                    {"name": "tool_name", "type": "string", "required": True},
                    {"name": "arguments", "type": "object", "required": True}
                ]
            }
        }
    }

def get_ui_blocks_spec():
    """UI blocks specification"""
    return {
        "name": "UI Components",
        "blocks": ["add_view", "ui_heading", "ui_paragraph", "ui_button", "ui_container", "ui_card", "ui_alert", "ui_divider"]
    }

def get_values_blocks_spec():
    """Values blocks specification"""
    return {
        "name": "Values & Data",
        "blocks": ["text", "math_number", "json_object", "json_property", "json_array", "text_multiline"]
    }

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
    # Allow overriding port via environment variable PORT
    port = int(os.getenv("PORT", "5005"))
    app.run(debug=True, host="0.0.0.0", port=port)
