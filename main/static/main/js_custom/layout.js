/* Sidebar dashboard: shrink (desktop) ka show (mobile). Hanesan tema Bootstrapious. */
$(function () {
	var largura = function () { return $(window).outerWidth(); };
	if (largura() > 1194) { $('nav.side-navbar').removeClass('shrink'); }
	$('#toggle-btn').on('click', function (e) {
		e.preventDefault();
		$(this).toggleClass('active');
		if (largura() > 1194) {
			$('nav.side-navbar').toggleClass('shrink');
			$('.page').toggleClass('active');
		} else {
			$('nav.side-navbar').toggleClass('show-sm');
			$('.page').toggleClass('active-sm');
		}
	});
	$('.alert-dismissible-auto').delay(6000).fadeOut(600);
});
