<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

html_header( __("Page Not Found") );
?>

<div id="error-page" class="box 404">
	<h2>404 - <?= __("Page Not Found") ?></h2>
	<p><?= __("Sorry, the page you've requested does not exist.") ?></p>
</div>

<?php
html_footer(AUR_VERSION);
