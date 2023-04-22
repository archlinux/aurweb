document.addEventListener('DOMContentLoaded', function() {
	const input = document.getElementById('merge_into');
	const form = document.getElementById('merge-form');
	const type = "suggest-pkgbase";
	typeahead.init(type, input, form, false);
});
