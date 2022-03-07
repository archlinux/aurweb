document.addEventListener('DOMContentLoaded', function() {
	document.querySelectorAll('.copy').addEventListener('click', function(e) {
		e.preventDefault();
		navigator.clipboard.writeText(e.target.text);
	});
});
