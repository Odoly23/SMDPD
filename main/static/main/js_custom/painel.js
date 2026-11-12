/* Grafik bara kuning ba painel Varanda (Chart.js v2): total membru ho número iha leten bara. */
(function () {
	var kanvas = document.getElementById('painel_grafik');
	var lab = document.getElementById('painel-label');
	var dad = document.getElementById('painel-data');
	if (!kanvas || !lab || !dad || typeof Chart === 'undefined') { return; }
	var label = JSON.parse(lab.textContent), data = JSON.parse(dad.textContent);
	var isi = document.getElementById('painel_isi');
	isi.style.minWidth = Math.max(0, label.length * 30) + 'px';
	Chart.plugins.register({
		id: 'nilaiBara',
		afterDatasetsDraw: function (c) {
			if (c.canvas.id !== 'painel_grafik') { return; }
			var ctx = c.ctx;
			ctx.save(); ctx.font = '10px Arial'; ctx.fillStyle = '#333'; ctx.textAlign = 'center';
			c.getDatasetMeta(0).data.forEach(function (bar, i) {
				ctx.fillText(data[i], bar._model.x, bar._model.y - 4);
			});
			ctx.restore();
		}
	});
	new Chart(kanvas, {
		type: 'bar',
		data: { labels: label, datasets: [{ label: 'Membru', data: data, backgroundColor: '#f9d71c', borderColor: '#e0bd00', borderWidth: 1 }] },
		options: {
			responsive: true, maintainAspectRatio: false, legend: { display: false },
			layout: { padding: { top: 16 } },
			scales: {
				yAxes: [{ ticks: { beginAtZero: true, precision: 0, fontSize: 9 }, gridLines: { color: '#eee' } }],
				xAxes: [{ ticks: { autoSkip: false, maxRotation: 60, minRotation: 60, fontSize: 9 }, gridLines: { display: false } }]
			},
			tooltips: { callbacks: { label: function (t) { return t.yLabel + ' membru'; } } }
		}
	});
})();
