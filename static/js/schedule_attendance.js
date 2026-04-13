$(document).ready(function(){
    $('#modal-loading').modal('show');

    fetch('/attendance/schedule', {
        method: "GET"
    })
    .then(response => response.json())
    .then(data => {
        scheduleForm(data.response);
    })
    .catch(error => {
        console.log("Error: " + error);
    })
    .finally(() => {
        setTimeout(() => {
            $('#modal-loading').modal('hide');
        }, 500);
    });
    
    scheduleForm = function(data){
        const fields = [
            {
                type: "select",
                id: "input-course",
                label: "Course",
                col: "col-md-12",
                options: ["Choose...", "..."]
            },
            {
                type: "select",
                id: "input-unit",
                label: "Unit",
                col: "col-md-6",
                options: ["Choose...", "..."]
            },
            // {
            //     type: "select",
            //     id: "input-instructor",
            //     label: "Instructor",
            //     col: "col-md-6",
            //     options: ["Choose...", "..."]
            // },
            {
                type: "date",
                id: "input-date",
                label: "Date",
                col: "col-md-6"
            },
            {
                type: "time",
                id: "input-start-time",
                label: "Start Time",
                col: "col-md-6"
            },
            {
                type: "time",
                id: "input-end-time",
                label: "End Time",
                col: "col-md-6"
            },
            { 
                type: "hidden", 
                id: "operation-type", 
                value: "schedule_attendance" 
            },
            { 
                type: "hidden", 
                id: "csrfmiddlewaretoken", 
                value: $("input[name='csrfmiddlewaretoken']").val()
            }
        ]
        var row_container = document.createElement("div");
        row_container.classList.add("row");
        var qr_viewer = document.createElement("div");
        qr_viewer.innerHTML = `
        <div class="d-flex flex-column align-items-center justify-content-center mt-4">
        <div class="fs-3 text-muted fw-bold">Generated QR Code</div>
        <div id="qr_div"></div>
        <div id="btn_export_wrapper" class="dropdown d-none">
        <button class="btn btn-secondary dropdown-toggle" type="button" id="export_btn" data-bs-toggle="dropdown" aria-expanded="false">
            Export file
        </button>
        <ul class="dropdown-menu" aria-labelledby="export_btn">
            <li><a class="dropdown-item" href="#" id="btn_download_image">Open Image</a></li>
            <li><a class="dropdown-item" href="#" id="btn_download_pdf">Download PDF</a></li>
        </ul>
        </div>
        </div>
        `;
        qr_viewer.id = "qr_viewer";
        qr_viewer.classList.add("col-md-5");
        var container = createForm(fields);
        container.classList.add("col-md-7");
        container.classList.remove("w-75")

        row_container.appendChild(container);
        row_container.appendChild(qr_viewer);
    
        const content = document.getElementById("container_add_student");

        // Remove all existing HTML by clearing the innerHTML
        content.innerHTML = "";

        content.appendChild(row_container);
        populateForm(data, false, false, true, true, false);
    }

})