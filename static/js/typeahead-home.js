document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('pkgsearch-field');
    const form = document.getElementById('pkgsearch-form');
    const type = 'suggest';
    typeahead.init(type, input, form);
});
