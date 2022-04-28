

function showMsgs(data) {
    /*
        <div class="box">
            <div class="content">hello</div>
            <div class="img">
                <img src="https://do7al7xnsrd3m.cloudfront.net/notion-avatar-1633667244492.png">
            </div>
        </div>
        <hr>
    */
    const contents = document.querySelector("#contents");
    contents.innerHTML = '';
    for (const msg of data) {
        const box = document.createElement("div");
        box.classList.add("box");

        const content = document.createElement("div");
        content.classList.add("content");
        content.innerText = msg[0];

        const img = document.createElement("div");
        img.classList.add("img");
        const imgImg = document.createElement("img");
        imgImg.src = msg[1];

        const hr = document.createElement("hr");

        img.appendChild(imgImg);
        box.appendChild(content);
        box.appendChild(img);
        contents.appendChild(box);
        contents.appendChild(hr);
    }
}


function insertNewMsg(data) {
    const msg = data[0];
    const contents = document.querySelector("#contents");
    const msgBox = `
    <div class="box">
        <div class="content">${msg[0]}</div>
        <div class="img">
            <img src=${msg[1]}>
        </div>
    </div>
    <hr>
    `
    contents.innerHTML = msgBox + contents.innerHTML;
}


const submit = document.querySelector("#submit");
submit.addEventListener("click", function(e) {
    e.preventDefault();
    const url = "/api/submitNshow";

    const formData = new FormData();
    const fileField = document.querySelector("#file");
    const content = document.querySelector("#content");

    if (!content.value) {
        content.classList.add("alert");
        content.placeholder = "此處為必填";
    } else {
        content.classList.remove("alert");
        content.placeholder = '';
    }
    if (!fileField.value) {
        fileField.classList.add("alert");
    } else {
        fileField.classList.remove("alert");
    }

    if (content.value && fileField.value) {
        formData.append("content", content.value);
        formData.append("file", fileField.files[0]);

        fetch(url, {
            method: "POST",
            body: formData
        }).then(response => response.json()
        ).then(dataJson => {
            data = dataJson.data;
            insertNewMsg(data);
            content.value = '';
            fileField.value = '';
        }).catch(err => {
            alert(err);
        });
    }    
});

document.addEventListener("DOMContentLoaded", function() {
    const url = "/api/getNshow";
    fetch(url).then(response => response.json()
    ).then(dataJson => {
        data = dataJson.data;
        if (data) {
            showMsgs(data);
        }
    });
});