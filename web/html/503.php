<?php

set_include_path(get_include_path() . PATH_SEPARATOR . '../lib');

html_header( __("Service Unavailable") );
?>

<div id="error-page" class="box 503">
	<h2>503 - <?= __("Service Unavailable") ?></h2>
	<p><?= __("Don't panic! This site is down due to maintenance. We will be back soon.") ?></p>
</div>

<?php
html_footer(AURWEB_VERSION);
