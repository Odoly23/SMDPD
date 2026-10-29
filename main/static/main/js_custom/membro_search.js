/* Pesquiza membru (naran ka nu. eleitoral) ba form aloka pozisaun. */
$(function () {
	var $input = $('#cari-membro');
	if (!$input.length) { return; }
	var url = $input.closest('form').data('membro-url');
	var timer = null;
	$input.on('keyup', function () {
		clearTimeout(timer);
		var q = $.trim($(this).val());
		timer = setTimeout(function () {
			if (q.length < 2) { return; }
			$.ajax({ url: url, data: { q: q }, success: function (html) { $('#id_membro').html(html); } });
		}, 300);
	});
});
