$(document).ready(function(){
    $("#btn_add_school").click((event)=>{
        $('#modal-loading').modal('show');
        setTimeout(() => {
            createAddSchoolForm();
            $('#modal-loading').modal('hide');
        }, 500);
    })
    createAddSchoolForm = function(){
        const fields = [
            // { type: "text", id: "input-school", label: "School Code", col: "col-md-6" },
            { type: "text", id: "input-school-name", label: "Name", col: "col-md-12" },
            { type: "textarea", id: "input-school-description", label: "Description", col: "col-md-12", placeholder: "Enter description (optional)" },
            { 
                type: "hidden", 
                id: "operation-type", 
                value: "add_school" 
            },
            { 
                type: "hidden", 
                id: "csrfmiddlewaretoken", 
                value: $("input[name='csrfmiddlewaretoken']").val()
            }
        ]
        const container = createForm(fields);
    
        const content = document.getElementById("content");

        // Remove all existing HTML by clearing the innerHTML
        content.innerHTML = "";

        // Append the new container to the content
        content.appendChild(container);
    }
})