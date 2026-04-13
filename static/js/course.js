$(document).ready(function(){
    $("#btn_add_course").click((event)=>{
        event.preventDefault();
        $('#modal-loading').modal('show');
        fetch('/course/add',{
            method:"GET"
        }).then((response)=>{
            return response.json()
        }).then((data)=>{
            //get school, departments,courses details
            createCourseForm(data.response)
            $('#modal-loading').modal('hide');
        }).catch((error)=>{
            $('#modal-loading').modal('hide');
        })
    })
    createCourseForm = function(data){
        const fields = [
            // { type: "text", id: "input-course-code", label: "Course code", col: "col-md-6" },
            { type: "text", id: "input-course-name", label: "Name", col: "col-md-12" },
            {
                type: "select",
                id: "input-department",
                label: "Department",
                col: "col-md-12",
                options: ["Choose...", "..."]
            },
            { 
                type: "hidden", 
                id: "operation-type", 
                value: "add_course" 
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
        populateForm(data,false,true,false, false,false);
    }
})