document.addEventListener("DOMContentLoaded", () => {
    const images = [
        "/static/images/img1.jpg",
        "/static/images/img2.jpg",
        "/static/images/img3.jpg"
    ];

    let currentIndex = 0;
    let votes = []; 
    let selectedRating = 0;

    const voteImage = document.getElementById("voteImage");
    const confirmButton = document.getElementById("confirmButton");
    const statusText = document.getElementById("statusText");
    const ratingButtons = document.querySelectorAll(".star-button");
    const USERNAME = document.querySelector(".vote-container").dataset.username;
    const buttonsContainer = document.querySelector(".buttons-container");

    let restartBtn = document.createElement("button");
    restartBtn.id = "restartButton";
    restartBtn.textContent = "Заново";
    restartBtn.className = "confirm-button";
    restartBtn.style.display = "none";
    buttonsContainer.appendChild(restartBtn);

    restartBtn.addEventListener("click", () => {
        currentIndex = 0;
        votes = [];
        selectedRating = 0;

        ratingButtons.forEach(b => b.classList.remove("selected", "hover"));

        loadImage(currentIndex);
    });

    function loadImage(index) {
        if (index < images.length) {
            voteImage.style.display = "block";
            document.querySelector(".rating-buttons").style.display = "flex";
            voteImage.src = images[index];
            selectedRating = 0;
            confirmButton.disabled = true;
            confirmButton.textContent = "Далее";
            statusText.textContent = `Картинка ${index + 1} из ${images.length}`;
            restartBtn.style.display = "none";
            ratingButtons.forEach(b => b.classList.remove("selected", "hover"));
        } else {
            voteImage.style.display = "none";
            document.querySelector(".rating-buttons").style.display = "none";
            confirmButton.textContent = "Сохранить";
            confirmButton.disabled = false;
            statusText.textContent = " ";
            restartBtn.style.display = "inline-block";
        }
    }

    ratingButtons.forEach((btn, index) => {
        btn.addEventListener("mouseenter", () => {
            ratingButtons.forEach((b, i) => {
                if (i <= index) {
                    b.classList.add("hover");
                } else {
                    b.classList.remove("hover");
                }
            });
        });

        btn.addEventListener("mouseleave", () => {
            ratingButtons.forEach((b, i) => {
                b.classList.remove("hover");
                if (i < selectedRating) {
                    b.classList.add("selected");
                }
            });
        });

        btn.addEventListener("click", () => {
            selectedRating = index + 1;
            ratingButtons.forEach((b, i) => {
                if (i < selectedRating) {
                    b.classList.add("selected");
                } else {
                    b.classList.remove("selected");
                }
            });
            confirmButton.disabled = false;
        });
    });


    confirmButton.addEventListener("click", async () => {
        if (currentIndex < images.length) {
            votes.push({ image: images[currentIndex], rating: selectedRating });
            currentIndex++;
            loadImage(currentIndex);
        } else {
            const payload = {
                username: USERNAME,
                created_at: new Date().toISOString(),
                votes: votes
            };

            const formData = new FormData();
            formData.append("payload", JSON.stringify(payload));

            const response = await fetch("/vote/submit", {
                method: "POST",
                body: formData
            });
            const data = await response.json();
            console.log(data);

            statusText.textContent = "Сохранено";

            confirmButton.style.display = "none";
            restartBtn.style.display = "none"; 

            let resultsBtn = document.createElement("button");
            resultsBtn.textContent = "Посмотреть результаты";
            resultsBtn.className = "vote-link";
            resultsBtn.addEventListener("click", () => {
                window.location.href = "/vote/results"; 
            });
            buttonsContainer.appendChild(resultsBtn);
        }
    });

    loadImage(currentIndex);
});
