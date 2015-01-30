
			<!-- End of main content -->

			<div id="footer">
				<?php if ($ver): ?>
				<p>aurweb <?= htmlspecialchars($ver) ?></p>
				<?php endif; ?>
				<p>Copyright &copy; 2004-<?= date("Y") ?> aurweb Development Team.</p>
				<p><?= __('Unsupported packages are user produced content. Any use of the provided files is at your own risk.') ?></p>
			</div>
		</div>
	</body>
</html>
