function showHideMergeSection() {
    const elem = document.getElementById('id_type');
    const merge_section = document.getElementById('merge_section');
    if (elem.value == 'merge') {
        merge_section.style.display = '';
    } else {
        merge_section.style.display = 'none';
    }
}

function showHideRequestHints() {
    document.getElementById('deletion_hint').style.display = 'none';
    document.getElementById('merge_hint').style.display = 'none';
    document.getElementById('orphan_hint').style.display = 'none';

    const elem = document.getElementById('id_type');
    document.getElementById(elem.value + '_hint').style.display = '';
}

document.addEventListener('DOMContentLoaded', function() {
    showHideMergeSection();
    showHideRequestHints();

    const input = document.getElementById('id_merge_into');
    const form = document.getElementById('request-form');
    const type = "suggest-pkgbase";

    typeahead.init(type, input, form, false);
});

// Bind the change event here, otherwise we have to inline javascript,
// which angers CSP (Content Security Policy).
document.getElementById("id_type").addEventListener("change", function() {
    showHideMergeSection();
    showHideRequestHints();
});
