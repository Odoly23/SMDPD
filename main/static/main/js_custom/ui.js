/* UX umum SMDPD: modal konfirmasaun, alerta otomátiku, botaun fila ba leten, proteje submit dala rua. */
$(function () {
	// 1) Konfirmasaun ho modal Bootstrap (form[data-confirm])
	var $modal = $('#modal-konfirma'), pendente = null;
	$(document).on('submit', 'form[data-confirm]', function (e) {
		if (this.dataset.konfirmadu === '1') { return; }
		e.preventDefault();
		pendente = this;
		$('#modal-konfirma-teks').text($(this).data('confirm'));
		$modal.modal('show');
	});
	$('#modal-konfirma-ok').on('click', function () {
		if (!pendente) { return; }
		pendente.dataset.konfirmadu = '1';
		$modal.modal('hide');
		if (pendente.requestSubmit) { pendente.requestSubmit(); } else { pendente.submit(); }
	});
	$modal.on('hidden.bs.modal', function () { pendente = null; });

	// 2) Alerta sai automátiku (la ba error)
	setTimeout(function () { $('.alerta-auto.alert-success, .alerta-auto.alert-info').alert('close'); }, 7000);

	// 3) Botaun fila ba leten
	var $top = $('#btn-sai-leten');
	$(window).on('scroll', function () { $top.toggleClass('hatudu', $(this).scrollTop() > 300); });
	$top.on('click', function () { $('html, body').animate({ scrollTop: 0 }, 250); });

	// 4) Proteje submit dala rua + indikadór loading
	$(document).on('submit', 'form[method=post], form[method=POST]', function (e) {
		if (e.isDefaultPrevented()) { return; }
		var $f = $(this);
		if ($f.data('submitted')) { e.preventDefault(); return; }
		$f.data('submitted', true);
		$f.find('button[type=submit]').each(function () {
			var $b = $(this);
			$b.prop('disabled', true).data('html', $b.html()).html('<i class="fa fa-spinner fa-spin"></i> ' + $.trim($b.text()));
		});
		setTimeout(function () { $f.data('submitted', false); $f.find('button[type=submit]').each(function () { $(this).prop('disabled', false).html($(this).data('html')); }); }, 15000);
	});
});
