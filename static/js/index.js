function onClick(element) {
    element.style.visibility = 'hidden';
    var img = document.createElement('div');
    img.setAttribute("class", "spinner-grow text-danger");
    img.setAttribute("role", "status");

    var text = document.createElement('h5');
    text.innerHTML = "Пожалуйста, подождите, идёт обработка данных";

    document.body.append(img);
    document.body.append(text);
    img.style = "position: absolute; left: 50%; top: 50%; visibility: visible";
    text.style = "position: absolute; left: 33%; top: 60%; visibility: visible;";
}