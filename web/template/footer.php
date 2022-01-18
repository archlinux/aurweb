
			<!-- End of main content -->

			<div id="footer">
				<?php if ($ver): ?>
				<p>aurweb <a href="https://gitlab.archlinux.org/archlinux/aurweb/-/tree/<?= htmlspecialchars($ver, ENT_QUOTES) ?>"><?= htmlspecialchars($ver) ?></a></p>
				<?php endif; ?>
				<p><?= __('Copyright %s 2004-%d aurweb Development Team.', '&copy;', date('Y')) ?></p>
				<p><?= __('AUR packages are user produced content. Any use of the provided files is at your own risk.') ?></p>
			</div>
		</div>
	</body>
</html>
