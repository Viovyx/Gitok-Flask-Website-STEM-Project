var table_name;
var id_num;

var panel = document.getElementById("edit-panel");
var panel_loader = document.getElementById("edit-panel-loader");
var panel_fields = {};
fetch("/static/js/panel_fields.json")
    .then((response) => response.json())
    .then((json) => (panel_fields = json));

// Connect to socketio
var socket = io.connect();

async function openPanel(name, item = null) {
    panel_loader.classList.remove("hidden");

    const fields = panel_fields[name];
    if (!fields) {
        console.log(`[ERROR] Found format for '${name} (id: ${item["id"]})'`);
        return;
    }

    if (fields["select_table"]) {
        var select_items = await getSelectItems(fields["select_table"]);
    }

    var title = document.getElementById("title");
    var delete_form = document.getElementById("delete-form");
    var form = document.getElementById("form");
    form.innerHTML = "";

    const action = document.createElement("input");
    action.type = "hidden";
    action.name = "action";

    // id is given => edit item
    if (item) {
        table_name = fields["table"];
        id_num = item["id"];
        delete_form.classList.remove("hidden");

        title.textContent = `Edit Item - ${name} (id: ${item["id"]})`;
        action.value = "edit";

        const { id, optionsHTML } = generateOptions(fields, select_items, item);
        form.appendChild(id);
        form.innerHTML += optionsHTML;
    }
    // id is not given => create item
    else {
        delete_form.classList.add("hidden");
        title.textContent = `Create Item - ${name}`;
        action.value = "create";

        const { id, optionsHTML } = generateOptions(fields, select_items);
        form.appendChild(id);
        form.innerHTML += optionsHTML;
    }

    const delete_input = document.createElement("input");
    delete_input.type = "hidden";
    delete_input.name = "delete_input";
    delete_input.value = "false";

    const table = document.createElement("input");
    table.type = "hidden";
    table.name = "table";
    table.value = fields["table"];

    form.appendChild(delete_input);
    form.appendChild(table);
    form.appendChild(action);

    form.innerHTML += `
            <button type="submit">Submit</button>
            <button type="button" class="cancel" onclick="closePanel()">
                Cancel
            </button>
        `;

    panel.classList.remove("hidden");
    document.querySelector(".edit-panel .panel-wrapper").scrollTop = 0;
}

async function getSelectItems(select_table) {
    return new Promise((resolve, reject) => {
        socket.emit("getSelectItems", {
            table: select_table["name"],
            index: select_table["index"],
        });

        socket.on("selectItemsResponse", (data) => {
            if (data.error) {
                reject(data.error);
            } else {
                resolve(data.items);
            }
        });
    });
}

function generateOptions(fields, select_items = null, item = null) {
    const id = document.createElement("input");
    id.type = "hidden";
    id.name = "id";
    optionsHTML = "";

    for (const [key, value] of Object.entries(fields)) {
        if (key != "table" && key != "select_table") {
            if (key == "id") {
                id.value = item ? item["id"] : value["default"];
            } else if (
                value["index"] != "fixed" &&
                (value["type"] != "password" || !item)
            ) {
                optionsHTML += `<label for=${key}>${key}: <b>*</b></label>`;

                if (value["type"] != "checkbox") {
                    optionsHTML += `<p class="subscript">${value["description"]}</p>`;
                }

                if (value["type"] == "select") {
                    optionsHTML += `<select name=${key} id=${key}>`;
                    for (const option of select_items) {
                        optionsHTML += `<option value=${option["id"]} ${
                            item
                                ? item[value["index"]] == option["id"]
                                    ? "selected"
                                    : ""
                                : ""
                        }>${option["id"]} - ${option["value"]}</option>`;
                    }
                    optionsHTML += `</select>`;
                } else {
                    if (value["type"] == "checkbox") {
                        optionsHTML += `
                            <input
                                type="checkbox"
                                id=${key}
                                name=${key}
                                value="true"
                                ${item && item[key] ? "checked" : ""}
                            />
                            <input type="hidden" name=${key} id=${key} value="false">
                            <br>
                        `;
                    } else {
                        optionsHTML += `
                            <input
                                required
                                type=${value["type"]}
                                id=${key}
                                name=${key}
                                placeholder="${
                                    item
                                        ? item[key]
                                        : value["default"]
                                        ? value["default"]
                                        : key
                                }"
                                ${
                                    item && value["type"] != "password"
                                        ? `value="${item[key]}"`
                                        : ""
                                }
                            />
                        `;
                    }
                }
            } else if (!item) {
                optionsHTML += `
                        <input
                            type=hidden
                            id=${key}
                            name=${key}
                            value=${value["default"]}
                        />
                    `;
            }

            if (value["type"] == "checkbox") {
                optionsHTML += `<p class="subscript">${value["description"]}</p>`;
            }
        }
    }

    return { id, optionsHTML };
}

function closePanel() {
    panel.classList.add("hidden");
    panel_loader.classList.add("hidden");
}

function confirmDelete() {
    const deleteForm = document.getElementById("delete-form");

    const table = document.createElement("input");
    table.type = "hidden";
    table.name = "table";
    table.value = table_name;

    const id = document.createElement("input");
    id.type = "hidden";
    id.name = "id";
    id.value = id_num;

    deleteForm.appendChild(table);
    deleteForm.appendChild(id);

    return confirm("Are you sure you want to delete this item?");
}
