$(document).ready(function(){
    $("#btn_edit_course_unit").click((event)=>{
        event.preventDefault();
        $('#modal-loading').modal('show');

        fetch("/courses", {
            method: "GET",
        })
        .then(response => response.json())
        .then(data => {
            var status = data.status;
            var message = data.message;

            if (status == 200) {
                const container = createFormCourseUnit(data.response);
                const content = document.getElementById("content");

                // Remove all existing HTML
                content.innerHTML = "";

                // Append the new container to the content
                content.appendChild(container);
            } else {
                console.log("Message: " + message);
            }
        })
        .catch(error => {
            console.log("Error: " + error);
        })
        .finally(() => {
            $('#modal-loading').modal('hide'); // Always hide modal
        });


        
    });

    function createFormCourseUnit(data){
        const container = document.createElement("div");
        container.className = "w-75 m-auto";
        const form = document.createElement("form");
        form.className = "row g-3";
        form.id = "course_unit_form";
        form.method = "GET";
        const fields = [
            {
                type: "select",
                id: "input-course",
                label: "Filter course",
                col: "col-md-12",
                options: ["Choose...", "..."]
            },
            { type: "text", id: "input-unit-code", label: "Enter unit code", col: "col-md-7" },
            { type: "button", id: "btn-search-unit", label: "Add", col: "col-md-5", class:"btn btn-outline-primary d-flex" }
        ]
        let input;
        fields.forEach((field)=>{
            const fieldDiv = document.createElement("div");
            const label = document.createElement("label");
            fieldDiv.className = field.col;
            if(field.type !== "button" && field.id !== "input-unit-code"){
                label.className = "form-label";
                label.htmlFor = field.id;
                label.textContent = field.label;
            }
            
            if (field.type === "select") {
                input = document.createElement("select");
                input.className = "form-select";
            
                // Add an empty option for the placeholder
                const placeholderOption = document.createElement("option");
                placeholderOption.textContent = ""; // Keep text empty
                placeholderOption.value = ""; // Empty value for placeholder
                placeholderOption.selected = true; // Ensure it's selected by default
                placeholderOption.disabled = true; // Prevent user from selecting it again
                input.appendChild(placeholderOption);
                // Populate the options
                data.forEach((course) => {
                    const option = document.createElement("option");
                    option.textContent = course.course_name;
                    option.value = course.course_code;
                    input.appendChild(option);
                });            
                // Initialize Select2
                
                $(document).ready(function () {
                    $(`#${field.id}`).select2({
                        placeholder: "Search for an option",
                        allowClear: true,
                        width: '100%' // Ensures proper resizing
                    });
                    $(`#${field.id}`).on("change", function(){
                        const selectedCourseId = $(this).val();
                        const selectedCourse = data.find(course => course.course_code === selectedCourseId);
                        if(selectedCourse != null){
                            buildTable(selectedCourse.units)
                        }
                    })
                });

            }
            else if(field.type === "text"){
                input = document.createElement("input");
                input.type = field.type;
                input.className = "form-control";
                input.placeholder = field.label;
            }else if(field.type === "button"){
                const buttonDiv = document.createElement("div");
                buttonDiv.className = field.col; // Add the column class (col-6)

                // Create the button element
                const btn = document.createElement("button");
                btn.className = field.class; // Add button class
                btn.type = field.type; // Set button type

                btn.appendChild(document.createTextNode(field.label));

                // Append the button to the buttonDiv
                buttonDiv.appendChild(btn);
                input = buttonDiv;

                $(btn).click((event)=>{
                    var unit_code = $("#input-unit-code").val();
                    var course_code = $("#input-course").val();

                    const is_valid = verify();
                    var formData = new FormData();
                    formData.append("unit_code", unit_code);
                    formData.append("course_code", course_code);
                    formData.append("csrfmiddlewaretoken", $("input[name='csrfmiddlewaretoken']").val());
                    if(is_valid){
                        $('#modal-loading').modal('show');
                        fetch(`/courses/${course_code}/units/add`,{
                            method: "POST", body: formData
                        }).then((response)=>{
                            $('#modal-loading').modal('hide');
                            return response.json()
                        }).then((response_data)=>{
                            const message = response_data.message;
                            const status = response_data.status;
                            createToast(message, status);
                            if(status == 200 || status == 201){
                                console.log("Unit added successfully")
                                var selectedCourse = data.find(course => course.course_code === course_code);
                                selectedCourse.units = response_data.units;
                                buildTable(response_data.units);
                            }else{
                                console.log("Something went wrong!")
                            }

                        }).catch((error)=>{
                            console.log("Error: "+error);
                            $('#modal-loading').modal('hide');
                        })
                    }else{
                        console.log("Invalid data")
                    }
                    
                })
            }
            input.id = field.id;
            input.name = field.id;
            fieldDiv.appendChild(label);
            fieldDiv.appendChild(input);
            form.appendChild(fieldDiv);
        })
        var table_unit_container = document.createElement("div");
        table_unit_container.id = "table_wrapper";
        form.appendChild(table_unit_container);
        container.appendChild(form)

        return container;
    }
    function verify(){
        var unit_code = $("#input-unit-code").val();
        var course_code = $("#input-course").val();
        if(course_code.length === 0){
            createToast("select course", 300);
            return false;
        }
        if(unit_code.length === 0){
            createToast("Enter unit code", 300);
            return false;
        }
        return true;
    }
    function buildTable(data) {
        $("#table_wrapper").html(""); // Clear wrapper
    
        var unit_table = document.createElement("table");
        unit_table.className = "table";
    
        // Table head
        var table_head = document.createElement("thead");
        var tr_head = document.createElement("tr");
        ["#", "Unit Code", "Name", "Department", "Action"].forEach((value) => {
            var th = document.createElement("th");
            th.setAttribute("scope", "col");
            th.textContent = value;
            tr_head.appendChild(th);
        });
        table_head.appendChild(tr_head);
        unit_table.appendChild(table_head);
    
        // Table body
        var table_body = document.createElement("tbody");
        const courseUnit = data;
    
        if (courseUnit.length > 0) {
            for (let i = 0; i < courseUnit.length; i++) {
                var tr = document.createElement("tr");
    
                // Row number
                var th = document.createElement("th");
                th.setAttribute("scope", "row");
                th.textContent = i + 1;
    
                // Unit Code
                var td_code = document.createElement("td");
                td_code.textContent = courseUnit[i].unit_code;
    
                // Unit Name
                var td_name = document.createElement("td");
                td_name.textContent = courseUnit[i].unit_name;
    
                // Department
                var td_dept = document.createElement("td");
                td_dept.textContent = courseUnit[i].department;
    
                // Action Button
                var td_btn = document.createElement("td");
                var action = document.createElement("a");
                action.textContent = "drop";
                action.href = "#"; // Prevent navigation
                td_btn.appendChild(action);
    
                // Append all columns to the row
                tr.appendChild(th);
                tr.appendChild(td_code);
                tr.appendChild(td_name);
                tr.appendChild(td_dept);
                tr.appendChild(td_btn);
    
                // Append the row to the table body
                table_body.appendChild(tr);
            }
            var table_container  = document.createElement("div");
            table_container.className = "table-responsive-md";
            unit_table.appendChild(table_body);
            table_container.appendChild(unit_table);
            $("#table_wrapper").append(table_container); // Append the table
        } else {
            $("#table_wrapper").append(document.createTextNode("No units. Add new"));
        }
    }
    
    
});
