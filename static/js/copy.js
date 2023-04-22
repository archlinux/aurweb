document.addEventListener('DOMContentLoaded', function() {
    let elements = document.querySelectorAll('.copy');
    elements.forEach(function(el) {
        el.addEventListener('click', function(e) {
            e.preventDefault();
            navigator.clipboard.writeText(e.target.text);
        });
    });
});
