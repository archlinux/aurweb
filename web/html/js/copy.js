document.addEventListener('DOMContentLoaded', function() {
	document.querySelector('.copy').addEventListener('click', function(e) {
		e.preventDefault();
		navigator.clipboard.writeText(event.target.text);
	});
});
