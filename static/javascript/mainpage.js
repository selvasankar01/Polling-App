

function body_alignment(){
    let navbar_height = document.querySelector('#navbar').scrollHeight;
    let margin_top = document.querySelector('#other-than-navbar');
    margin_top.style.marginTop = navbar_height;
    console.log(navbar_height);
}


window.onload = () => {
    body_alignment();
};