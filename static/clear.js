document.addEventListener("DOMContentLoaded", () => {
    let clear = document.querySelectorAll('.clear');
    //console.log(clear)
    
    document.querySelectorAll('.close').forEach((event, i ) => {
        event.onclick = () => {
            //console.log(clear[i]);
            clear[i].value = '';
        }
    });
});