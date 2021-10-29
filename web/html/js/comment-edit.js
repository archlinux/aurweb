function add_busy_indicator(sibling) {
    const img = document.createElement('img');
    img.src = "/images/ajax-loader.gif";
    img.classList.add('ajax-loader');
    img.style.height = 11;
    img.style.width = 16;
    img.alt = "Busy…";

    sibling.insertAdjacentElement('afterend', img);
}

function remove_busy_indicator(sibling) {
    const elem = sibling.nextElementSibling;
    elem.parentNode.removeChild(elem);
}

function getParentsUntil(elem, className) {
    // Limit to 10 depth
    for ( ; elem && elem !== document; elem = elem.parentNode) {
        if (elem.matches(className)) {
            break;
        }
    }

    return elem;
}

function handleEditCommentClick(event, pkgbasename) {
    event.preventDefault();
    const parent_element = getParentsUntil(event.target, '.comment-header');
    const parent_id = parent_element.id;
    const comment_id = parent_id.substr(parent_id.indexOf('-') + 1);
    // The div class="article-content" which contains the comment
    const edit_form = parent_element.nextElementSibling;

    const url = "/pkgbase/" + pkgbasename + "/comments/" + comment_id + "/form?";

    add_busy_indicator(event.target);

    fetch(url + new URLSearchParams({ next: window.location.pathname }), {
        method: 'GET',
        credentials: 'same-origin'
    })
    .then(function(response) {
        if (!response.ok) {
            throw Error(response.statusText);
        }
        return response.json();
    })
    .then(function(data) {
        remove_busy_indicator(event.target);
        edit_form.innerHTML = data.form;
        edit_form.querySelector('textarea').focus();
    })
    .catch(function(error) {
        remove_busy_indicator(event.target);
        console.error(error);
    });

    return false;
}
