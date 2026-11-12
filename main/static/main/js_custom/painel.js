/* Grafik bara Mane x Feto ba painel Varanda (Chart.js v2): bara kluster ho númeru iha leten. */
(function () {
	var kanvas = document.getElementById('painel_grafik');
	var lab = document.getElementById('painel-label');
	var mn = document.getElementById('painel-mane');
	var ft = document.getElementById('painel-feto');
	if (!kanvas || !lab || !mn || !ft || typeof Chart === 'undefined') { return; }
	var label = JSON.parse(lab.textContent), mane = JSON.parse(mn.textContent), feto = JSON.parse(ft.textContent);
	document.getElementById('painel_isi').style.minWidth = Math.max(0, label.length * 46) + 'px';
	Chart.plugins.register({
		afterDatasetsDraw: function (c) {
			if (c.canvas.id !== 'painel_grafik') { return; }
			var ctx = c.ctx;
			ctx.save(); ctx.font = '10px Arial'; ctx.fillStyle = '#333'; ctx.textAlign = 'center';
			c.data.datasets.forEach(function (ds, d) {
				c.getDatasetMeta(d).data.forEach(function (bar, i) {
					if (ds.data[i] > 0) { ctx.fillText(ds.data[i], bar._model.x, bar._model.y - 4); }
				});
			});
			ctx.restore();
		}
	});
	new Chart(kanvas, {
		type: 'bar',
		data: {
			labels: label,
			datasets: [
				{ label: 'Mane', data: mane, backgroundColor: '#02b0ed', borderColor: '#0190c2', borderWidth: 1 },
				{ label: 'Feto', data: feto, backgroundColor: '#f9d71c', borderColor: '#e0bd00', borderWidth: 1 }
			]
		},
		options: {
			responsive: true, maintainAspectRatio: false, legend: { display: false },
			layout: { padding: { top: 16 } },
			scales: {
				yAxes: [{ ticks: { beginAtZero: true, precision: 0, fontSize: 9 }, gridLines: { color: '#eee' } }],
				xAxes: [{ ticks: { autoSkip: false, maxRotation: 45, minRotation: 0, fontSize: 9 }, gridLines: { display: false } }]
			},
			tooltips: { mode: 'index', intersect: false }
		}
	});
})();
