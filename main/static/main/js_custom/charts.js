/* Grafik Chart.js (v2) ho data husi API report. Kór tuir tema SMDPD. */
var KOR = ['#04d419', '#02b0ed', '#ffc107', '#dc3545', '#6f42c1', '#17a2b8', '#fd7e14', '#868e96', '#20c997', '#e83e8c'];

/* tipu: 'bar' | 'doughnut' | 'pie' | 'horizontalBar' */
function grafik(canvasId, endpoint, tipu, naran) {
	$.ajax({
		method: 'GET',
		url: endpoint,
		success: function (data) {
			var pie = (tipu === 'pie' || tipu === 'doughnut');
			var warna = data.label.map(function (_, i) { return KOR[i % KOR.length]; });
			var opsaun = { responsive: true, maintainAspectRatio: false, legend: { display: pie, position: 'bottom' } };
			if (!pie) {
				var eixu = [{ ticks: { beginAtZero: true, precision: 0 } }];
				opsaun.scales = (tipu === 'horizontalBar') ? { xAxes: eixu } : { yAxes: eixu };
			}
			new Chart(document.getElementById(canvasId), {
				type: tipu,
				data: {
					labels: data.label,
					datasets: [{ label: naran || 'Membru', data: data.obj, backgroundColor: pie ? warna : '#04d419', borderWidth: 0 }]
				},
				options: opsaun
			});
		},
		error: function (e) { console.log(e); }
	});
}
