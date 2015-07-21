
			<!-- End of main content -->

			<div id="footer">
				<?php if ($ver): ?>
				<p>aurweb <a href="https://projects.archlinux.org/aurweb.git/log/?h=<?= htmlspecialchars($ver, ENT_QUOTES) ?>"><?= htmlspecialchars($ver) ?></a></p>
				<?php endif; ?>
				<p>Copyright &copy; 2004-<?= date("Y") ?> aurweb Development Team.</p>
				<p><?= __('AUR packages are user produced content. Any use of the provided files is at your own risk.') ?></p>
			</div>
		</div>
	</body>
</html>
