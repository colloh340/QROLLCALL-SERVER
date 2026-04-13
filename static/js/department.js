$(document).ready(function(){
    $("#btn_add_department").click((event)=>{
        $('#modal-loading').modal('show');
        fetch('/department/add',{
            method:"GET"
        }).then((response)=>{
            return response.json()
        }).then((data)=>{
            createDepartmentForm(data.response);
            $('#modal-loading').modal('hide');
        }).catch((error)=>{
            console.log("Error: "+error);
            $('#modal-loading').modal('hide');
        })
    })
    createDepartmentForm = function(data){
        const fields = [
            // { type: "text", id: "input-department-id", label: "Department code", col: "col-md-6" },
            { type: "text", id: "input-department-name", label: "Name", col: "col-md-12" },
            {
                type: "select",
                id: "input-school",
                label: "School",
                col: "col-md-12",
                options: ["Choose...",]
            },
            { type: "textarea", id: "input-department-description", label: "Description", col: "col-md-12", placeholder: "Enter description (optional)" },
            { 
                type: "hidden", 
                id: "operation-type", 
                value: "add_department" 
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
        populateForm(data,true, false, false, false,false);
        
    }
})