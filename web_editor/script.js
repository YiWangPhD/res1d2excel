// -------- INITIAL DATA --------
const data = {
    catchment: [],
    node: [],
    link: [],
    orifice: [],
    pump: [],
    regulation: [],
    weir: [],
    valve: [],
    bridge: [],
    direct_discharge: [],
    gate: [],
    combined: [],
    output_files: {
        output_folder: "",
        resample_interval: "",
        skip_time: "",
        trunc_time: "",
        to_html: true,
        export_by_element: false,
        export_by_result_file: false,
        export_statistics: false
    },

    res1d_files: []
};

const RESULT_TYPES = ["network", "runoff"];
const RESULT_FILE_EXTENSIONS = [".res1d", ".res", ".resx", ".whr"];

const defaultSchemas = {
    catchment: ["alias", "quantity", "muid"],
    node: ["alias", "quantity", "muid"],
    link: ["alias", "quantity", "muid", "chainage"],
    orifice: ["alias", "quantity", "muid"],
    pump: ["alias", "quantity", "muid"],
    regulation: ["alias", "quantity", "muid", "chainage"],
    weir: ["alias", "quantity", "muid"],
    valve: ["alias", "quantity", "muid"],
    bridge: ["alias", "quantity", "muid"],
    direct_discharge: ["alias", "quantity", "muid"],
    gate: ["alias", "quantity", "muid"],
    res1d_files: ["result_type", "short_name", "file_path"],
    combined: ["alias", "quantity", "terms"]
};

const combinedSources = [
    "catchment", "node", "link", "orifice", "pump", "regulation",
    "weir", "valve", "bridge", "direct_discharge", "gate"
];

let currentTab = "";
let selectedRowIndex = -1;

// -------- INIT --------
function init() {
    createTabs();
    updateJSONView();
}

function createTabs() {
    const tabs = document.getElementById("tabs");
    const contents = document.getElementById("tab-contents");

    ["Instructions", "JSON", ...Object.keys(data)].forEach(name => {

        const btn = document.createElement("button");
        btn.innerText = name;
        btn.className = "tab-button";
        btn.onclick = () => switchTab(name);
        tabs.appendChild(btn);

        const div = document.createElement("div");
        div.id = "tab-" + name;
        div.className = "tab-content";

        if (name === "Instructions") {
            div.innerHTML = instructionsHTML();
        } else if (name === "JSON") {
            div.innerHTML = `
                <textarea id="jsonInput"></textarea><br>
                <button onclick="loadJSON()">Load JSON</button>
            `;
        } else if (name === "output_files") {
            div.innerHTML = outputFilesHTML();
        } else if (name === "res1d_files") {
            div.innerHTML = res1dHTML();
        } else if (name === "combined") {
            div.innerHTML = combinedHTML();
        } else {
            div.innerHTML = genericTabHTML(name);
        }

        contents.appendChild(div);
    });

    switchTab("Instructions");
}

function section(title, content) {
    return `
    <div class="section">
        <div class="section-header" onclick="toggleSection(this)">
            ▶ ${title}
        </div>
        <div class="section-content">
            ${content}
        </div>
    </div>
    `;
}
function toggleSection(header) {
    const content = header.nextElementSibling;

    if (content.style.display === "none") {
        content.style.display = "block";
        header.innerText = header.innerText.replace("▶", "▼");
    } else {
        content.style.display = "none";
        header.innerText = header.innerText.replace("▼", "▶");
    }
}

// -------- GENERIC TAB --------
function genericTabHTML(name) {
    return `
        <div id="form-${name}"></div>
        <button onclick="addRow('${name}')">Add Row</button>
        <button onclick="exportCSV('${name}')">Export CSV</button>
        <input type="file" onchange="importCSV(event,'${name}')">

        <table id="table-${name}"></table>
    `;
}

// -------- OUTPUT FILES TAB --------
function outputFilesHTML() {
    return `
        <label>Output Folder</label>
        <input id="of-folder" readonly><br>

        <label>Resample Interval</label>
        <input type="number" id="of-interval-value" min="0" step="1"
               style="width:80px;" oninput="updateOutputFiles()">

        <select id="of-interval-unit" onchange="updateOutputFiles()">
            <option value="day">day</option>
            <option value="hour">hour</option>
            <option value="minute">minute</option>
            <option value="second">second</option>
        </select><br>

        <label>Skip Time</label>
        <input type="number" id="of-skip-value" min="0" step="1"
               style="width:80px;" oninput="updateOutputFiles()">

        <select id="of-skip-unit" onchange="updateOutputFiles()">
            <option value="day">day</option>
            <option value="hour">hour</option>
            <option value="minute">minute</option>
            <option value="second">second</option>
        </select><br>

        <label>Truncation Time</label>
        <input type="number" id="of-trunc-value" min="0" step="1"
               style="width:80px;" oninput="updateOutputFiles()">

        <select id="of-trunc-unit" onchange="updateOutputFiles()">
            <option value="day">day</option>
            <option value="hour">hour</option>
            <option value="minute">minute</option>
            <option value="second">second</option>
        </select><br>

        <label>Export HTML Plots</label>
        <input type="checkbox" id="of-html" onchange="updateOutputFiles()"><br>

        <label>Export by Element</label>
        <input type="checkbox" id="of-e1" onchange="updateOutputFiles()"><br>

        <label>Export by Result File</label>
        <input type="checkbox" id="of-e2" onchange="updateOutputFiles()"><br>

        <label>Export Statistics</label>
        <input type="checkbox" id="of-e3" onchange="updateOutputFiles()">
    `;
}

function setDurationControls(prefix, duration, defaultUnit) {
    const valueEl = document.getElementById(`${prefix}-value`);
    const unitEl = document.getElementById(`${prefix}-unit`);

    if (!duration) {
        valueEl.value = 0;
        unitEl.value = defaultUnit;
        return;
    }

    const match = String(duration).trim().match(/^([0-9.]+)\s*([a-zA-Z]+)$/);
    if (!match) {
        valueEl.value = 0;
        unitEl.value = defaultUnit;
        return;
    }

    const unitMap = {
        d: "day",
        day: "day",
        days: "day",
        h: "hour",
        H: "hour",
        hr: "hour",
        hour: "hour",
        hours: "hour",
        min: "minute",
        minute: "minute",
        minutes: "minute",
        s: "second",
        sec: "second",
        second: "second",
        seconds: "second"
    };

    valueEl.value = parseFloat(match[1]);
    unitEl.value = unitMap[match[2]] || defaultUnit;
}

function renderOutputFiles() {
    const o = data.output_files;

    document.getElementById("of-folder").value = o.output_folder || "";

    // ✅ Parse string format like "10 minute"
    if (!o.resample_interval) {
        document.getElementById("of-interval-value").value = 0;
        document.getElementById("of-interval-unit").value = "minute";
    } else {
        const parts = o.resample_interval.split(" ");
        document.getElementById("of-interval-value").value = parseFloat(parts[0]);
        document.getElementById("of-interval-unit").value = parts[1];
    }

    setDurationControls("of-skip", o.skip_time, "hour");
    setDurationControls("of-trunc", o.trunc_time, "hour");

    document.getElementById("of-html").checked = o.to_html || false;
    document.getElementById("of-e1").checked = o.export_by_element || false;
    document.getElementById("of-e2").checked = o.export_by_result_file || false;
    document.getElementById("of-e3").checked = o.export_statistics || false;
}

function updateOutputFiles() {
    let value = parseFloat(document.getElementById("of-interval-value").value);
    let unit = document.getElementById("of-interval-unit").value;
    let skipValue = parseFloat(document.getElementById("of-skip-value").value);
    let skipUnit = document.getElementById("of-skip-unit").value;
    let truncValue = parseFloat(document.getElementById("of-trunc-value").value);
    let truncUnit = document.getElementById("of-trunc-unit").value;

    // ✅ validation
    if (isNaN(value) || value < 0) {
        alert("Resample interval must be >= 0");
        value = 0;
        document.getElementById("of-interval-value").value = 0;
    }

    if (isNaN(skipValue) || skipValue < 0) {
        alert("Skip time must be >= 0");
        skipValue = 0;
        document.getElementById("of-skip-value").value = 0;
    }

    if (isNaN(truncValue) || truncValue < 0) {
        alert("Truncation time must be >= 0");
        truncValue = 0;
        document.getElementById("of-trunc-value").value = 0;
    }

    // ✅ construct string OR null
    let resample = null;
    if (value > 0) {
        resample = `${value} ${unit}`;
    }

    let skipTime = null;
    if (skipValue > 0) {
        skipTime = `${skipValue} ${skipUnit}`;
    }

    let truncTime = null;
    if (truncValue > 0) {
        truncTime = `${truncValue} ${truncUnit}`;
    }

    data.output_files = {
        output_folder: document.getElementById("of-folder").value,
        resample_interval: resample,
        skip_time: skipTime,
        trunc_time: truncTime,
        to_html: document.getElementById("of-html").checked,

        export_by_element: document.getElementById("of-e1").checked,
        export_by_result_file: document.getElementById("of-e2").checked,
        export_statistics: document.getElementById("of-e3").checked
    };

    updateJSONView();
}

// -------- RESULT FILES TAB --------
function res1dHTML() {
    return `
        <div id="form-res1d_files"></div>

        <button onclick="addRow('res1d_files')">Add Row</button>
        <button onclick="loadRes1dFolder()">Load Result Folder</button>
        <button onclick="exportCSV('res1d_files')">Export CSV</button>
        <input type="file" onchange="importCSV(event,'res1d_files')">

        <table id="table-res1d_files"></table>
    `;
}
function loadRes1dFolder() {
    const input = document.createElement("input");
    input.type = "file";
    input.webkitdirectory = true;

    input.onchange = () => {
        const files = Array.from(input.files);

        // filter supported result files
        const res1dFiles = files.filter(f =>
            RESULT_FILE_EXTENSIONS.some(ext => f.name.toLowerCase().endsWith(ext))
        );

        // ✅ reset existing data
        data.res1d_files = [];

        res1dFiles.forEach(file => {
            data.res1d_files.push({
                result_type: "network",     // ✅ default
                short_name: "",             // ✅ blank
                file_path: file.name        // ✅ filename only
            });
        });

        selectedRowIndex = -1;
        renderTab("res1d_files");
        updateJSONView();

        alert(`${res1dFiles.length} result files loaded.`);
    };

    input.click();
}

function pickSingleRes1dFile() {
    // ✅ Ensure a row exists
    if (selectedRowIndex < 0) {
        addRow("res1d_files");
    }

    const input = document.createElement("input");
    input.type = "file";
    input.accept = RESULT_FILE_EXTENSIONS.join(",");

    input.onchange = () => {
        const file = input.files[0];
        if (!file) return;

        const fileName = file.name;

        // ✅ Update data model
        data.res1d_files[selectedRowIndex].file_path = fileName;

        // ✅ Update textbox
        const textbox = document.getElementById("res1d_files-file_path");
        if (textbox) textbox.value = fileName;

        // ✅ Refresh table + JSON
        renderTable("res1d_files", getColumns("res1d_files"));
        updateJSONView();
    };

    input.click();
}

// -------- COMBINED TAB -------
function combinedHTML() {
    return `
        <div id="combined-form"></div>

        <button onclick="addCombinedItem()">Add Combined Item</button>

        <table id="combined-table"></table>
    `;
}

function renderCombined() {
    renderCombinedTable();
}

function renderCombinedTable() {
    const table = document.getElementById("combined-table");

    table.innerHTML = `
        <tr>
            <th>Alias</th>
            <th>Quantity</th>
            <th>Terms</th>
            <th>Actions</th>
        </tr>
    `;

    data.combined.forEach((item, i) => {

        let termsStr = item.terms.map(t =>
            `${t.op} ${t.source}.${t.alias}`
        ).join(" ");

        let row = document.createElement("tr");

        row.onclick = () => renderCombinedForm(i);

        row.innerHTML = `
            <td>${item.alias}</td>
            <td>CalculatedDischarge</td>
            <td>${termsStr}</td>
            <td>
                <button onclick="event.stopPropagation();deleteCombined(${i})">Delete</button>
            </td>
        `;

        table.appendChild(row);
    });
}

function renderCombinedForm(index) {
    const container = document.getElementById("combined-form");
    const item = data.combined[index];

    container.innerHTML = `
        <h3>Edit Combined Item</h3>

        <label>Alias</label>
        <input id="comb-alias" value="${item.alias}" oninput="updateCombined(${index})"><br>

        <label>Quantity</label>
        <input value="CalculatedDischarge" readonly><br>

        <h4>Terms</h4>
        <div id="terms-container"></div>

        <button onclick="addTerm(${index})">Add Term</button>
    `;

    renderTerms(index);
}

function renderTerms(index) {
    const container = document.getElementById("terms-container");
    const terms = data.combined[index].terms;

    container.innerHTML = "";

    terms.forEach((t, i) => {

        const aliases = getAvailableAliases(t.source);

        container.innerHTML += `
            <div style="margin-bottom:5px">

                <!-- OPERATOR -->
                <select onchange="updateTerm(${index},${i},'op',this.value)">
                    <option value="+" ${t.op === "+" ? "selected" : ""}>+</option>
                    <option value="-" ${t.op === "-" ? "selected" : ""}>-</option>
                </select>

                <!-- SOURCE -->
                <select onchange="changeTermSource(${index},${i},this.value)">
                    ${combinedSources
                        .map(s => `<option value="${s}" ${t.source===s?"selected":""}>${s}</option>`)
                        .join("")}
                </select>

                <!-- ALIAS DROPDOWN -->
                <select onchange="updateTerm(${index},${i},'alias',this.value)">
                    <option value="">--select--</option>
                    ${aliases.map(a => 
                        `<option value="${a}" ${a===t.alias?"selected":""}>${a}</option>`
                    ).join("")}
                </select>

                <button onclick="deleteTerm(${index},${i})">X</button>
            </div>
        `;
    });
}

function addCombinedItem() {
    data.combined.push({
        alias: "",
        quantity: "CalculatedDischarge",
        terms: [
            { op: "+", source: "node", alias: "" }
        ]
    });

    renderCombined();
    updateJSONView();
}

function deleteCombined(i) {
    data.combined.splice(i, 1);
    renderCombined();
    updateJSONView();
}

function updateCombined(i) {
    data.combined[i].alias =
        document.getElementById("comb-alias").value;

    updateJSONView();
}

function addTerm(i) {
    data.combined[i].terms.push({
        op: "+",
        source: "node",
        alias: ""
    });

    renderTerms(i);
    updateJSONView();
}

function deleteTerm(i, j) {
    data.combined[i].terms.splice(j, 1);

    renderTerms(i);
    updateJSONView();
}

function updateTerm(i, j, field, value) {
    data.combined[i].terms[j][field] = value;

    updateJSONView();
}

function validateCombined() {
    data.combined.forEach(c => {

        if (!c.alias) {
            console.warn("Combined item missing alias");
        }

        if (c.terms.length < 1) {
            console.warn("Combined item needs at least 1 term");
        }
    });
}

function parseBoolean(value) {
    if (typeof value === "boolean") return value;
    if (value === null || value === undefined) return false;
    if (typeof value === "string") {
        return ["true", "yes", "y", "1"].includes(value.trim().toLowerCase());
    }
    return Boolean(value);
}

function getAvailableAliases(source) {
    if (!data[source]) return [];

    return data[source]
        .map(item => item.alias)
        .filter(a => a && a !== "");
}

function changeTermSource(i, j, newSource) {
    data.combined[i].terms[j].source = newSource;

    // ✅ reset alias when source changes
    data.combined[i].terms[j].alias = "";

    renderTerms(i);
    updateJSONView();
}

function getAvailableAliases(source) {
    if (!data[source]) return [];

    return data[source]
        .map(item => item.alias)
        .filter(a => a && a !== "")
        .sort();
}

// -------- TABLE LOGIC --------
function getColumns(name) {

    // ✅ ALWAYS prefer schema
    if (defaultSchemas[name]) {
        return defaultSchemas[name];
    }

    // fallback (just in case)
    if (!data[name] || data[name].length === 0) {
        return [];
    }

    let cols = new Set();
    data[name].forEach(r => {
        Object.keys(r).forEach(c => cols.add(c));
    });

    return Array.from(cols);
}

function renderTab(name) {
    const cols = getColumns(name);
    renderForm(name, cols);
    renderTable(name, cols);
}

function renderForm(name, cols) {
    const div = document.getElementById("form-" + name);
    if (!div) return;

    if (!cols || cols.length === 0) {
        div.innerHTML = "<i>No schema available</i>";
        return;
    }

    div.innerHTML = "";

    cols.forEach(c => {
        div.innerHTML += `
            <label>${c}</label>
            <input id="${name}-${c}" oninput="updateRow('${name}')"><br>
        `;
    });
}


function renderTable(name, cols) {
    const table = document.getElementById("table-" + name);
    if (!table) return;

    table.innerHTML = "<tr>" + cols.map(c => `<th>${c}</th>`).join("") + "<th>Actions</th></tr>";

    data[name].forEach((row, i) => {
        let tr = document.createElement("tr");
        if (i === selectedRowIndex) tr.classList.add("selected");

        tr.onclick = () => {
            selectedRowIndex = i;
            fillForm(name, row);
            renderTable(name, cols);
        };

        tr.innerHTML = cols.map(c => `<td>${row[c] || ""}</td>`).join("") +
            `<td>
                <button onclick="event.stopPropagation();copyRow('${name}',${i})">Copy</button>
                <button onclick="event.stopPropagation();deleteRow('${name}',${i})">Del</button>
             </td>`;

        table.appendChild(tr);
    });
}

// -------- ROW OPS --------
function addRow(name) {
    const cols = getColumns(name);

    let obj = {};

    cols.forEach(c => {
        if (name === "res1d_files" && c === "result_type") {
            obj[c] = "network";   // default
        } else if (c === "chainage") {
            obj[c] = 0;
        } else {
            obj[c] = "";
        }
    });

    data[name].push(obj);
    selectedRowIndex = data[name].length - 1;

    // ✅ FORCE redraw
    renderTab(name);
    fillForm(name, obj);

    updateJSONView();
}


function deleteRow(name, i) {
    data[name].splice(i, 1);
    selectedRowIndex = -1;
    renderTab(name);
    updateJSONView();
}

function copyRow(name, i) {
    const r = {...data[name][i]};
    data[name].splice(i+1,0,r);
    renderTab(name);
    updateJSONView();
}

// -------- FORM SYNC --------
function fillForm(name, row) {
    Object.keys(row).forEach(k => {
        const el = document.getElementById(`${name}-${k}`);
        if (!el) return;

        if (el.tagName === "SELECT") {
            el.value = row[k] || "network";
        } else {
            el.value = row[k] || "";
        }
    });
}

function updateRow(name) {
    if (selectedRowIndex < 0) return;

    let row = data[name][selectedRowIndex];
    Object.keys(row).forEach(k => {
        row[k] = document.getElementById(`${name}-${k}`).value;
    });

    renderTable(name, getColumns(name));
    updateJSONView();
}

// -------- CSV --------
function exportCSV(name) {
    let rows = data[name];
    if (!rows.length) return;

    let cols = getColumns(name);

    let csv = cols.join(",") + "\n";
    rows.forEach(r => {
        csv += cols.map(c => `"${r[c]||""}"`).join(",") + "\n";
    });

    let blob = new Blob([csv]);
    let a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = name + ".csv";
    a.click();
}

function importCSV(e, name) {
    let file = e.target.files[0];
    let reader = new FileReader();

    reader.onload = () => {
        let lines = reader.result.split("\n").filter(l=>l);
        let cols = lines[0].split(",");

        data[name] = lines.slice(1).map(line => {
            let vals = line.split(",");
            let obj = {};
            cols.forEach((c,i)=>obj[c]=vals[i].replace(/"/g,""));
            return obj;
        });

        renderTab(name);
        updateJSONView();
    };
    reader.readAsText(file);
}

// -------- JSON --------
function updateJSONView() {
    const el = document.getElementById("jsonInput");
    if (el) el.value = JSON.stringify(data, null, 2);
}

function loadJSON() {
    try {
        const input = document.getElementById("jsonInput").value;
        const parsed = JSON.parse(input);

        // ✅ Merge into existing data
        Object.keys(data).forEach(key => {
            if (parsed[key] !== undefined) {
                data[key] = parsed[key];
            }
        });

        ["bridge", "direct_discharge", "gate"].forEach(key => {
            if (!Array.isArray(data[key])) {
                data[key] = [];
            }
        });

        // ✅ Ensure combined exists
        if (!Array.isArray(data.combined)) {
            data.combined = [];
        }

        data.output_files.to_html = parseBoolean(data.output_files.to_html);

        // ✅ Normalize combined structure
        data.combined.forEach(item => {

            if (!item.alias) item.alias = "";
            item.quantity = "CalculatedDischarge";

            if (!Array.isArray(item.terms)) {
                item.terms = [];
            }

            item.terms.forEach(term => {
                if (!term.op) term.op = "+";
                if (!term.source) term.source = "node";
                if (!term.alias) term.alias = "";
            });
        });

        selectedRowIndex = -1;

        // ✅ Force full UI refresh (all tabs safe)
        Object.keys(data).forEach(key => {
            if (key === "combined") {
                renderCombined();
            } else if (key === "output_files") {
                renderOutputFiles();
            } else if (key !== "JSON" && key !== "Instructions") {
                renderTab(key);
            }
        });
        
        // ✅ Make sure visible tab is refreshed AGAIN (important)
        if (currentTab === "combined") {
            renderCombined();
        }
        
        updateJSONView();
        
        alert("JSON loaded successfully");

    } catch (e) {
        console.error(e);
        alert("Invalid JSON format");
    }
}

// -------- TAB SWITCH --------
function switchTab(name) {
    currentTab = name;
    selectedRowIndex = -1;

    document.querySelectorAll(".tab-button").forEach(b =>
        b.classList.toggle("active", b.innerText === name)
    );

    document.querySelectorAll(".tab-content").forEach(c =>
        c.classList.remove("active")
    );

    document.getElementById("tab-" + name).classList.add("active");

    if (name === "output_files") renderOutputFiles();
    else if (name === "combined") renderCombined();
    else if (name !== "JSON" && name !== "Instructions") renderTab(name);

}

// -------- INSTRUCTIONS --------
function instructionsHTML() {
    return `
<div class="instructions-container">

<h2>Instructions</h2>

${section("0. Environment Required", `
<ul>
<li><b>Python:</b> 3.11 or above</li>
<li><b>Packages:</b> pandas, numpy, mikeio1d, pythonnet</li>
</ul>
`)}

${section("1. Generate Template Spreadsheet and JSON", `
<pre>python res1d2excel.py</pre>
`)}

${section("2. Run with JSON Input", `
<p>Use <b>index.html</b> to create your JSON, then save as a file (e.g. inputs.json).</p>
<pre>python res1d2excel.py full_path_to_your_json_file</pre>

<p>Example:</p>
<pre>python res1d2excel.py "C:\\Data\\inputs.json"</pre>
`)}

${section("3. How to Use This Webpage", `
<h4>3.1 Element Tabs</h4>
<p>Use tabs: catchment, node, link, orifice, pump, regulation, weir, valve, bridge, direct_discharge, gate</p>

<h4>3.2 Data Entry Rules</h4>
<ul>
<li>Each record must include: <b>alias, quantity, muid</b></li>
<li>Chainage required for links & regulations</li>
</ul>

<div class="warning">
Chainage defaults to 0. Incorrect values will be adjusted automatically.
</div>

<pre>
alias            quantity    muid    chainage
CA38_Level       WaterLevel  10149   0
CA38_Discharge   Discharge   10149   15
</pre>

<h4>3.3 Result Files</h4>
<ul>
<li>First column must be: <b>network, runoff, or stats</b></li>
<li>Use <b>network</b> for MIKE network files and EPANET .res/.resx/.whr files</li>
<li>Short names must be UNIQUE</li>
</ul>

<div class="warning">
DO NOT duplicate short names
</div>

<h4>3.4 Output Files</h4>

<table class="instruction-table">
<tr><th>Option</th><th>File</th><th>Description</th></tr>
<tr><td>by_elements</td><td>by_element.xlsx</td><td>Organized by element</td></tr>
<tr><td>by_file</td><td>by_file.xlsx</td><td>Organized by result file</td></tr>
<tr><td>stats</td><td>stats.xlsx</td><td>Statistics output</td></tr>
</table>

<div class="warning">
DO NOT enable stats if result files already contain statistics
</div>

<p><b>Resampling examples:</b></p>
<ul>
<li>1 day</li>
<li>2 hour</li>
<li>5 minute</li>
<li>30 second</li>
</ul>
`)}

${section("4. Catchment Quantities", `
<p>NetRainfall, TotalRunOff, </p>
	<p>SurfaceStorage, OverlandFlow, OverlandFlowFirstReservoir, OverlandFirstReservoirStorage, OverlandSecondReservoirStorage, </p>
	<p>RootZoneStorage, InterFlow, InterFlowAndBaseFlow, InterFlowFirstReservoir, CapillaryFlux, InfiltrationToGroundWater, </p>
	<p>GroundWaterDepth, BaseFlow, LowerBaseFlow.</p>
`)}

${section("5. Network Quantities", `
<ul>
<li><b>Nodes:</b>
            <p>WaterVolume, WaterLevel, TotalOutflow, TotalInflow</p>
            </li>
<li><b>Links:</b>
			<p>WaterLevel, WaterVolume, TotalInflow, TotalOutflow, </p>
			<p>Discharge, DischargeVolume, DischargeVolumeNegative, DischargeVolumePositive, </p>
			<p>ControlStrategyId, FlowVelocity, </p>
			<p>DischargeInStructure, DischargeInStructureVolume, DischargeInStructureVolumeNegative, DischargeInStructureVolumePositive</p>
			</li>
<li><b>Orifices:</b>
			<p>WaterLevel, TotalInflow, TotalOutflow, </p>
			<p>Discharge, DischargeVolume, DischargeVolumeNegative, DischargeVolumePositive, </p>
			<p>ControlStrategyId, GateLevel, </p>
			<p>DischargeInStructure, DischargeInStructureVolume, DischargeInStructureVolumeNegative, DischargeInStructureVolumePositive, </p>
			<p>FlowAreaInStructure, FlowVelocityInStructure</p>
			</li>
<li><b>Pumps:</b>
			<p>WaterLevel, TotalInflow, TotalOutflow, </p>
			<p>Discharge, DischargeVolume, DischargeVolumeNegative, DischargeVolumePositive, </p>
			<p>ControlStrategyId, PumpIsActive, </p>
			<p>DischargeInStructure, DischargeInStructureVolume, DischargeInStructureVolumeNegative, DischargeInStructureVolumePositive</p>
			</li>
<li><b>Regulations:</b>
			<p>WaterLevel, WaterVolume, TotalInflow, TotalOutflow, </p>
			<p>Discharge, DischargeVolume, DischargeVolumeNegative, DischargeVolumePositive, </p>
			<p>ControlStrategyId, FlowVelocity, </p>
			<p>DischargeInStructure, DischargeInStructureVolume, DischargeInStructureVolumeNegative, DischargeInStructureVolumePositive</p>
			</li>
<li><b>Weirs:</b>
			<p>WaterLevel, TotalInflow, TotalOutflow, </p>
			<p>Discharge, DischargeVolume, DischargeVolumeNegative, DischargeVolumePositive, </p>
			<p>CrestLevel, ControlStrategyId, </p>
			<p>DischargeInStructure, DischargeInStructureVolume, DischargeInStructureVolumeNegative, DischargeInStructureVolumePositive, </p>
			<p>FlowAreaInStructure, FlowVelocityInStructure</p>
			</li>
</ul>
`)}

${section("5.1 EPANET Quantities", `
<p>Use result_type <b>network</b> for EPANET .res, .resx, and .whr files.</p>
<p>For .res files, keep the matching .inp file beside the result file.</p>
<ul>
<li><b>Nodes:</b> Demand, Head, Pressure, WaterQuality, Volume, Volume Percentage</li>
<li><b>Links:</b> Flow, Velocity, HeadlossPer1000Unit, AvgWaterQuality, StatusCode, Setting, ReactorRate, FrictionFactor</li>
<li><b>Pumps:</b> Pump efficiency, Pump energy costs, Pump energy</li>
</ul>
<p>EPANET pumps and valves can also be listed in the link tab.</p>
`)}

${section("6. Advection-Dispersion Quantities", `
<p>Examples using pollutant "sewage":</p>
<ul>
<li><b>Nodes:</b> sewageMass, sewage</li>
<li><b>Links:</b> sewageTransportMassPositive, sewageMass, sewageTransportMassNegative, sewageTransport, sewage, sewageTransportMass</li>
<li><b>Pumps/Weirs/Orifices:</b> sewageTransportMassPositive, sewageTransportMassNegative, sewageTransport, sewage, sewageTransportMass</li>
</ul>
`)}

${section("7. Statistics Quantities", `
<p>Examples:</p>
<ul>
<li><b>Nodes:</b>
			<p>WaterLevelAverage, WaterLevelMax, WaterLevelMaxTime, WaterLevelMin, WaterLevelMinTime, </p>
			<p>WaterVolumeAverage, WaterVolumeMax, WaterVolumeMaxTime, WaterVolumeMin, WaterVolumeMinTime, </p>
			<p>TotalInflow, TotalOutflow</p>
			</li>
<li><b>Links:</b>
			<p>WaterLevelAverage, WaterLevelMax, WaterLevelMaxTime, WaterLevelMin, WaterLevelMinTime, </p>
			<p>WaterVolumeAverage, WaterVolumeMax, WaterVolumeMaxTime, WaterVolumeMin, WaterVolumeMinTime, </p>
			<p>TotalInflow, TotalOutflow, </p>
			<p>DischargeAverage, DischargeMax, DischargeMaxTime, DischargeMin, DischargeMinTime, </p>
			<p>DischargeVolume, DischargeVolumeNegative, DischargeVolumePositive, </p>
			<p>ControlStrategyIdAverage, ControlStrategyIdMax, ControlStrategyIdMaxTime, ControlStrategyIdMin, ControlStrategyIdMinTime, </p>
			<p>DischargeInStructureAverage, DischargeInStructureMax, DischargeInStructureMaxTime, DischargeInStructureMin, DischargeInStructureMinTime, </p>
			<p>DischargeInStructureVolume, DischargeInStructureVolumeNegative, DischargeInStructureVolumePositive, </p>
			<p>FlowVelocityAverage, FlowVelocityMax, FlowVelocityMaxTime, FlowVelocityMin, FlowVelocityMinTime</p>
			</li>
<li><b>Orifices:</b>
			<p>WaterLevelAverage, WaterLevelMax, WaterLevelMaxTime, WaterLevelMin, WaterLevelMinTime, </p>
			<p>TotalInflow, TotalOutflow, </p>
			<p>DischargeAverage, DischargeMax, DischargeMaxTime, DischargeMin, DischargeMinTime, </p>
			<p>DischargeVolume, DischargeVolumeNegative, DischargeVolumePositive, </p>
			<p>GateLevelAverage, GateLevelMax, GateLevelMaxTime, GateLevelMin, GateLevelMinTime, </p>
			<p>ControlStrategyIdAverage, ControlStrategyIdMax, ControlStrategyIdMaxTime, ControlStrategyIdMin, ControlStrategyIdMinTime, </p>
			<p>DischargeInStructureAverage, DischargeInStructureMax, DischargeInStructureMaxTime, DischargeInStructureMin, DischargeInStructureMinTime, </p>
			<p>DischargeInStructureVolume, DischargeInStructureVolumeNegative, DischargeInStructureVolumePositive, </p>
			<p>FlowAreaInStructureAverage, FlowAreaInStructureMax, FlowAreaInStructureMaxTime, FlowAreaInStructureMin, FlowAreaInStructureMinTime, </p>
			<p>FlowVelocityInStructureAverage, FlowVelocityInStructureMax, FlowVelocityInStructureMaxTime, FlowVelocityInStructureMin, FlowVelocityInStructureMinTime</p>
			</li>
<li><b>Pumps:</b>
			<p>WaterLevelAverage, WaterLevelMax, WaterLevelMaxTime, WaterLevelMin, WaterLevelMinTime, </p>
			<p>TotalInflow, TotalOutflow, </p>
			<p>DischargeAverage, DischargeMax, DischargeMaxTime, DischargeMin, DischargeMinTime, </p>
			<p>DischargeVolume, DischargeVolumeNegative, DischargeVolumePositive, </p>
			<p>ControlStrategyIdAverage, ControlStrategyIdMax, ControlStrategyIdMaxTime, ControlStrategyIdMin, ControlStrategyIdMinTime, </p>
			<p>DischargeInStructureAverage, DischargeInStructureMax, DischargeInStructureMaxTime, DischargeInStructureMin, DischargeInStructureMinTime, </p>
			<p>DischargeInStructureVolume, DischargeInStructureVolumeNegative, DischargeInStructureVolumePositive</p>
			</li>
<li><b>Weir:</b>
			<p>WaterLevelAverage, WaterLevelMax, WaterLevelMaxTime, WaterLevelMin, WaterLevelMinTime, </p>
			<p>TotalInflow, TotalOutflow, </p>
			<p>DischargeAverage, DischargeMax, DischargeMaxTime, DischargeMin, DischargeMinTime, </p>
			<p>DischargeVolume, DischargeVolumeNegative, DischargeVolumePositive, </p>
			<p>CrestLevelAverage, CrestLevelMax, CrestLevelMaxTime, CrestLevelMin, CrestLevelMinTime, </p>
			<p>ControlStrategyIdAverage, ControlStrategyIdMax, ControlStrategyIdMaxTime, ControlStrategyIdMin, ControlStrategyIdMinTime, </p>
			<p>DischargeInStructureAverage, DischargeInStructureMax, DischargeInStructureMaxTime, DischargeInStructureMin, DischargeInStructureMinTime, </p>
			<p>DischargeInStructureVolume, DischargeInStructureVolumeNegative, DischargeInStructureVolumePositive, </p>
			<p>FlowAreaInStructureAverage, FlowAreaInStructureMax, FlowAreaInStructureMaxTime, FlowAreaInStructureMin, FlowAreaInStructureMinTime, </p>
			<p>FlowVelocityInStructureAverage, FlowVelocityInStructureMax, FlowVelocityInStructureMaxTime, FlowVelocityInStructureMin, FlowVelocityInStructureMinTime</p>
			</li>
<li><b>Tracer:</b>
<p>sewageAverage, sewageMax, sewageMaxTime, sewageMin, sewageMinTime,</p>
			<p>sewageTransportAverage, sewageTransportMax, sewageTransportMaxTime, sewageTransportMin, sewageTransportMinTime,</p>
            <p>sewageMassAverage, sewageMassMax, sewageMassMaxTime, sewageMassMin, sewageMassMinTime,</p>
            <p>sewageTransportMass, sewageTransportMassNegative, sewageTransportMassPositive</p>
			</li>
</ul>
`)}

</div>
    `;
}
// -------- START --------
init();
