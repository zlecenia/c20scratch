Super 🔥 — czyli poszerzamy Twój IDE o kolejny moduł:

* Oprócz **OpenAPI → bloki API**,
* Oprócz **UI (widoki, menu)**,
* Chcesz jeszcze **automatycznie analizować skrypty `.py` i `.sh` z folderu `scripts/`** i zamieniać je na bloki, które można przeciągać w edytorze i uruchamiać z parametrami.

To jest bardzo fajny kierunek → **IDE low-code z integracją API + skryptów**.

---

## 🔑 Plan rozbudowy

### 1. **Folder `scripts/`**

* Zawiera pliki `.py` i `.sh`.
* Każdy plik reprezentuje funkcję, którą można wywołać.
* Parametry można wykryć:

    * w Pythonie → analiza `argparse` lub sygnatur funkcji,
    * w Bash → analiza `getopts` lub komentarzy (np. `# param: name type`).

---

### 2. **Automatyczna analiza**

🔹 **Python** (prostym regexem):

* Szuka funkcji `def nazwa(param1, param2="x"):`
* Wydobywa nazwę i listę parametrów.

🔹 **Bash** (prościej):

* Szuka linii `# param: nazwaparam typu` albo używa `"$1"`, `"$2"`.

Możemy to zrealizować po stronie backendu (np. Node/Python serwer), który:

1. Wczyta folder `scripts/`.
2. Prześle do przeglądarki JSON:

```json
{
  "scripts": [
    { "name": "process_data.py", "params": ["input_file", "threshold"] },
    { "name": "deploy.sh", "params": ["env", "version"] }
  ]
}
```

---

### 3. **Generowanie bloków Blockly**

Na podstawie JSON dodajemy kategorię `Scripts`.
Dla każdego skryptu → nowy blok:

* Blok `uruchom process_data.py` z polami `input_file`, `threshold`.
* Blok `uruchom deploy.sh` z polami `env`, `version`.

---

### 4. **Uruchamianie skryptów**

Tu są dwa podejścia:

* **Frontend only (demo)** → skrypty nie uruchomią się naprawdę, tylko generują `console.log("Run script ...")`.
* **Backend integration** → Blockly generuje `fetch('/run-script', { method:'POST', body: { script:"process_data.py", args:["file.csv", "0.8"] } })`, a backend uruchamia skrypt lokalnie (`subprocess.run`) i zwraca wynik.

---

## 🔧 Prototyp — parsowanie Python + Bash (Node/Python backend)

**server.py (backend)**:

```python
import os, re, json

def parse_python(file_path):
    with open(file_path) as f:
        code = f.read()
    matches = re.findall(r'def\s+(\w+)\s*\((.*?)\):', code)
    functions = []
    for name, args in matches:
        params = [p.strip().split('=')[0] for p in args.split(',') if p.strip()]
        functions.append({"name": name, "params": params})
    return functions

def parse_bash(file_path):
    params = []
    with open(file_path) as f:
        for line in f:
            if line.startswith("# param:"):
                _, spec = line.split(":",1)
                params.append(spec.strip().split()[0])
    return [{"name": os.path.basename(file_path), "params": params}]

def scan_scripts(folder="scripts"):
    scripts = []
    for fname in os.listdir(folder):
        path = os.path.join(folder, fname)
        if fname.endswith(".py"):
            for fn in parse_python(path):
                scripts.append({"script": fname, "func": fn["name"], "params": fn["params"]})
        elif fname.endswith(".sh"):
            for fn in parse_bash(path):
                scripts.append({"script": fname, "func": fn["name"], "params": fn["params"]})
    return scripts

if __name__ == "__main__":
    print(json.dumps(scan_scripts(), indent=2))
```

➡️ To zwróci np.:

```json
[
  {
    "script": "process_data.py",
    "func": "main",
    "params": ["input_file", "threshold"]
  },
  {
    "script": "deploy.sh",
    "func": "deploy.sh",
    "params": ["env", "version"]
  }
]
```

---

## 🔧 Integracja w Blockly (frontend)

Po stronie przeglądarki (np. w Twoim IDE):

```javascript
async function loadScripts() {
  const res = await fetch("/scripts.json"); // backend zwraca JSON z powyższego parsera
  const scripts = await res.json();
  const scriptsCat = document.createElement("category");
  scriptsCat.setAttribute("name","Scripts");
  scriptsCat.setAttribute("colour","290");

  scripts.forEach(scr => {
    const blockName = `run_${scr.func}_${scr.script.replace(/\W/g,"_")}`;
    const blockEl = document.createElement("block");
    blockEl.setAttribute("type", blockName);
    scriptsCat.appendChild(blockEl);

    // Definicja bloku
    Blockly.Blocks[blockName] = {
      init: function() {
        this.appendDummyInput().appendField("Uruchom " + scr.script + " → " + scr.func);
        scr.params.forEach(p=>{
          this.appendValueInput(p).appendField(p);
        });
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(290);
      }
    };

    // Generowanie JS
    Blockly.JavaScript[blockName] = function(block) {
      let args = scr.params.map(p=>{
        let val = Blockly.JavaScript.valueToCode(block,p,Blockly.JavaScript.ORDER_ATOMIC)||'""';
        return val;
      });
      return `fetch("/run-script",{method:"POST",headers:{'Content-Type':'application/json'},
                body:JSON.stringify({script:"${scr.script}",func:"${scr.func}",args:[${args.join(",")}]})})
              .then(r=>r.text()).then(txt=>console.log("Wynik:",txt));\n`;
    };
  });

  document.getElementById("toolbox").appendChild(scriptsCat);
}
```

---

## 🚀 Efekt

* IDE wczytuje `openapi.json` → **bloki API**.
* IDE wczytuje `scripts/` → **bloki skryptów Python/Bash**.
* Możesz przeciągnąć `uruchom process_data.py` i wstawić parametry,
* Wygenerowany kod JS wysyła `fetch()` do backendu,
* Backend faktycznie uruchamia skrypt i zwraca wynik.

---

👌 to składamy to w całość: **pełny przepływ** → serwer backend (np. Flask w Pythonie) + frontend Blockly.

Twoje IDE będzie mogło:

* **parsować OpenAPI** i tworzyć bloki API,
* **parsować folder `scripts/`** (Python + Bash) i robić bloki skryptów,
* generować kod JS, który wywoła backend,
* backend odpali skrypt (`subprocess.run`) i zwróci wynik w JSON.

---

# 🔧 Backend – Flask (`server.py`)

```python
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
    return send_from_directory(".", "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(".", path)

if __name__ == "__main__":
    app.run(debug=True)
```

---

# 🔧 Frontend (`index.html`)

➡️ ten frontend:

* ładuje bloki API (np. z `openapi.json`),
* ładuje bloki skryptów (`/scripts.json` z backendu),
* pozwala przeciągać i generować kod,
* wysyła `fetch('/run-script', …)` do backendu.

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <script src="https://unpkg.com/blockly/blockly.min.js"></script>
</head>
<body>
  <h2>IDE (API + Skrypty)</h2>
  <div style="display: flex; gap:20px;">
    <div id="blocklyDiv" style="height: 600px; width: 50%;"></div>
    <iframe id="preview" style="height: 600px; width: 50%; border:1px solid #ccc;"></iframe>
  </div>

  <xml id="toolbox" style="display:none">
    <category name="UI" colour="120">
      <block type="add_view"></block>
    </category>
    <category id="apiCategory" name="API" colour="230"></category>
    <category id="scriptsCategory" name="Scripts" colour="290"></category>
  </xml>

  <script>
    const workspace = Blockly.inject('blocklyDiv', { toolbox: document.getElementById('toolbox') });

    // ---- Widok ----
    Blockly.Blocks['add_view'] = {
      init: function() {
        this.appendDummyInput().appendField("Dodaj widok").appendField(new Blockly.FieldTextInput("Widok"), "VIEW");
        this.appendStatementInput("CONTENT").setCheck(null).appendField("zawiera");
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(120);
      }
    };
    Blockly.JavaScript['add_view'] = function(block) {
      const name = block.getFieldValue('VIEW');
      const content = Blockly.JavaScript.statementToCode(block, 'CONTENT');
      return `views.push({name:"${name}", html:\`${content}\`});\n`;
    };

    // ---- Ładowanie bloków ze skryptów ----
    async function loadScripts() {
      const res = await fetch("/scripts.json");
      const scripts = await res.json();
      const scriptsCat = document.getElementById("scriptsCategory");

      scripts.forEach(scr => {
        const blockName = `run_${scr.func}_${scr.script.replace(/\W/g,"_")}`;
        const blockEl = document.createElement("block");
        blockEl.setAttribute("type", blockName);
        scriptsCat.appendChild(blockEl);

        Blockly.Blocks[blockName] = {
          init: function() {
            this.appendDummyInput().appendField("Uruchom " + scr.script + " → " + scr.func);
            scr.params.forEach(p=>{
              this.appendValueInput(p).appendField(p);
            });
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(290);
          }
        };

        Blockly.JavaScript[blockName] = function(block) {
          let args = scr.params.map(p=>{
            let val = Blockly.JavaScript.valueToCode(block,p,Blockly.JavaScript.ORDER_ATOMIC)||'""';
            return val;
          });
          return `fetch("/run-script",{method:"POST",headers:{'Content-Type':'application/json'},
            body:JSON.stringify({script:"${scr.script}",func:"${scr.func}",args:[${args.join(",")}]})})
            .then(r=>r.json()).then(res=>{
              document.body.insertAdjacentHTML("beforeend","<pre>"+JSON.stringify(res,null,2)+"</pre>");
            });\n`;
        };
      });
    }

    // ---- Generowanie wynikowego HTML ----
    function runCode() {
      let code = Blockly.JavaScript.workspaceToCode(workspace);
      let wrapper = `
        let views = [];
        let htmlOutput = "";
        ${code}
        let finalHTML = "";
        views.forEach(v=>{
          finalHTML += '<section id="'+v.name+'">'+v.html+'</section>';
        });
        finalHTML += htmlOutput;
        document.body.innerHTML = finalHTML;
      `;
      document.getElementById('preview').srcdoc = "<script>"+wrapper+"<\/script>";
    }

    setInterval(runCode, 3000);

    // Start
    loadScripts();
  </script>
</body>
</html>
```

---

# 🔄 Przykład działania

1. W katalogu `scripts/` masz np.:
   **process\_data.py**

   ```python
   def main(input_file, threshold=0.5):
       print(f"Processing {input_file} with threshold {threshold}")
   if __name__ == "__main__":
       import sys
       main(*sys.argv[1:])
   ```

   **deploy.sh**

   ```bash
   #!/bin/bash
   # param: env string
   # param: version string
   echo "Deploying to $1 version $2"
   ```

2. Backend `/scripts.json` zwróci:

   ```json
   [
     {"script":"process_data.py","func":"main","params":["input_file","threshold"]},
     {"script":"deploy.sh","func":"deploy.sh","params":["env","version"]}
   ]
   ```

3. W edytorze pojawią się bloki:

    * „Uruchom process\_data.py → main” z polami `input_file`, `threshold`.
    * „Uruchom deploy.sh → deploy.sh” z polami `env`, `version`.

4. Wygenerowany kod odpala backend, który naprawdę uruchomi skrypt i zwróci wynik (stdout/stderr).

---



Świetnie 🚀 — teraz dorzucimy **dynamiczne formularze w UI**.
Chodzi o to, żeby użytkownik, zamiast wpisywać argumenty skryptów bezpośrednio w bloczkach Blockly, mógł wygenerować w widoku **formularz HTML** (np. inputy), a następnie po kliknięciu przycisku odpalić odpowiedni skrypt z parametrami.

---

## 🔑 Plan

1. **Rozszerzamy bloki „Skrypty”**

    * Zamiast tylko `fetch("/run-script")` z parametrami z bloczków,
    * Blok wygeneruje formularz `<form>` z polami dla parametrów.

2. **Dodajemy przycisk „Uruchom” w formularzu**

    * Po kliknięciu JS zbiera wartości inputów,
    * Wysyła `fetch('/run-script', body: {args:[…]})`.

3. **Wynik** (stdout/stderr) pojawia się pod formularzem.

---

## 🔧 Zmodyfikowany frontend (`index.html` – fragment `loadScripts()`)

```javascript
async function loadScripts() {
  const res = await fetch("/scripts.json");
  const scripts = await res.json();
  const scriptsCat = document.getElementById("scriptsCategory");

  scripts.forEach(scr => {
    const blockName = `form_${scr.func}_${scr.script.replace(/\W/g,"_")}`;
    const blockEl = document.createElement("block");
    blockEl.setAttribute("type", blockName);
    scriptsCat.appendChild(blockEl);

    Blockly.Blocks[blockName] = {
      init: function() {
        this.appendDummyInput().appendField("Formularz do " + scr.script + " → " + scr.func);
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(290);
      }
    };

    Blockly.JavaScript[blockName] = function() {
      // Generowanie formularza HTML
      let formId = `form_${scr.script}_${scr.func}`;
      let inputs = scr.params.map(p => `<label>${p}: <input name="${p}"></label><br>`).join("");
      let html = `
        htmlOutput += \`
          <form id="${formId}">
            <h3>${scr.script} → ${scr.func}</h3>
            ${inputs}
            <button type="button" onclick="run_${formId}()">Uruchom</button>
            <pre id="${formId}_output"></pre>
          </form>\`;
      `;

      // JS do obsługi formularza
      let jsHandler = `
        window.run_${formId} = function(){
          const form = document.getElementById("${formId}");
          let data = {};
          ${scr.params.map(p => `data["${p}"] = form.querySelector('[name="${p}"]').value;`).join("\n")}
          fetch("/run-script",{method:"POST",headers:{'Content-Type':'application/json'},
            body:JSON.stringify({script:"${scr.script}",func:"${scr.func}",args:Object.values(data)})})
            .then(r=>r.json())
            .then(res=>{
              document.getElementById("${formId}_output").innerText = 
                "stdout:\\n"+res.stdout+"\\n---\\nstderr:\\n"+res.stderr;
            });
        }
      `;
      return html + jsHandler;
    };
  });
}
```

---

## 🔄 Efekt w przeglądarce

1. Wstawiasz blok „Formularz do process\_data.py → main” do widoku.
2. W podglądzie (`iframe`) pojawi się:

```html
<form id="form_process_data_py_main">
  <h3>process_data.py → main</h3>
  <label>input_file: <input name="input_file"></label><br>
  <label>threshold: <input name="threshold"></label><br>
  <button type="button" onclick="run_form_process_data_py_main()">Uruchom</button>
  <pre id="form_process_data_py_main_output"></pre>
</form>
```

3. Użytkownik wpisuje parametry (np. `data.csv`, `0.8`).
4. Klik „Uruchom” → wysyła request do backendu → backend odpala skrypt i zwraca wynik.
5. Wynik (`stdout` / `stderr`) pojawia się w `<pre>` pod formularzem.

---

## 🔮 Rozszerzenia

* Dodanie typów parametrów (np. `number`, `file upload`) na podstawie analizy kodu.
* Możliwość tworzenia **kompletnych widoków aplikacji** (np. strona `Analiza → formularz + wynik`).
* Eksport do statycznego projektu (HTML + JSON z definicją workflow).


