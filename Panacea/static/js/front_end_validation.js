const my_form = document.getElementById("summary_data_form");
const old_values = formDataToObject(my_form);

let error_dict = {};  //dictionary for storing errors that are being displayed

//Error messages and error message generators
const err_msg_previous_report_needs_comment = "Please provide a brief comment regarding the reason for this historical update.";
const err_msg_fifteen_percent_change = "There is a greater than 15% change from last year, please provide a comment explaining this change.";
function greater_than_error_msg(lesser_label, greater_label){
    return (greater_label + " must be greater than " + lesser_label + ".")
}

//List of error messages that may be removed by comments
// // When adding new validation rule that are removed by comments be sure to add them to validate_if_null function
// // TODO make it so one does not need to do this.
let err_msg_removable_by_comment = [err_msg_previous_report_needs_comment, err_msg_fifteen_percent_change];

//dictionary that contains the labels for the fields that must be greater than the other field: key > value
const total_greater_than_dict = {
    'Total Vehicle Hours':'Revenue Vehicle Hours',
    'Total Vehicle Miles':'Revenue Vehicle Miles'
};

//List of  fields to apply total greater than to - also need these as a pair of lists
const greater_fields = Object.keys(total_greater_than_dict);
const lesser_fields = greater_fields.map(function (key) {return total_greater_than_dict[key]});

//Reads data from forms and stores in an object to tell if values change (cut and pasted from SO)
function formDataToObject(elForm) {
    if (!elForm instanceof Element) return;
    let fields = elForm.querySelectorAll('input, select, textarea'),
        o = {};
    for (let i=0, imax=fields.length; i<imax; ++i) {
        let field = fields[i],
            sKey = field.name || field.id;
        if (field.type==='button' || field.type==='image' || field.type==='submit' || !sKey) continue;
        switch (field.type) {
            case 'checkbox':
                o[sKey] = +field.checked;
                break;
            case 'radio':
                if (o[sKey]===undefined) o[sKey] = '';
                if (field.checked) o[sKey] = field.value;
                break;
            case 'select-multiple':
                let a = [];
                for (let j=0, jmax=field.options.length; j<jmax; ++j) {
                    if (field.options[j].selected) a.push(field.options[j].value);
                }
                o[sKey] = a;
                break;
            default:
                o[sKey] = field.value;
        }
    }
    // console.log('Form data:\n\n' + JSON.stringify(o, null, 2));
    return o;
}

//Add event listeners to fields that need validation
const validate_table_cells_previous_years = document.querySelectorAll('.previous-year, .two-years-ago');
const validate_table_cells_this_year = document.querySelectorAll('.this-year');
const comment_table_cells = document.querySelectorAll(".comments");

////validation on this years data
for(let i = 0; i < validate_table_cells_this_year.length; i++) {
    let validate_field = validate_table_cells_this_year[i].querySelector('.validate-field');
    if(validate_field != undefined){
        validate_field.addEventListener("blur", fifteen_percent_needs_comment, true);
        validate_field.addEventListener("blur", total_greater_than, true);
        validate_field.addEventListener("blur", set_button_status, true);
    }
}
////Validation on previous year fields - comments on updates
for(let i = 0; i < validate_table_cells_previous_years.length; i++) {
    let validate_field = validate_table_cells_previous_years[i].querySelector('.validate-field');
    if(validate_field != undefined){
        validate_field.addEventListener("blur", updates_to_past_data_need_comments, true);
        validate_field.addEventListener("blur", set_button_status, true);
    }
}
////Remove errors on comment
for(let i = 0; i < comment_table_cells.length; i++) {
    let comment_field = comment_table_cells[i].querySelector('.comment-field');
    if(comment_field != undefined){
        comment_field.addEventListener("blur", comment_entered, true);
        comment_field.addEventListener("blur", validate_if_null, true);
        comment_field.addEventListener("blur", set_button_status, true);
    }
}

// Validator functions
function validate_if_null() {
    if (this.value == ""){
        let elem = getPreviousElement(this.parentElement, 'summary-input');
        if (elem.classList.contains('this-year')){
            fifteen_percent_needs_comment.call(elem.childNodes[0])
        } else {
            updates_to_past_data_need_comments.call(elem.childNodes[0])
        }
    }
}

function comment_entered() {
    let input_elem = get_comments_input_element(this);
    if (element_has_error(input_elem) && this.value != ''){
        remove_err_msg(input_elem);
    }
}

function updates_to_past_data_need_comments() {
    let err_msg = err_msg_previous_report_needs_comment;
    if(changed_from_previous_report(this) && !element_has_comment(this)){
        if(!element_has_error(this, err_msg)){
            add_err_msg(this, err_msg)
        }
    } else if (!changed_from_previous_report(this) && element_has_error(this, err_msg)){
        remove_err_msg(this, err_msg)
    }
}

function total_greater_than(){
    console.log('total_greater_than');
    let input_label = get_input_label_text(this);
    let is_lesser_field = lesser_fields.includes(input_label);
    let is_greater_field = greater_fields.includes(input_label);
    let lesser_field, lesser_value, greater_field, greater_value, index, year_class;

    if (is_lesser_field || is_greater_field){
        year_class = get_field_year_class(this);
        if(is_lesser_field){
            index = lesser_fields.indexOf(input_label);
            lesser_field = this;
            lesser_value = this.value;
            greater_field = get_field_by_label_and_class(greater_fields[index], year_class);
            greater_value = greater_field.value
        } else {
            index = greater_fields.indexOf(input_label);
            lesser_field = get_field_by_label_and_class(lesser_fields[index], year_class);
            lesser_value = lesser_field.value;
            greater_field = this;
            greater_value = this.value

        }
        lesser_value = parseFloat(lesser_value.replace(/[$,]/g, ""));
        greater_value = parseFloat(greater_value.replace(/[$,]/g, ""));

        let err_msg =  greater_than_error_msg(lesser_fields[index], greater_fields[index]);
        if (lesser_value > greater_value && !element_has_error(lesser_field , err_msg)){
            add_err_msg(lesser_field, err_msg);
            add_err_msg(greater_field, err_msg);
        } else if (lesser_value < greater_value && element_has_error(lesser_field , err_msg)){
            remove_err_msg(lesser_field, err_msg);
            remove_err_msg(greater_field, err_msg)
        }
    }
}

function set_button_status(){
    // disables the submit button if there are any errors in the error dictionary
    document.getElementById("submit_btn").disabled = Object.keys(error_dict).length > 0;
}

function fifteen_percent_needs_comment() {
    let err_msg = err_msg_fifteen_percent_change;
    if (this.value == ""){
        remove_err_msg(this, err_msg)
        return true
    }
    let new_value = parseFloat(this.value.replace(/[$,]/g, ""));
    let previous_value = getPreviousElement(this.parentElement, 'summary-input').childNodes[0].value;
    previous_value = parseFloat(previous_value.replace(/[$,]/g, ""));
    let greater_than_15 = Math.abs((previous_value - new_value) / new_value) >= .15;

    if (greater_than_15) {
        if (!element_has_error(this, err_msg) && !element_has_comment(this)) {
            add_err_msg(this, err_msg)
        }
    } else if (element_has_error(this, err_msg)) {
        remove_err_msg(this, err_msg)
    }
}

//Helper functions
// // elem should always refer to the form input element, elem.ParentElement is the table cell

// // Helper functions to get next & previous sibling with given class
function getNextElement(any_elem, className) {
    let next = any_elem.nextElementSibling;
    while (next && !next.classList.contains(className)) next = next.nextElementSibling;
    return next;
}
function getPreviousElement(any_elem, className) {
    let next = any_elem.previousElementSibling;
    while (next && !next.classList.contains(className)) next = next.previousElementSibling;
    return next;
}

// // Other helper functions
function changed_from_previous_report(elem){
    return !(parseFloat(old_values[elem.name]).toFixed(2) == parseFloat(elem.value.replace(/\$|,/g, "")).toFixed(2));
}

function element_has_error(elem, err_msg){
    if (error_dict[elem.name] == null) {
        return false
    } else if (err_msg !== undefined){
        return error_dict[elem.name].includes(err_msg);
    } else {
        return error_dict[elem.name].length > 0
    }
}

function add_err_msg(elem, err_msg) {
    if (error_dict[elem.name] == null) {
        error_dict[elem.name] = [];
    }
    error_dict[elem.name].push(err_msg);
    elem.classList.add("is-invalid");
    let node = document.createElement("LI");
    let textnode = document.createTextNode(err_msg);
    node.appendChild(textnode);
    let errorlist_elem = getNextElement(elem.parentElement, 'validation_errors');
    errorlist_elem.childNodes[0].appendChild(node);
}

function element_has_comment(elem) {
    let elem_comments = getNextElement(elem.parentElement, 'comments').childNodes[0];
    return !(elem_comments.value == '')
}

function get_comments_input_element(elem){
    return getPreviousElement(elem.parentElement, 'summary-input').childNodes[0];
}

function error_list_remove_li(errorlist_elem, err_msg){
    for (let i = 0; i < errorlist_elem.length; i++){
        if (errorlist_elem[i].textContent === err_msg){
            errorlist_elem[i].remove();
            break
        }
    }
}

function remove_err_msg(elem, err_msg) {
    // remove_err_msg without an err_msg parameter will remove all error messages that require a comment
    //select error list
    let errorlist_elem = getNextElement(elem.parentElement, 'validation_errors').childNodes[0];
    errorlist_elem = errorlist_elem.querySelectorAll('li');
    //if no specific err_msg remove all error msg
    if (element_has_error(elem) && err_msg == null){
        let msg_to_remove = error_dict[elem.name];
        for(let i=0; i < msg_to_remove.length; i++){
            if(err_msg_removable_by_comment.includes(msg_to_remove[i])){
                remove_err_msg(elem, msg_to_remove[i])
            }
        }
    } else if (element_has_error(elem, err_msg)){
        let index = error_dict[elem.name].indexOf(err_msg);
        error_dict[elem.name].splice(index, 1);
        error_list_remove_li(errorlist_elem, err_msg);
        if(!element_has_error(elem)){
            elem.classList.remove("is-invalid");
            delete error_dict[elem.name];
        }
    }
}

function get_input_label_text(elem){
    let label = getPreviousElement(elem.parentElement, 'label_values').textContent;
    return label
}

function get_field_by_label_and_class(label_text, field_class){
    let all_labels = document.querySelectorAll('.label_values');
    for(let i=0; i < all_labels.length; i++){
        console.log(all_labels[i].textContent);
        if(all_labels[i].textContent == label_text){
            return getNextElement(all_labels[i], field_class).childNodes[0]
        }
    }
}

function get_field_year_class(elem){
    console.log('class_list:');
    let class_list = elem.parentElement.classList;
    console.log(class_list);
    if (class_list.contains('this-year')){
        return 'this-year'
    } else if (class_list.contains('previous-year')){
        return 'previous-year'
    } else if (class_list.contains('two-years-ago')){
        return 'two-years-ago'
    }
}

// may need this at some point - thought i did
/*function element_error_count(elem) {
    return error_dict[elem.name].length
}*/