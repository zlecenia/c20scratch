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

