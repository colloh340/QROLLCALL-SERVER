$(document).ready(function(){
    $("#btn_add_unit").click((event)=>{
        $('#modal-loading').modal('show');
        fetch('/units/add',{
            method:"GET"
        }).then((response)=>{
            return response.json()
        }).then((data)=>{
            //get school, departments,courses details
            createAddUnitForm(data.response)
            $('#modal-loading').modal('hide');
        }).catch((error)=>{
            $('#modal-loading').modal('hide');
        })
    })
    createAddUnitForm = function(data){
        const fields = [
            { type: "text", id: "input-unit-code", label: "Unit Code", col: "col-md-6", placeholder: "e.g., ITB1400 or ICB3102" },
            { type: "text", id: "input-unit-name", label: "Name", col: "col-md-6" },
            {
                type: "select",
                id: "input-department",
                label: "Department",
                col: "col-md-6",
                options: ["Choose...", "..."]
            },
            {
                type: "select",
                id: "input-semester",
                label: "Semester offered",
                col: "col-md-6",
                options: ["1", "2"]
            },
            { 
                type: "hidden", 
                id: "operation-type", 
                value: "add_unit" 
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
        console.log("DATA: "+data)
        populateForm(data,false,true,false,false,false);
    }
})
