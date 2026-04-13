$(document).ready(async function(){
    //$("#btn_add_staff").click(async () => {
        $('#modal-loading').modal('show');
    
        try {
            const response = await fetch('/lecturer/add');
            const data = await response.json();
            createLecturerForm(data.response);
        } catch (error) {
            console.error("Error fetching lecturer data:", error);
        } finally {
            $('#modal-loading').modal('hide');
        }
    //});
    
    
})
function createLecturerForm(data){
    // Array to define the input fields and their properties
    const fields = [
    { type: "text", id: "input-first-name", label: "First Name", col: "col-md-6" },
    { type: "text", id: "input-last-name", label: "Last Name", col: "col-md-6" },
    { type: "email", id: "input-email", label: "Email", col: "col-md-12" },
    // { type: "text", id: "input-staff-id", label: "Staff ID", col: "col-md-6" },
    {
        type: "select",
        id: "input-school",
        label: "School",
        col: "col-md-12",
        options: ["Choose...", "..."],
        class: "select2", // Add Select2 class
        // dropdown: "general_modal"
    },
    {
        type: "select",
        id: "input-department",
        label: "Department",
        col: "col-md-12",
        options: ["Choose...", "..."],
        class: "select2", // Add Select2 class
        // dropdown: "general_modal"
    },
    { type: "password", id: "password", label: "Password", col: "col-md-12" },
    { type: "password", id: "password2", label: "Confirm Password", col: "col-md-12" },
    { 
        type: "hidden", 
        id: "operation-type", 
        value: "add_staff" 
    },
    { 
        type: "hidden", 
        id: "csrfmiddlewaretoken", 
        value: $("input[name='csrfmiddlewaretoken']").val()
    }
    
    ];
    const container = createForm(fields);

    const content = document.getElementById("container_add_staff");

    // Remove all existing HTML by clearing the innerHTML
    content.innerHTML = "";

    // Append the new container to the content
    content.appendChild(container);

    // Reinitialize Select2 after adding form to the modal
    $(".select2").select2(); 

    populateForm(data, true,true, false, false,false);
    // showReportModal();

}