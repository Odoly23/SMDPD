/* Tunggu fotu hotu loke molok dialogu imprime (fotu membru husi storage privadu). */
window.addEventListener('load', function () {
	var imgs = Array.prototype.slice.call(document.images);
	var tunggu = imgs.map(function (im) {
		return im.complete ? Promise.resolve() : new Promise(function (ok) { im.onload = im.onerror = ok; });
	});
	Promise.all(tunggu).then(function () { setTimeout(function () { window.print(); }, 300); });
});
