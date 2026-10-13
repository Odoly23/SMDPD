/* Dropdown berantai Munisipiu -> Postu -> Suku -> Aldeia (AJAX).
   Form tenke iha atributu data-posts-url, data-villages-url no data-aldeias-url. */
$(function () {
	var $form = $('form[data-posts-url]');
	if (!$form.length) { return; }
	var $mun = $('#id_municipality'), $post = $('#id_post'), $vil = $('#id_village'), $ald = $('#id_aldeia');

	function muat($alvu, url, key, val) {
		if (!$alvu.length || $alvu.prop('disabled')) { return; }
		if (!val) { $alvu.html('<option value="">---------</option>'); return; }
		var data = {}; data[key] = val;
		$.ajax({ url: url, data: data, success: function (html) { $alvu.html(html); } });
	}
	function limpa($lista) {
		$.each($lista, function (_, $e) { if ($e.length && !$e.prop('disabled')) { $e.html('<option value="">---------</option>'); } });
	}

	$mun.on('change', function () {
		limpa([$vil, $ald]);
		muat($post, $form.data('posts-url'), 'municipality', $(this).val());
	});
	$post.on('change', function () {
		limpa([$ald]);
		muat($vil, $form.data('villages-url'), 'post', $(this).val());
	});
	$vil.on('change', function () {
		muat($ald, $form.data('aldeias-url'), 'village', $(this).val());
	});
});
