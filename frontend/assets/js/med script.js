function expandCard(button) {
    const card = button.parentElement;

    if (!card.classList.contains("expanded")) {
        card.classList.add("expanded");
        card.querySelector(".card-image").style.display = "none";
        card.querySelector(".learn-more").style.display = "none";
        card.querySelector(".description").style.display = "block";
    } else {
        resetCard(card);
    }
}

function resetCard(card) {
    card.classList.remove("expanded");
    card.querySelector(".card-image").style.display = "block";
    card.querySelector(".learn-more").style.display = "block";
    card.querySelector(".description").style.display = "none";
}
document.addEventListener('DOMContentLoaded', function() {
    const buttons = document.querySelectorAll('.card-button');
    
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            const card = button.closest('.card');
            const description = card.querySelector('.card-description');
            description.classList.toggle('active');
        });
    });
});
