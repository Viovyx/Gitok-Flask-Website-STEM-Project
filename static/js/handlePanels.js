var table_name;
var id_num;

var panel = document.getElementById("edit-panel");
var panel_fields = {};
fetch("/static/js/panel_fields.json")
    .then((response) => response.json())
    .then((json) => (panel_fields = json));

function openPanel(name, item = null, select_items = null) {
    const fields = panel_fields[name];
    if (!fields) {
        console.log(`[ERROR] Found format for '${name} (id: ${item["id"]})'`);
        return;
    }

    var title = document.getElementById("title");
    var form = document.getElementById("form");
    var delete_form = document.getElementById("delete-form");
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
}

function generateOptions(fields, select_items = null, item = null) {
    const id = document.createElement("input");
    id.type = "hidden";
    id.name = "id";
    optionsHTML = "";

    for (const [key, value] of Object.entries(fields)) {
        if (key != "table") {
            if (key == "id") {
                id.value = item ? item["id"] : value["default"];
            } else if (
                value["index"] != "fixed" &&
                (value["type"] != "password" || !item)
            ) {
                optionsHTML += `<label for=${key}>${key}: <b>*</b></label>`;

                if (value["type"] == "password") {
                    optionsHTML += '<p class="subscript">This can only be set once! Changes have to be made by owner account.</p>'
                }

                if (value["index"] == "unique") {
                    optionsHTML += `<p class="subscript">Must be unique accross all ${fields["table"]}!</p>`;
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
                        }>${option["id"]} - ${
                            option[value["index_name"]]
                        }</option>`;
                    }
                    optionsHTML += `</select>`;
                } else {
                    optionsHTML += `
                        <input
                            type=${value["type"]}
                            id=${key}
                            name=${key}
                            placeholder=${
                                item
                                    ? item[key]
                                    : value["default"]
                                    ? value["default"]
                                    : key
                            }
                            ${
                                item && value["type"] != "password"
                                    ? "value=" + item[key]
                                    : ""
                            }
                            ${
                                value["type"] != "checkbox"
                                    ? "required"
                                    : item && item[key]
                                    ? "checked"
                                    : ""
                            }
                        /> 
                        ${
                            value["type"] == "checkbox"
                                ? `<input type="hidden" name=${key} id=${key} value=${value["default"]}><br>`
                                : ""
                        }
                    `;
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
        }
    }

    return { id, optionsHTML };
}

function closePanel() {
    panel.classList.add("hidden");
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
