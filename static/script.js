document.addEventListener("DOMContentLoaded", () => {
    let more = document.querySelectorAll('.show-more');
    
    document.querySelectorAll('.event').forEach((event,i ) => {
        event.onclick = () => {
            // toggle between showing
            if (more[i].style.display === 'table-row') {
                more[i].style.display = 'none'; 
            } else {
                more[i].style.display = 'table-row';
            }
        }
    });
});