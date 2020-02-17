var currentState = 0;
var maxState = 10;
var svg;
var isStateLocked = false;

var getJSON = function(url, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.responseType = 'json';
    xhr.onload = function() {
        var status = xhr.status;
        if (status === 200) {
            callback(null, xhr.response);
        } else {
            callback(status, xhr.response);
        }
    };
    xhr.send();
};

function getFadeElement(fadeOut, id = null) {
    var animateFade = document.createElementNS('http://www.w3.org/2000/svg', 'animate');
    animateFade.setAttribute("attributeName", "opacity");
    animateFade.setAttribute("begin", "indefinite");
    animateFade.setAttribute("dur", "5s");
    animateFade.setAttribute("values", fadeOut ? "1;0" : "0;1");
    animateFade.setAttribute("fill", "freeze");
    if (fadeOut) {
        animateFade.setAttribute("onend", "removeElement('" + id + "')");
    }
    return animateFade
}

function getImageElement(url, id) {
    image = document.createElementNS('http://www.w3.org/2000/svg', 'image');
    image.setAttribute("id", id)
    image.setAttribute("href", url)
    image.setAttribute("preserveAspectRatio", "xMidYMid meet")
    image.setAttribute("width", "100")
    image.setAttribute("height", "100")
    return image
}

function swapImagesBack() {
    trueColour = svg.getElementById("heightMap");
    fadeOut = getFadeElement(true, "heightMap")
    trueColour.appendChild(fadeOut)

    heightMap = getImageElement("img/true_colour_resized.jpg", "trueColour")
    fadeIn = getFadeElement(false)
    heightMap.appendChild(fadeIn)
    svg.appendChild(heightMap)

    fadeIn.beginElement()
    fadeOut.beginElement()
}

function swapImages() {
    trueColour = svg.getElementById("trueColour");
    fadeOut = getFadeElement(true, "trueColour")
    trueColour.appendChild(fadeOut)

    heightMap = getImageElement("img/height_map.png", "heightMap")
    fadeIn = getFadeElement(false)
    heightMap.appendChild(fadeIn)
    svg.appendChild(heightMap)

    fadeIn.beginElement()
    fadeOut.beginElement()
}

function transitionToState(stateIndex, previousState) {
    if (stateIndex == 1 && previousState == 0) {
        isStateLocked = true;
        swapImages()
    } else if (stateIndex == 0 && previousState == 1) {
        isStateLocked = true;
        swapImagesBack()
    } else if (stateIndex == 2 && previousState == 1) {
        console.log("Should clear image")
    } else if (stateIndex == 1 && previousState == 2) {
        console.log("Should add image")
    } else if (stateIndex == 3 && previousState == 2) {
        height = getJSON("http://localhost:5000/height/3000/3000/3010/3010", function(status, response) {
            console.log(response);
        });
    }
    console.log("Changing to state " + stateIndex)
}

function removeElement(elementId) {
    trueColour = svg.getElementById(elementId);
    svg.removeChild(trueColour);
    isStateLocked = false;
}

document.addEventListener("DOMContentLoaded", function(event) {
    svg = document.getElementById("vis");
    transitionToState(currentState, 0);
});

function nextState() {
    if (currentState < maxState && !isStateLocked) {
        currentState++;
        transitionToState(currentState, currentState - 1)
    }
}

function previousState() {
    if (currentState > 0 && !isStateLocked) {
        currentState--;
        transitionToState(currentState, currentState + 1)
    }
}