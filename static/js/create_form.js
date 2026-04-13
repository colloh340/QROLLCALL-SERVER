const alert = document.createElement("div");

function createForm(fields) {
    const container = document.createElement("div");
    container.className = "m-auto";

    const form = document.createElement("form");
    form.className = "row g-3";
    form.id = "main_form";
    form.method = "POST";

    // Alert Message for Form
    alert.className = "alert col-md-12 text-center";
    alert.setAttribute("role", "alert");
    form.appendChild(alert);

    fields.forEach((field) => {
        form.appendChild(createFormField(field));
    });

    form.appendChild(formButtons());
    container.appendChild(form);

    $(form).submit(handleFormSubmit);

    return container;
}

/**
 * Creates a form field based on the given specifications.
 */
function createFormField(field) {
    const fieldDiv = document.createElement("div");

    if (field.type !== "hidden") {
        fieldDiv.className = field.col;
    }

    const label = document.createElement("label");
    if (field.type !== "hidden") {
        label.className = "form-label";
        label.htmlFor = field.id;
        label.textContent = field.label;
    }

    let input;
    switch (field.type) {
        case "select":
            input = createSelectField(field);
            break;
        case "textarea":
            input = document.createElement("textarea");
            input.className = "form-control";
            input.placeholder = field.placeholder;
            input.style.height = "100px";
            break;
        case "date":
        case "time":
            input = createDateTimeField(field);
            break;
        case "hidden":
            input = document.createElement("input");
            input.type = "hidden";
            input.value = field.value;
            break;
        default:
            input = document.createElement("input");
            input.type = field.type;
            input.className = "form-control";
            if (field.placeholder) {
                input.placeholder = field.placeholder;
            }
            break;
    }

    input.id = field.id;
    input.name = field.id;

    fieldDiv.appendChild(label);
    fieldDiv.appendChild(input);

    return fieldDiv;
}

/**
 * Creates a select field with options.
 */
function createSelectField(field) {
    const select = document.createElement("select");
    select.className = "form-select form-control select2";
    select.style.padding = "20px 20px";

    field.options.forEach((optionText) => {
        const option = document.createElement("option");
        option.textContent = optionText;
        option.value = optionText.toLowerCase().replace(/\s+/g, "-");
        if (optionText === "Choose...") option.selected = true;
        select.appendChild(option);
    });

    $(document).ready(function () {
        const dropdownConfig = {
            placeholder: "Search for an option",
            allowClear: true,
            width: "100%",
        };

        if (field.dropdown) {
            dropdownConfig.dropdownParent = $(`#${field.dropdown}`);
        }

        $(`#${field.id}`).select2(dropdownConfig);
    });

    return select;
}

/**
 * Creates a date or time input with proper constraints.
 */
function createDateTimeField(field) {
    const input = document.createElement("input");
    input.className = "form-control";
    input.type = field.type;

    if (field.type === "date") {
        input.setAttribute("min", new Date().toISOString().split("T")[0]); // Today’s date
    } else if (field.type === "time") {
        const now = new Date();
        let hours = now.getHours();
        let minutes = String(now.getMinutes()).padStart(2, "0");

        // Define min and max time
        const minTime = "07:00"; // 7 AM
        const maxTime = "19:00"; // 7 PM

        // Ensure the min time is at least 7 AM
        if (hours < 7) {
            hours = "07";
            minutes = "00";
        } else {
            hours = String(hours).padStart(2, "0");
        }

        const currentTime = `${hours}:${minutes}`;

        input.setAttribute("min", minTime);
        input.setAttribute("max", maxTime);

    }
    

    return input;
}

/**
 * Handles form submission, validating input and determining API endpoint.
 */
function handleFormSubmit(event) {
    event.preventDefault();

    const operationType = $("#operation-type").val();
    const formData = new FormData(event.target);
    let url = null;
    let isValid = false;

    const operations = {
        add_school: { url: "/schools/add", validator: isValidSchool },
        add_department: { url: "/department/add", validator: isValidDepartment },
        add_course: { url: "/course/add", validator: isValidCourse },
        add_student: { url: "/students/add", validator: () => isValidStudentStaff(true) },
        add_unit: { url: "/units/add", validator: isValidUnit },
        add_staff: { url: "/lecturer/add", validator: () => isValidStudentStaff(false) },
        schedule_attendance: { url: "/attendance/schedule", validator: isValidAttendance },
    };

    if (operationType in operations) {
        url = operations[operationType].url;
        isValid = operations[operationType].validator();
    }

    if (url && isValid) {
        submitData(operationType, url, formData);
    } else {
        console.error("Invalid URL or validation failed: " + url);
    }
}


async function submitData(operation_type, url, formData) {
    try {
        $('#modal-loading').modal('show'); // Show loading modal
        
        const response = await fetch(url, {
            method: "POST",
            body: formData,
            headers: {
                "X-CSRFToken": $("input[name='csrfmiddlewaretoken']").val(),
                'Client': 'qrollcall.com'
            }
        });

        const data = await response.json();
        
        // Show alert & toast notification
        const message = data.message;
        const status = data.status;
        showAlert(message, status === 200 || status === 201 ? 1 : 0);
        createToast(message, status);

        // Handle attendance QR generation
        if (operation_type === "schedule_attendance" && (status === 200 || status === 201)) {
            const img_data = data.response.img_data;
            const attendance = data.response.attendance_id;
            $("#qr_div").html(`
                <img src="data:image/png;base64, ${img_data}" alt="QR Code" class="img-fluid rounded" style="max-width: 100%; height: auto;">
            `);
            document.getElementById("btn_export_wrapper").classList.remove("d-none");
            document.getElementById("btn_download_pdf").href = `/attendance/report?attendance=${attendance}&get=qr&type=pdf`;
            document.getElementById("btn_download_image").href = `/attendance/report?attendance=${attendance}&get=qr`;
        }

        // Reset form on success
        if (status === 200 || status === 201) {
            document.getElementById("main_form").reset();
        }
        if(data.redirect_url != null && data.redirect_url.length > 0){
            window.location.href = data.redirect_url;
        }
        
    } catch (error) {
        console.error(`Submission error: ${error}`);
        showAlert("An error occurred!", 0);
    } finally {
        $('#modal-loading').modal('hide'); // Ensure modal is always hidden
    }
}
function isValidStudentStaff(student = true) {
    var first_name = $("#input-first-name").val().trim();
    var last_name = $("#input-last-name").val().trim();
    var email = $("#input-email").val().trim();
    var department_id = $("#input-department").val();
    email = email.trim();
    console.log("Validating email:", email);


    if (first_name.length < 3 || first_name.length > 30) {
        showAlert("First name should be between 3 to 30 characters.", 0);
        return false;
    }
    if (!/^[A-Za-z]+$/.test(first_name)) {
        showAlert("First name should not contain numbers or special characters.", 0);
        return false;
    }
    
    if (last_name.length < 3 || last_name.length > 30) {
        showAlert("Last name should be between 3 to 30 characters.", 0);
        return false;
    }
    if (!/^[A-Za-z]+$/.test(last_name)) {
        showAlert("Last name should not contain numbers or special characters.", 0);
        return false;
    }
    
    if (email.length === 0 || email.length > 50) {
        showAlert("Email should not be empty and must be less than 50 characters.", 0);
        return false;
    }
    if (department_id.length === 0) {
        showAlert("Select department", 0);
        return false;
    }

    if (!student) {
        var password = $("#password").val();
        var password2 = $("#password2").val();
        if (password.length < 6) {
            showAlert("Password too short.", 0);
            return false;
        } else if (password !== password2) {
            showAlert("Passwords do not match.", 0);
            return false;
        }

        // var staffEmailRegex =/^(?!\.)[A-Za-z0-9]+(\.[A-Za-z0-9]+)?@staff\.jooust\.ac\.ke$/;
        var staffEmailRegex = /^[A-Za-z0-9]+(\.[A-Za-z0-9]+)*@staff\.jooust\.ac\.ke$/;

        if (!staffEmailRegex.test(email)) {
            showAlert("Invalid staff email format. It should be in the format: name@staff.jooust.ac.ke (1-15 characters, letters/numbers, only one dot allowed, cannot start or end with a dot).", 0);
            return false;
        }


    }

    if (student) {
        var course_id = $("#input-course").val();
        if (course_id.length === 0) {
            showAlert("Select course", 0);
            return false;
        }

        var registration_number = $("#input-reg-no").val().trim();
        var regEx = /^[A-Za-z]\d{3}\/[A-Za-z]\/\d{4}\/\d{2}$/;

        if (!regEx.test(registration_number)) {
            showAlert("Invalid registration number format. It should be in the format I231/G/1234/22.", 0);
            return false;
        }

        // Validate the trailing 2-digit year in the registration number.
        var year = parseInt(registration_number.split('/')[3], 10);
        var currentYear = new Date().getFullYear() % 100;
        if (year < 0 || year > currentYear) {
            showAlert("Invalid year in registration number.", 0);
            return false;
        }

        // Student email validation: must contain at least one letter and one number
        var studentEmailRegex = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z0-9]+@students\.jooust\.ac\.ke$/;
        if (!studentEmailRegex.test(email)) {
            showAlert("Invalid student email format. It should be in the format: abc456@students.jooust.ac.ke.", 0);
            return false;
        }
    }

    return true;
}



function isValidUnit(){
    var unit_code = $("#input-unit-code").val().trim();
    var unit_name = $("#input-unit-name").val().trim();
    var semester = $("#input-semester").val().trim();
    var department_id = $("#input-department").val().trim();

    // Regex: exactly 3 uppercase letters followed by 4 digits (e.g., ITB1400, ICB3102)
    var unitCodeRegex = /^[A-Z]{3}\d{4}$/;

    if (!unitCodeRegex.test(unit_code)) {
        showAlert("Invalid unit code format. It should be 3 uppercase letters followed by 4 digits (e.g., ITB1400, ICB3102).", 0);
        return false;
    }

    if (unit_name.length < 5 || unit_name.length > 80) {
        showAlert("Unit name should be between 5 and 80 characters.", 0);
        return false;
    }

    if (department_id.length === 0) {
        showAlert("Select department.", 0);
        return false;
    }

    if (semester.length === 0) {
        showAlert("Select semester.", 0);
        return false;
    }

    return true;
}
function isValidAttendance() {
    var course = $("#input-course").val();
    var date = $("#input-date").val();
    var unit_code = $("#input-unit").val();
    var start_time = $("#input-start-time").val();
    var end_time = $("#input-end-time").val();

    if (course.length === 0) {
        showAlert("Select course.", 0);
        return false;
    }
    if (unit_code.length === 0) {
        showAlert("Select unit.", 0);
        return false;
    }
    if (date.length === 0) {
        showAlert("Select date.", 0);
        return false;
    }
    if (start_time.length === 0) {
        showAlert("Select start time.", 0);
        return false;
    }
    if (end_time.length === 0) {
        showAlert("Input end time.", 0);
        return false;
    }

    // Get today's date in YYYY-MM-DD format
    var today = new Date();
    var todayStr = today.toISOString().split("T")[0];

    // Ensure the date is today or a future date
    if (date < todayStr) {
        showAlert("Date cannot be in the past.", 0);
        return false;
    }

    // Convert times to Date objects for comparison
    var startTime = new Date(`2024-01-01T${start_time}`);
    var endTime = new Date(`2024-01-01T${end_time}`);
    
    var minStartTime = new Date(`2024-01-01T07:00`); // 7:00 AM
    var maxStartTime = new Date(`2024-01-01T19:00`); // 7:00 PM
    var maxEndTime = new Date(`2024-01-01T20:00`); // 8:00 PM

    // If date is today, start time must not be before the current time
    var currentTime = new Date();
    var currentHours = currentTime.getHours();
    var currentMinutes = currentTime.getMinutes();
    var currentFormattedTime = new Date(`2024-01-01T${String(currentHours).padStart(2, "0")}:${String(currentMinutes).padStart(2, "0")}`);

    if (date === todayStr && startTime < currentFormattedTime) {
        showAlert("Start time cannot be in the past for today's date.", 0);
        return false;
    }

    // If date is not today, start time must not be less than 7:00 AM
    if (date !== todayStr && startTime < minStartTime) {
        showAlert("Start time must be 7:00 AM or later.", 0);
        return false;
    }

    // Ensure start time is within 7 AM - 7 PM
    if (startTime > maxStartTime) {
        showAlert("Start time must be between 7:00 AM and 7:00 PM.", 0);
        return false;
    }

    // Ensure end time is at least 10 minutes after start time and within the allowed range
    var minEndTime = new Date(startTime.getTime() + 10 * 60000); // 10 minutes after start time

    if (endTime < minEndTime) {
        showAlert("End time must be at least 10 minutes after start time.", 0);
        return false;
    }
    if (endTime > maxEndTime) {
        showAlert("End time cannot be later than 8:00 PM.", 0);
        return false;
    }

    // **Ensure class duration is not more than 3 hours**
    var maxDuration = 3 * 60 * 60 * 1000; // 3 hours in milliseconds
    if ((endTime.getTime() - startTime.getTime()) > maxDuration) {
        showAlert("Class duration cannot exceed 3 hours.", 0);
        return false;
    }

    return true;
}



function isValidSchool() {
    var school_name = $("#input-school-name").val();
    var school_description = $("#input-school-description").val();

    // Check if school name is valid
    if(school_name.length < 5 || school_name.length > 50) {
        showAlert("School name should be less than 50 characters.", 0);
        return false;
    }

    // Check if school description is valid
    if(school_description.length > 250) {
        showAlert("School description too long", 0);
        return false;
    }

    // If all checks pass, return true
    return true;
}
function isValidDepartment(){
    var department_name = $("#input-department-name").val();
    // var department_id = $("#input-department-id").val();
    var description = $("#input-department-description").val();
    var school = $("#input-school").val()


    if(department_name.length < 5 || department_name.length > 50) {
        showAlert("Department name should be between 5 and 50 letters.", 0);
        return false;
    }

    if(description.length > 250) {
        showAlert("Description too long", 0);
        return false;
    }
    if(school.length === 0){
        showAlert("Select school", 0);
        return false;
    }

    return true;
}
function isValidCourse(){
    var course_name = $("#input-course-name").val();
    var department = $("#input-department").val();

    if(course_name.length < 5 || course_name.length > 50) {
        showAlert("Course name should be less than 50 characters.", 0);
        return false;
    }

    if(department.length === 0){
        showAlert("Select department", 0);
        return false;
    }
    // If all checks pass, return true
    return true;
}

function showAlert(message, value){
    if(value == 1){
        alert.classList.add("alert-success");
    }else{
        alert.classList.add("alert-danger");
    }
    alert.textContent = message;
    setTimeout(()=>{
        alert.textContent = "";
        if(value == 1){
            alert.classList.remove("alert-success");
        }else{
            alert.classList.remove("alert-danger");
        }
    }, 5000);
}


function populateForm(data, school = false,department =false,course =false, unit=false, instructor=false) {
    var schoolSelect;
    var departmentSelect;
    var courseSelect;
    var unitSelector;
    var instructorSelect
    if (school) {
        schoolSelect = document.getElementById("input-school");
        schoolSelect.innerHTML = `<option value="">Choose...</option>`;
    }
    if (department) {
        departmentSelect = document.getElementById("input-department");
        departmentSelect.innerHTML = `<option value="">Choose...</option>`;
    }
    if (course) {
        courseSelect = document.getElementById("input-course");
        courseSelect.innerHTML = `<option value="">Choose...</option>`;
    }
    if(unit){
        unitSelector = document.getElementById("input-unit");
        unitSelector.innerHTML = `<option value="">Choose...</option>`;
    }
    if(instructor){
        instructorSelect = document.getElementById("input-instructor");
        instructorSelect.innerHTML = `<option value="">Choose...</option>`;
    }


    // Populate the school dropdown
    if(school){
        data.forEach(schoolObj => {
            const option = document.createElement("option");
            option.value = schoolObj.school_id; // Use school ID as the value
            option.textContent = schoolObj.school; // Use school name as the text
            schoolSelect.appendChild(option);
        });
    }
    if(instructor){
        data.instructors.forEach(instructorObj => {
            const option = document.createElement("option");
            option.value = instructorObj.instructor_id;
            option.textContent = instructorObj.instructor_name;
            instructorSelect.appendChild(option);
        });
    }
    if(course && unit){
        // Populate the course dropdown
            data.course_unit.forEach(course_unit => {
                $("#input-course").append(
                    `<option value="${course_unit.course_code}">${course_unit.course}</option>`
                );
            });

            // Add change event listener to course dropdown
            $("#input-course").on("change", function () {
                const selectedCourseId = $(this).val(); // Get selected value
                console.log("Selected course: " + selectedCourseId);

                // Find the selected course
                const selectedCourse = data.course_unit.find(course => course.course_code === selectedCourseId);

                // Clear and populate units dropdown
                $("#input-unit").html('<option value="">Choose...</option>'); // Clear options
                if (selectedCourse) {
                    selectedCourse.units.forEach(c_unit => {
                        $("#input-unit").append(
                            `<option value="${c_unit.unit_code}">${c_unit.unit_code}</option>`
                        );
                    });
                }
            });

    }
    if(department && !school && !course){
        data.forEach(departmentObj => {
            const option = document.createElement("option");
            option.value = departmentObj.department_id;
            option.textContent = departmentObj.department;
            departmentSelect.appendChild(option);
        });
    }

    // Add event listener for the school select
    if(school && department){
        $(schoolSelect).on("change", function () {
        
            const selectedSchoolId = $(this).val();
        
            // Find the selected school
            const selectedSchool = data.find(school => school.school_id === selectedSchoolId);
        
            // Clear and populate departments
            departmentSelect.innerHTML = `<option value="">Choose...</option>`;
            if (course)
                courseSelect.innerHTML = `<option value="">Choose...</option>`; // Reset courses
            if (selectedSchool) {
                selectedSchool.departments.forEach(department => {
                    const option = document.createElement("option");
                    option.value = department.department_id; // Use department ID as the value
                    option.textContent = department.department; // Use department name as the text
                    departmentSelect.appendChild(option);
                });
            }
        });
        
    }
    

    // Add event listener for the department select
    if(school && department && course){
        $("#input-department").on("change", function () {
            const selectedDepartmentId = $(this).val(); // Get the selected value
        
            // Find the selected school and department
            const selectedSchool = data.find(school => 
                school.departments.some(dept => dept.department_id === selectedDepartmentId)
            );
        
            const selectedDepartment = selectedSchool 
                ? selectedSchool.departments.find(dept => dept.department_id === selectedDepartmentId)
                : null;
        
            // Clear and populate courses
            $("#input-course").html('<option value="">Choose...</option>'); // Clear options
            if (selectedDepartment) {
                selectedDepartment.courses.forEach(course => {
                    $("#input-course").append(
                        `<option value="${course.code}">${course.name}</option>` // Append new options
                    );
                });
            }
        });
        
    }
    
}
