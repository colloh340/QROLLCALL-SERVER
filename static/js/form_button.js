function formButtons() {
    // Define button properties
    const buttons = [
        {
            class: "btn btn-danger d-flex align-items-center justify-content-center gap-2 fw-bold py-2",
            type: "button",
            text: "Clear",
            imgSrc: "/static/img/x.svg",
            col: "col-sm-12 col-md-6"
        },
        {
            class: "btn btn-primary d-flex align-items-center justify-content-center gap-2 fw-bold py-2",
            type: "submit",
            text: "Submit",
            imgSrc: "/static/img/ic_upload.svg",
            col: "col-sm-12 col-md-6"
        }
    ];

    // Create a container for the buttons
    var buttonContainer = document.createElement("div");
    buttonContainer.className = "row g-3 mt-3 text-center"; // Adds spacing & centering

    buttons.forEach((button) => {
        // Create button wrapper
        const buttonDiv = document.createElement("div");
        buttonDiv.className = button.col; // Ensure proper column layout

        // Create button element
        const btn = document.createElement("button");
        btn.className = button.class;
        btn.type = button.type;

        // Create image element
        const img = document.createElement("img");
        img.src = button.imgSrc;
        img.width = 20;
        img.height = 20;
        
        // Append image and text to button
        btn.appendChild(img);
        btn.appendChild(document.createTextNode(button.text));

        // Append button to div
        buttonDiv.appendChild(btn);

        // Append div to container
        buttonContainer.appendChild(buttonDiv);
    });

    return buttonContainer;
}
