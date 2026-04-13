$(document).ready(function(){

    function buildScheduleTable(data){
        // Create the table
        var table_wrapper = document.createElement("div");
        table_wrapper.style.padding = "15px";
        table_wrapper.id = "table_wrapper";
        table_wrapper.className = "table-responsive-md";

        var unit_table = document.createElement("table");
        
        unit_table.classList.add("table", "table-striped", "table-hover", "caption-top");
        // Table head
        var table_head = document.createElement("thead");
        var tr_head = document.createElement("tr");
        ["#", "Unit Code", "Name", "Action"].forEach((value) => {
            var th = document.createElement("th");
            th.setAttribute("scope", "col");
            th.textContent = value;
            tr_head.appendChild(th);
        });

        table_head.appendChild(tr_head);

        var caption = document.createElement("caption");
        const today_date = new Date().toLocaleDateString();
        caption.textContent = `Date : ${today_date}`;
        unit_table.appendChild(caption);

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
            
                // Action Button
                var td_btn = document.createElement("td");
                var action = document.createElement("button");
                action.className = "btn btn-secondary";
                action.setAttribute("type", "button");
                action.setAttribute("data-bs-toggle", "popover");
                action.setAttribute("data-bs-placement", "left");
                action.setAttribute("data-bs-trigger", "focus");
                action.setAttribute("data-bs-html", "true"); // Important to render HTML
            
                action.innerHTML = '<i class="fa-solid fa-ellipsis-vertical"></i>';
                
                td_btn.appendChild(action);
            
                // Set popover content
                action.setAttribute("data-bs-content", `
                    <button class="btn btn-primary btn-sm" onclick="viewItem()">View</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteItem()">Delete</button>
                `);
            
                // Append all columns to the row
                tr.appendChild(th);
                tr.appendChild(td_code);
                tr.appendChild(td_name);
                tr.appendChild(td_btn);
            
                // Append the row to the table body
                tr.onclick = function() {
                    showUnitModal({
                        unit_code: courseUnit[i].unit_code || "N/A",
                        unit_name: courseUnit[i].unit_name || "N/A",
                        course: courseUnit[i].course   || "N/A",
                        lecturer_name: courseUnit[i].lecturer_name || "N/A",
                        lecturer_email: courseUnit[i].lecturer_email || "N/A",
                        date: courseUnit[i].date || "N/A",
                        start_time: courseUnit[i].start_time || "N/A",
                        end_time: courseUnit[i].end_time || "N/A",
                        students: courseUnit[i].students || []
                    });
                };
                table_body.appendChild(tr);
            }

            // Ensure popovers are initialized after elements are added to the DOM
            setTimeout(() => {
                var popovers = document.querySelectorAll('[data-bs-toggle="popover"]');
                popovers.forEach(popover => new bootstrap.Popover(popover));
            }, 100); // Small delay ensures elements exist before initialization


            var table_container  = document.createElement("div");
            table_container.className = "table-responsive-md";
            unit_table.appendChild(table_body);
            table_container.appendChild(unit_table);
            table_wrapper.append(table_container); // Append the table
        } else {
            table_wrapper.style.textAlign = "center";
            table_wrapper.style.padding = "20px";
            table_wrapper.style.fontSize = "1.5rem";
            table_wrapper.innerHTML = "No schedules available";
        }
        return table_wrapper;
    }

    // Example functions for button actions
    function viewItem() {
        alert("View button clicked!");
    }

    function deleteItem() {
        alert("Delete button clicked!");
    }

    function showUnitModal(data){
        const existingModal = document.getElementById("unitModal");
        if (existingModal) {
            existingModal.remove();
        }
        const modal = document.createElement("div");
        modal.className = "modal fade";
        const modal_dialog = document.createElement("div");
        modal_dialog.className = "modal-dialog modal-fullscreen-sm-down";
        modal.id = "unitModal";
        modal.tabIndex = "-1";
        modal.setAttribute("aria-labelledby", "unitModalLabel");
        modal.setAttribute("aria-hidden", "true");
        modal_dialog.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="unitModalLabel">${data.unit_code} Attendance</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="">Unit name: ${data.unit_name}</div>
                        <div class="">Unit code: ${data.unit_code}</div>
                        <div class="">Course: ${data.course}</div>
                        <div class="">Lecturer
                            <div class="">Name: ${data.lecturer_name}</div>
                            <div class="">Email: ${data.lecturer_email}</div>
                        </div>
                        <div class="">Date: ${data.date}</div>
                        <div class="">Time: ${data.start_time} - ${data.end_time}</div>
                        <div class="table_wrapper" id="table_wrapper_students">
                            ${buildStudentTable(data.students)}
                        </div>
                    </div>
                </div>
            `;
            // Append modal dialog to modal
            modal.appendChild(modal_dialog);

            // Append modal to body
            document.body.appendChild(modal);

            // Initialize and show the modal
            const modalInstance = new bootstrap.Modal(modal);
            modalInstance.show();
    }
    function buildStudentTable(data){
        // Create the table
        var table_wrapper = document.createElement("div");
        table_wrapper.style.padding = "15px";
        table_wrapper.id = "table_wrapper";
        table_wrapper.className = "table-responsive-md";

        var unit_table = document.createElement("table");
        
        unit_table.classList.add("table", "table-striped", "table-hover", "caption-top");
        // Table head
        var table_head = document.createElement("thead");
        var tr_head = document.createElement("tr");
        ["#", "Name", "Reg No", "Action"].forEach((value) => {
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
            
                // Student Name
                var td_name = document.createElement("td");
                td_name.textContent = courseUnit[i].student_name;
            
                // Student Reg No
                var td_reg_no = document.createElement("td");
                td_reg_no.textContent = courseUnit[i].reg_no;
            
                // Action Button
                var td_btn = document.createElement("td");
                var action = document.createElement("button");
                action.className = "btn btn-secondary";
                action.setAttribute("type", "button");
                action.setAttribute("data-bs-toggle", "popover");
                action.setAttribute("data-bs-placement", "left");
                action.setAttribute("data-bs-trigger", "focus");
                action.setAttribute("data-bs-html", "true"); // Important to render HTML
            
                action.innerHTML = '<i class="fa-solid fa-ellipsis-vertical"></i>';
                
                td_btn.appendChild(action);
            
                // Set popover content
                action.setAttribute("data-bs-content", `
                    <button class="btn btn-primary btn-sm" onclick="viewItem()">View</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteItem()">Delete</button>
                `);
                // Append all columns to the row
                tr.appendChild(th);
                tr.appendChild(td_name);
                tr.appendChild(td_reg_no);
                tr.appendChild(td_btn);
            
                // Append the row to the table body
                tr.onclick = function() {
                    console.log("Row clicked!");
                };
                table_body.appendChild(tr);
            }
            unit_table.appendChild(table_body);
            table_wrapper.appendChild(unit_table);
        } else {
            table_wrapper.style.textAlign = "center";
            table_wrapper.style.padding = "20px";
            table_wrapper.style.fontSize = "1.5rem";
            table_wrapper.innerHTML = "No students are available.";
        }
        return table_wrapper.innerHTML;
    }
});