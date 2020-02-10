var currentState = 0;
var maxState=10;
var svg;

function transitionToState(stateIndex, previousState) {
    if (stateIndex == 1 && previousState == 0){
        true_colour = svg.getElementById("true_colour");

        var animageFade = document.createElementNS('http://www.w3.org/2000/svg','animate');
        animageFade.setAttribute("attributeName","opacity");
        animageFade.setAttribute("begin","indefinite");
        animageFade.setAttribute("dur","5s");
        animageFade.setAttribute("values","1;0");
        animageFade.setAttribute("fill","freeze");
        true_colour.appendChild(animageFade)
        animageFade.beginElement()
    }
    console.log("Changing to state "+ stateIndex)
}


document.addEventListener("DOMContentLoaded", function(event) {
    svg = document.getElementById("vis");
    transitionToState(currentState, 0);
});

function nextState() {
    if (currentState < maxState){
        currentState++;
        transitionToState(currentState, currentState - 1)
    }
}

function previousState() {
    if (currentState > 0){
        currentState--;
        transitionToState(currentState, currentState + 1)
    }
}
