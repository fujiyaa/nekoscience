document.addEventListener("DOMContentLoaded", () => {
    const container = document.querySelector(".results-container");
    const blocks = Array.from(container.querySelectorAll(".result-block"));

    blocks.sort((a, b) => {
        const aRating = parseFloat(a.querySelector(".rating-text").textContent);
        const bRating = parseFloat(b.querySelector(".rating-text").textContent);
        return bRating - aRating;
    });

    container.innerHTML = "";
    blocks.forEach(block => container.appendChild(block));
});