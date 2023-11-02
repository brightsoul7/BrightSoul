document.addEventListener("DOMContentLoaded", function() {
    let cards = document.querySelectorAll(".card");
    cards.forEach((card, index) => {
        let btn = card.querySelector("button");
        let modal = card.querySelector(".modal");
        let modalContent = card.querySelector(".modal-content");
        
        btn.addEventListener("click", function(event) {
            event.stopPropagation(); // Prevents the click event from propagating to the body
            modal.style.display = "flex";
            setTimeout(function() {
                modalContent.style.opacity = 1;
            }, 100);
        });
        
        modal.addEventListener("mouseleave", function() {
            modalContent.style.opacity = 0;
            setTimeout(function() {
                modal.style.display = "none";
            }, 500);
        });

        // Close the modal when clicking outside the modal content
        modal.addEventListener("click", function(event) {
            if (event.target === modal) {
                modalContent.style.opacity = 0;
                setTimeout(function() {
                    modal.style.display = "none";
                }, 500);
            }
        });
    });
});
