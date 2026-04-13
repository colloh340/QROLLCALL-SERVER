$(document).ready(function(){
    $("#btn_add_student").click((event)=>{
        $('#modal-loading').modal('show');

        fetch('/students/add', {
            method: "GET",
            headers: {
                'Client': 'qrollcall.com'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            createStudentForm(data.response); // Process form data
        })
        .catch(error => {
            console.error("Error:", error); // Log error for debugging
        })
        .finally(() => {
            $('#modal-loading').modal('hide'); // Always hide modal
        });

    })
    createStudentForm = function(data){
        var fields = [
        { type: "text", id: "input-first-name", label: "First Name", col: "col-md-6" },
        { type: "text", id: "input-last-name", label: "Last Name", col: "col-md-6" },
        { type: "email", id: "input-email", label: "Email", col: "col-md-6" },
        { type: "text", id: "input-reg-no", label: "Registration Number", col: "col-md-6" },
        {
            type: "select",
            id: "input-school",
            label: "School",
            col: "col-md-6",
            options: ["Choose...", "..."],
            class: "select2", // Add Select2 class
            dropdown: "general_modal"
        },
        {
            type: "select",
            id: "input-department",
            label: "Department",
            col: "col-md-6",
            options: ["Choose...", "..."],
            class: "select2", // Add Select2 class
            dropdown: "general_modal"
        },
        {
            type: "select",
            id: "input-course",
            label: "Course",
            col: "col-md-12",
            options: ["Choose...", "..."],
            class: "select2", // Add Select2 class
            dropdown: "general_modal"
        },
        { 
            type: "hidden", 
            id: "operation-type", 
            value: "add_student" 
        },
        { 
            type: "hidden", 
            id: "csrfmiddlewaretoken", 
            value: $("input[name='csrfmiddlewaretoken']").val()
        }
        ];
        
        const container = createForm(fields);
    
        const content = document.getElementById("general_modal_body");

        // Remove all existing HTML by clearing the innerHTML
        content.innerHTML = "";

        // Append the new container to the content
        content.appendChild(container);
        // Reinitialize Select2 after adding form to the modal
        $(".select2").select2(); 

        populateForm(data, true,true,true, false,false)
        showReportModal();

    }

})