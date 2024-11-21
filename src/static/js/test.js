alert("TEST SCRIPT LOADED!");
console.log("TEST SCRIPT LOADED!");

// Test button click
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM LOADED!");
    alert("DOM LOADED!");
    
    // Create a test button
    const testButton = document.createElement('button');
    testButton.textContent = 'TEST BUTTON';
    testButton.style.position = 'fixed';
    testButton.style.top = '10px';
    testButton.style.right = '10px';
    testButton.style.zIndex = '9999';
    testButton.style.padding = '10px';
    testButton.style.backgroundColor = 'red';
    testButton.style.color = 'white';
    
    testButton.onclick = function() {
        console.log("BUTTON CLICKED!");
        alert("BUTTON CLICKED!");
    };
    
    document.body.appendChild(testButton);
});