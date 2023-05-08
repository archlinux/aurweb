document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('id_filter_pkg_name');
    const form = document.getElementById('todolist_filter');
    const type = 'suggest-pkgbase';
    typeahead.init(type, input, form);
});
